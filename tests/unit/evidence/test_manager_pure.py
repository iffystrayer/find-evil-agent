"""C6.3: pure-function tests for ``EvidenceManager`` helpers.

The async-io test file already pins the round-trip behavior of
``_save_evidence`` / ``load_evidence`` / ``list_evidence`` /
``add_custody_entry``. Two pure helpers had zero coverage:

* ``_detect_evidence_type`` — extension-based dispatch with a sizeable
  branch matrix.
* ``list_evidence`` — documented to return entries sorted by
  ``registered_at`` descending; the existing test only checks set
  equality, not order.

No mocks. Real EvidenceManager + Evidence objects.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from find_evil_agent.evidence.manager import EvidenceManager
from find_evil_agent.evidence.schemas import Evidence, EvidenceType


# ---------------------------------------------------------------------------
# _detect_evidence_type — parametrized branch matrix
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path,expected",
    [
        # Disk images
        ("/evidence/case1.dd", EvidenceType.DISK_IMAGE),
        ("/evidence/Case2.IMG", EvidenceType.DISK_IMAGE),
        ("/evidence/case3.E01", EvidenceType.DISK_IMAGE),
        ("/evidence/snapshot.vmdk", EvidenceType.DISK_IMAGE),
        ("/evidence/disk.vhd", EvidenceType.DISK_IMAGE),
        # Memory dumps
        ("/dumps/host1.mem", EvidenceType.MEMORY_DUMP),
        ("/dumps/host1.dmp", EvidenceType.MEMORY_DUMP),
        ("/dumps/host1.lime", EvidenceType.MEMORY_DUMP),
        ("/dumps/host1.vmem", EvidenceType.MEMORY_DUMP),
        # Network captures
        ("/pcap/traffic.pcap", EvidenceType.NETWORK_CAPTURE),
        ("/pcap/traffic.pcapng", EvidenceType.NETWORK_CAPTURE),
        ("/pcap/legacy.cap", EvidenceType.NETWORK_CAPTURE),
        # Logs
        ("/logs/app.log", EvidenceType.LOG_FILE),
        ("/logs/event.evtx", EvidenceType.LOG_FILE),
        ("/logs/output.csv", EvidenceType.LOG_FILE),
        # Filesystem markers
        ("/mnt/case-1/exported", EvidenceType.FILESYSTEM),
        ("/media/usb/filesystem", EvidenceType.FILESYSTEM),
        # Unknown falls through
        ("/foo/bar.exe", EvidenceType.UNKNOWN),
        ("/foo/bar.zip", EvidenceType.UNKNOWN),
    ],
)
def test_detect_evidence_type(tmp_path: Path, path: str, expected: EvidenceType):
    """Branch matrix for ``_detect_evidence_type`` extension dispatch."""
    manager = EvidenceManager(storage_path=tmp_path)
    assert manager._detect_evidence_type(path) is expected


def test_detect_evidence_type_is_case_insensitive(tmp_path: Path):
    manager = EvidenceManager(storage_path=tmp_path)
    assert manager._detect_evidence_type("/evidence/CASE.DD") is EvidenceType.DISK_IMAGE
    assert manager._detect_evidence_type("/evidence/CASE.dd") is EvidenceType.DISK_IMAGE


# ---------------------------------------------------------------------------
# list_evidence — newest-first ordering
# ---------------------------------------------------------------------------


def _evidence_with_registration(name: str, registered_at: datetime) -> Evidence:
    return Evidence(
        evidence_id=uuid4(),
        name=name,
        file_path=f"/tmp/{name}.bin",
        file_size=1,
        sha256_hash="b" * 64,
        evidence_type=EvidenceType.LOG_FILE,
        registered_by="ordering-test",
        registered_at=registered_at,
        validated=True,
    )


@pytest.mark.asyncio
async def test_list_evidence_returns_newest_first(tmp_path: Path):
    """``list_evidence`` must sort by ``registered_at`` descending so the
    UI / CLI surfaces the most recent evidence first."""
    manager = EvidenceManager(storage_path=tmp_path)

    base = datetime(2026, 5, 6, 12, 0, tzinfo=timezone.utc)
    items = [
        _evidence_with_registration("oldest", base),
        _evidence_with_registration("middle", base + timedelta(hours=1)),
        _evidence_with_registration("newest", base + timedelta(hours=2)),
    ]
    # Save in shuffled order to make sure the sort is real, not insertion-driven
    for ev in (items[1], items[0], items[2]):
        await manager._save_evidence(ev)

    listed = await manager.list_evidence()
    names = [ev.name for ev in listed]
    assert names == ["newest", "middle", "oldest"]
