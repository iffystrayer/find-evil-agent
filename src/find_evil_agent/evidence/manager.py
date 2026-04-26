"""Evidence manager for forensic chain-of-custody tracking."""

import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

import asyncssh
import structlog

from find_evil_agent.config.settings import get_settings
from find_evil_agent.evidence.schemas import Evidence, EvidenceType

logger = structlog.get_logger(__name__)


class EvidenceManager:
    """Manage forensic evidence with chain-of-custody tracking."""

    def __init__(self, storage_path: Path | None = None):
        """Initialize evidence manager.

        Args:
            storage_path: Path to store evidence metadata (default: .evidence/)
        """
        self.storage_path = storage_path or Path(".evidence")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.settings = get_settings()

    async def register_evidence(
        self,
        file_path: str,
        name: str,
        description: str | None = None,
        source: str | None = None,
        acquisition_date: datetime | None = None,
        registered_by: str = "find-evil-agent",
    ) -> Evidence:
        """Register new evidence with hash computation and validation.

        Args:
            file_path: Path to evidence file on SIFT VM
            name: Human-readable evidence name
            description: Optional evidence description
            source: Source system or location
            acquisition_date: When evidence was acquired
            registered_by: Who is registering the evidence

        Returns:
            Evidence object with computed hash and validation status

        Raises:
            FileNotFoundError: If evidence file doesn't exist on SIFT VM
            RuntimeError: If hash computation fails
        """
        logger.info("registering_evidence", file_path=file_path, name=name)

        # Validate file exists on SIFT VM
        file_size = await self._validate_file_exists(file_path)

        # Compute SHA256 hash
        sha256_hash = await self._compute_hash(file_path)

        # Detect evidence type
        evidence_type = self._detect_evidence_type(file_path)

        # Create evidence object
        evidence = Evidence(
            name=name,
            description=description,
            file_path=file_path,
            file_size=file_size,
            sha256_hash=sha256_hash,
            evidence_type=evidence_type,
            source=source,
            acquisition_date=acquisition_date,
            registered_by=registered_by,
            validated=True,
            validation_timestamp=datetime.utcnow(),
        )

        # Add initial chain-of-custody entry
        evidence.add_custody_entry(
            action="registered",
            actor=registered_by,
            details=f"Evidence registered: {name} ({evidence_type.value})",
            location=file_path,
        )

        # Save evidence metadata
        self._save_evidence(evidence)

        logger.info(
            "evidence_registered",
            evidence_id=str(evidence.evidence_id),
            hash=sha256_hash[:16],
            type=evidence_type.value,
        )

        return evidence

    async def validate_evidence(self, evidence: Evidence) -> bool:
        """Validate evidence file still exists and hash matches.

        Args:
            evidence: Evidence object to validate

        Returns:
            True if evidence is valid, False otherwise
        """
        logger.info("validating_evidence", evidence_id=str(evidence.evidence_id))

        try:
            # Check file exists
            file_size = await self._validate_file_exists(evidence.file_path)

            # Recompute hash
            computed_hash = await self._compute_hash(evidence.file_path)

            # Verify hash matches
            is_valid = evidence.verify_hash(computed_hash)

            if is_valid:
                evidence.validated = True
                evidence.validation_timestamp = datetime.utcnow()
                evidence.add_custody_entry(
                    action="validated",
                    actor="find-evil-agent",
                    details="Evidence integrity verified (hash match)",
                    location=evidence.file_path,
                )
                self._save_evidence(evidence)
                logger.info("evidence_validated", evidence_id=str(evidence.evidence_id))
            else:
                logger.error(
                    "evidence_hash_mismatch",
                    evidence_id=str(evidence.evidence_id),
                    expected=evidence.sha256_hash[:16],
                    computed=computed_hash[:16],
                )

            return is_valid

        except Exception as e:
            logger.error(
                "evidence_validation_failed",
                evidence_id=str(evidence.evidence_id),
                error=str(e),
            )
            return False

    async def _validate_file_exists(self, file_path: str) -> int:
        """Validate file exists on SIFT VM and return size.

        Args:
            file_path: Path to file on SIFT VM

        Returns:
            File size in bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            async with asyncssh.connect(
                host=self.settings.sift_vm_host,
                port=self.settings.sift_vm_port,
                username=self.settings.sift_ssh_user,
                known_hosts=None,
            ) as conn:
                # Check file exists and get size
                result = await conn.run(f"stat -c %s {file_path}", check=True)
                file_size = int(result.stdout.strip())
                logger.debug("file_validated", file_path=file_path, size=file_size)
                return file_size

        except Exception as e:
            logger.error("file_validation_failed", file_path=file_path, error=str(e))
            raise FileNotFoundError(f"Evidence file not found: {file_path}") from e

    async def _compute_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file on SIFT VM.

        Args:
            file_path: Path to file on SIFT VM

        Returns:
            SHA256 hash (hex string)

        Raises:
            RuntimeError: If hash computation fails
        """
        try:
            async with asyncssh.connect(
                host=self.settings.sift_vm_host,
                port=self.settings.sift_vm_port,
                username=self.settings.sift_ssh_user,
                known_hosts=None,
            ) as conn:
                # Compute SHA256 hash
                result = await conn.run(f"sha256sum {file_path}", check=True)
                sha256_hash = result.stdout.split()[0]
                logger.debug("hash_computed", file_path=file_path, hash=sha256_hash[:16])
                return sha256_hash

        except Exception as e:
            logger.error("hash_computation_failed", file_path=file_path, error=str(e))
            raise RuntimeError(f"Failed to compute hash: {file_path}") from e

    def _detect_evidence_type(self, file_path: str) -> EvidenceType:
        """Detect evidence type from file path/extension.

        Args:
            file_path: Path to evidence file

        Returns:
            Detected evidence type
        """
        file_path_lower = file_path.lower()

        # Disk images
        if any(
            ext in file_path_lower
            for ext in [".dd", ".img", ".raw", ".e01", ".aff", ".vmdk", ".vhd"]
        ):
            return EvidenceType.DISK_IMAGE

        # Memory dumps
        if any(ext in file_path_lower for ext in [".mem", ".dmp", ".raw", ".vmem", ".lime"]):
            return EvidenceType.MEMORY_DUMP

        # Network captures
        if any(ext in file_path_lower for ext in [".pcap", ".pcapng", ".cap"]):
            return EvidenceType.NETWORK_CAPTURE

        # Log files
        if any(ext in file_path_lower for ext in [".log", ".txt", ".evtx", ".csv", ".json"]):
            return EvidenceType.LOG_FILE

        # Filesystem exports
        if any(pattern in file_path_lower for pattern in ["/mnt/", "/media/", "filesystem"]):
            return EvidenceType.FILESYSTEM

        return EvidenceType.UNKNOWN

    def _save_evidence(self, evidence: Evidence) -> None:
        """Save evidence metadata to disk.

        Args:
            evidence: Evidence object to save
        """
        evidence_file = self.storage_path / f"{evidence.evidence_id}.json"
        with open(evidence_file, "w") as f:
            json.dump(evidence.model_dump(mode="json"), f, indent=2, default=str)

        logger.debug("evidence_saved", evidence_id=str(evidence.evidence_id))

    def load_evidence(self, evidence_id: UUID) -> Evidence | None:
        """Load evidence metadata from disk.

        Args:
            evidence_id: UUID of evidence to load

        Returns:
            Evidence object if found, None otherwise
        """
        evidence_file = self.storage_path / f"{evidence_id}.json"

        if not evidence_file.exists():
            logger.warning("evidence_not_found", evidence_id=str(evidence_id))
            return None

        with open(evidence_file) as f:
            data = json.load(f)
            evidence = Evidence(**data)

        logger.debug("evidence_loaded", evidence_id=str(evidence_id))
        return evidence

    def list_evidence(self) -> list[Evidence]:
        """List all registered evidence.

        Returns:
            List of all evidence objects
        """
        evidence_list = []

        for evidence_file in self.storage_path.glob("*.json"):
            with open(evidence_file) as f:
                data = json.load(f)
                evidence = Evidence(**data)
                evidence_list.append(evidence)

        logger.debug("evidence_listed", count=len(evidence_list))
        return sorted(evidence_list, key=lambda e: e.registered_at, reverse=True)

    def add_custody_entry(
        self,
        evidence_id: UUID,
        action: str,
        actor: str,
        details: str,
        location: str | None = None,
    ) -> Evidence | None:
        """Add chain-of-custody entry to evidence.

        Args:
            evidence_id: UUID of evidence
            action: Action taken
            actor: Person or system performing action
            details: Details about the action
            location: Optional location

        Returns:
            Updated evidence object if found, None otherwise
        """
        evidence = self.load_evidence(evidence_id)

        if evidence is None:
            return None

        evidence.add_custody_entry(action=action, actor=actor, details=details, location=location)

        self._save_evidence(evidence)

        logger.info(
            "custody_entry_added",
            evidence_id=str(evidence_id),
            action=action,
            actor=actor,
        )

        return evidence
