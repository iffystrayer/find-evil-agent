"""B3: async file I/O tests for EvidenceManager.

The plan converts the three blocking ``open()`` sites in
``evidence/manager.py`` (``_save_evidence``, ``load_evidence``,
``list_evidence``) to ``aiofiles``. Because the affected helpers are
called from already-async code paths (``register_evidence`` and
``validate_evidence``), they become async themselves; this file pins the
async contract and verifies round-trip behavior survives the migration.

No mocks per project policy — uses real tmp_path filesystem and real
EvidenceManager + Evidence objects. ``register_evidence`` requires a real
file path on a SIFT VM and is therefore not exercised here; we drive the
storage helpers directly with hand-built Evidence instances.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from find_evil_agent.evidence.manager import EvidenceManager
from find_evil_agent.evidence.schemas import Evidence, EvidenceType


def _evidence(name: str = "memdump-1") -> Evidence:
    return Evidence(
        evidence_id=uuid4(),
        name=name,
        description="async io test",
        file_path=f"/tmp/{name}.bin",
        file_size=1024,
        sha256_hash="a" * 64,
        evidence_type=EvidenceType.MEMORY_DUMP,
        source="test",
        acquisition_date=datetime(2026, 5, 6, tzinfo=timezone.utc),
        registered_by="b3-test",
        validated=True,
        validation_timestamp=datetime(2026, 5, 6, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_save_then_load_round_trip(tmp_path: Path) -> None:
    """_save_evidence + load_evidence must round-trip a full Evidence object."""
    manager = EvidenceManager(storage_path=tmp_path)
    original = _evidence("rt-1")

    # _save_evidence is async after B3
    await manager._save_evidence(original)

    loaded = await manager.load_evidence(original.evidence_id)
    assert loaded is not None
    assert loaded.evidence_id == original.evidence_id
    assert loaded.name == original.name
    assert loaded.sha256_hash == original.sha256_hash
    assert loaded.file_size == original.file_size


@pytest.mark.asyncio
async def test_load_returns_none_for_missing(tmp_path: Path) -> None:
    manager = EvidenceManager(storage_path=tmp_path)
    missing_id = uuid4()
    assert await manager.load_evidence(missing_id) is None


@pytest.mark.asyncio
async def test_list_evidence_returns_all_saved(tmp_path: Path) -> None:
    manager = EvidenceManager(storage_path=tmp_path)
    e1, e2, e3 = _evidence("a"), _evidence("b"), _evidence("c")
    for ev in (e1, e2, e3):
        await manager._save_evidence(ev)

    listed = await manager.list_evidence()
    assert {ev.name for ev in listed} == {"a", "b", "c"}


@pytest.mark.asyncio
async def test_concurrent_saves_do_not_block(tmp_path: Path) -> None:
    """asyncio.gather of multiple saves must complete with all files persisted."""
    manager = EvidenceManager(storage_path=tmp_path)
    items = [_evidence(f"concurrent-{i}") for i in range(8)]

    await asyncio.gather(*(manager._save_evidence(ev) for ev in items))

    # All files should now exist; load each back concurrently
    loaded = await asyncio.gather(
        *(manager.load_evidence(ev.evidence_id) for ev in items)
    )
    assert all(ev is not None for ev in loaded)
    assert {ev.name for ev in loaded} == {f"concurrent-{i}" for i in range(8)}


@pytest.mark.asyncio
async def test_add_custody_entry_round_trip(tmp_path: Path) -> None:
    """add_custody_entry must persist updates back to disk via async save."""
    manager = EvidenceManager(storage_path=tmp_path)
    ev = _evidence("custody-1")
    await manager._save_evidence(ev)

    updated = await manager.add_custody_entry(
        evidence_id=ev.evidence_id,
        action="reviewed",
        actor="analyst-1",
        details="checked metadata",
    )
    assert updated is not None
    assert any(entry.action == "reviewed" for entry in updated.chain_of_custody)

    # Re-load fresh and confirm persistence
    reloaded = await manager.load_evidence(ev.evidence_id)
    assert reloaded is not None
    assert any(entry.action == "reviewed" for entry in reloaded.chain_of_custody)


def test_evidence_manager_source_uses_aiofiles() -> None:
    """Static guard: evidence/manager.py must use aiofiles after B3."""
    src = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "find_evil_agent"
        / "evidence"
        / "manager.py"
    )
    text = src.read_text()
    assert "aiofiles" in text, "evidence/manager.py must import aiofiles after B3"
    assert text.count("aiofiles.open") >= 3, (
        "expected at least 3 aiofiles.open sites in evidence/manager.py "
        f"(_save_evidence, load_evidence, list_evidence). Found: {text.count('aiofiles.open')}"
    )
