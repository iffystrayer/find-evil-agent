"""Evidence schemas and data models."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Type of forensic evidence."""

    DISK_IMAGE = "disk_image"
    MEMORY_DUMP = "memory_dump"
    NETWORK_CAPTURE = "network_capture"
    LOG_FILE = "log_file"
    FILESYSTEM = "filesystem"
    UNKNOWN = "unknown"


class ChainOfCustodyEntry(BaseModel):
    """Single entry in chain-of-custody log."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str = Field(..., description="Action taken (registered, analyzed, transferred)")
    actor: str = Field(..., description="Person or system performing action")
    details: str = Field(..., description="Additional details about the action")
    location: Optional[str] = Field(None, description="Evidence location at time of action")


class Evidence(BaseModel):
    """Forensic evidence metadata and chain-of-custody."""

    # Identification
    evidence_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Human-readable evidence name")
    description: Optional[str] = Field(None, description="Evidence description")

    # File information
    file_path: str = Field(..., description="Path to evidence file on SIFT VM")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    sha256_hash: str = Field(..., description="SHA256 hash for integrity verification")

    # Evidence metadata
    evidence_type: EvidenceType = Field(
        default=EvidenceType.UNKNOWN, description="Type of evidence"
    )
    source: Optional[str] = Field(None, description="Source system or location")
    acquisition_date: Optional[datetime] = Field(None, description="When evidence was acquired")

    # Registration
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    registered_by: str = Field(default="find-evil-agent", description="Who registered")

    # Chain of custody
    chain_of_custody: list[ChainOfCustodyEntry] = Field(
        default_factory=list, description="Chronological chain-of-custody log"
    )

    # Validation
    validated: bool = Field(default=False, description="Whether file exists on SIFT VM")
    validation_timestamp: Optional[datetime] = Field(None, description="When validated")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat(), UUID: lambda v: str(v)}

    def add_custody_entry(
        self, action: str, actor: str, details: str, location: Optional[str] = None
    ) -> None:
        """Add entry to chain-of-custody log."""
        entry = ChainOfCustodyEntry(
            action=action, actor=actor, details=details, location=location
        )
        self.chain_of_custody.append(entry)

    def verify_hash(self, computed_hash: str) -> bool:
        """Verify evidence integrity by comparing hashes."""
        return self.sha256_hash.lower() == computed_hash.lower()
