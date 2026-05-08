"""C1: bounded, persistent-friendly checkpointer.

Replaces the unbounded module-level ``MemorySaver`` in
``agents/orchestrator.py:26`` with a wrapper that:

1. Tracks per-thread last-write timestamps.
2. Evicts threads whose age exceeds ``settings.session_ttl_minutes``.
3. Enforces a hard cap of ``settings.max_active_sessions`` (LRU).

Tests follow the project TDD pattern: real LangGraph checkpoint API,
no mocks. Uses synchronous ``put`` because ``InMemorySaver``'s sync /
async methods share storage and the sync path is simpler to drive
without an event loop.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import pytest

from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata

from find_evil_agent.config import settings as settings_module


# ---------------------------------------------------------------------------
# Conditional import — wrapper may not exist yet during the red phase
# ---------------------------------------------------------------------------

try:
    from find_evil_agent.agents.checkpointer import (
        BoundedMemorySaver,
        get_checkpointer,
    )

    CHECKPOINTER_AVAILABLE = True
except ImportError:
    CHECKPOINTER_AVAILABLE = False

    class BoundedMemorySaver:  # type: ignore[no-redef]
        pass

    def get_checkpointer():  # type: ignore[no-redef]
        raise NotImplementedError


pytestmark = pytest.mark.skipif(
    not CHECKPOINTER_AVAILABLE,
    reason="BoundedMemorySaver not implemented yet (C1)",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_settings_singleton():
    settings_module._settings = None
    yield
    settings_module._settings = None


def _make_checkpoint(idx: int) -> Checkpoint:
    """Build a minimal valid Checkpoint payload."""
    return Checkpoint(
        v=4,
        id=f"chk-{idx}",
        ts=datetime.now(timezone.utc).isoformat(),
        channel_values={"state": {"step": idx}},
        channel_versions={},
        versions_seen={},
    )


def _make_metadata() -> CheckpointMetadata:
    # CheckpointMetadata is a TypedDict — empty dict is valid.
    return CheckpointMetadata()


def _put_thread(saver: BoundedMemorySaver, thread_id: str, idx: int = 0) -> dict:
    """Write one checkpoint for ``thread_id``; return the resulting config."""
    config = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": "",
        }
    }
    return saver.put(config, _make_checkpoint(idx), _make_metadata(), {})


# ---------------------------------------------------------------------------
# Specification (always-on documentation tests)
# ---------------------------------------------------------------------------


class TestSpecification:
    def test_module_exposes_bounded_saver_class(self):
        from find_evil_agent.agents import checkpointer

        assert hasattr(checkpointer, "BoundedMemorySaver")
        assert hasattr(checkpointer, "get_checkpointer")

    def test_get_checkpointer_returns_bounded_saver(self):
        cp = get_checkpointer()
        assert isinstance(cp, BoundedMemorySaver)

    def test_get_checkpointer_is_singleton(self):
        assert get_checkpointer() is get_checkpointer()


# ---------------------------------------------------------------------------
# Structure — wrapper conforms to the LangGraph checkpointer contract
# ---------------------------------------------------------------------------


class TestStructure:
    def test_inherits_langgraph_checkpoint_saver(self):
        from langgraph.checkpoint.base import BaseCheckpointSaver

        assert issubclass(BoundedMemorySaver, BaseCheckpointSaver)

    def test_supports_put_and_get_tuple(self):
        saver = BoundedMemorySaver(ttl_minutes=60, max_threads=10)
        config = _put_thread(saver, "thread-A")
        retrieved = saver.get_tuple(config)
        assert retrieved is not None
        assert retrieved.checkpoint["id"] == "chk-0"


# ---------------------------------------------------------------------------
# Execution — TTL eviction
# ---------------------------------------------------------------------------


class TestTTLEviction:
    def test_thread_evicted_after_ttl_expires(self):
        # 1 minute TTL, manually advance the clock
        saver = BoundedMemorySaver(ttl_minutes=1, max_threads=100)
        config = _put_thread(saver, "thread-A")

        # Confirm it's there
        assert saver.get_tuple(config) is not None

        # Force the recorded write time to be > 1 minute in the past
        saver._mark_thread_age("thread-A", seconds_ago=120)

        # Trigger an eviction sweep by writing a different thread
        _put_thread(saver, "thread-B")

        # thread-A should now be gone
        assert saver.get_tuple(config) is None

    def test_recent_thread_is_not_evicted(self):
        saver = BoundedMemorySaver(ttl_minutes=60, max_threads=100)
        config_a = _put_thread(saver, "thread-A")
        config_b = _put_thread(saver, "thread-B")

        # Both fresh — neither should be evicted
        assert saver.get_tuple(config_a) is not None
        assert saver.get_tuple(config_b) is not None
        assert saver.thread_count() == 2


# ---------------------------------------------------------------------------
# Execution — LRU hard-cap eviction
# ---------------------------------------------------------------------------


class TestLRUEviction:
    def test_oldest_thread_evicted_when_cap_exceeded(self):
        saver = BoundedMemorySaver(ttl_minutes=60, max_threads=3)

        cfg1 = _put_thread(saver, "thread-1")
        cfg2 = _put_thread(saver, "thread-2")
        cfg3 = _put_thread(saver, "thread-3")
        assert saver.thread_count() == 3

        # Adding a 4th should evict thread-1 (least recently written)
        cfg4 = _put_thread(saver, "thread-4")

        assert saver.thread_count() == 3
        assert saver.get_tuple(cfg1) is None
        assert saver.get_tuple(cfg2) is not None
        assert saver.get_tuple(cfg3) is not None
        assert saver.get_tuple(cfg4) is not None

    def test_writing_to_existing_thread_refreshes_its_position(self):
        saver = BoundedMemorySaver(ttl_minutes=60, max_threads=3)

        cfg1 = _put_thread(saver, "thread-1", idx=0)
        cfg2 = _put_thread(saver, "thread-2", idx=0)
        cfg3 = _put_thread(saver, "thread-3", idx=0)

        # Refresh thread-1 — it now becomes the most recent
        _put_thread(saver, "thread-1", idx=1)

        # Adding thread-4 should evict thread-2 (now the oldest)
        cfg4 = _put_thread(saver, "thread-4")

        assert saver.get_tuple(cfg1) is not None
        assert saver.get_tuple(cfg2) is None
        assert saver.get_tuple(cfg3) is not None
        assert saver.get_tuple(cfg4) is not None


# ---------------------------------------------------------------------------
# Integration — settings flow through to the singleton
# ---------------------------------------------------------------------------


class TestSettingsIntegration:
    def test_settings_expose_session_ttl_default(self):
        s = settings_module.get_settings()
        assert s.session_ttl_minutes == 60
        assert s.max_active_sessions == 100

    def test_get_checkpointer_reads_from_settings(self, monkeypatch):
        monkeypatch.setenv("SESSION_TTL_MINUTES", "30")
        monkeypatch.setenv("MAX_ACTIVE_SESSIONS", "50")
        settings_module._settings = None

        # Force a fresh singleton via the public reset path
        from find_evil_agent.agents import checkpointer as cp_module

        cp_module._reset_singleton()
        cp = get_checkpointer()
        assert cp.ttl_minutes == 30
        assert cp.max_threads == 50


# ---------------------------------------------------------------------------
# Static guard — orchestrator no longer instantiates a bare MemorySaver
# ---------------------------------------------------------------------------


class TestStaticGuards:
    def test_orchestrator_does_not_use_unbounded_memory_saver(self):
        from pathlib import Path

        from find_evil_agent.agents import orchestrator as orch

        # After C3c split, orchestrator is a package. Check all .py files in the package.
        orch_file = Path(orch.__file__)
        if orch_file.name == "__init__.py":
            # Package - check all Python modules
            orch_dir = orch_file.parent
            src_files = list(orch_dir.glob("*.py"))
            assert src_files, "orchestrator package should have .py modules after C3c split"
            combined_src = "\n".join(f.read_text() for f in src_files if f.name != "__init__.py")
        else:
            # Monolithic file
            combined_src = orch_file.read_text()

        # The literal global was the unbounded one — must be gone
        assert "_global_memory_saver = MemorySaver()" not in combined_src
        # Replacement must source from the bounded checkpointer module
        assert "checkpointer" in combined_src
