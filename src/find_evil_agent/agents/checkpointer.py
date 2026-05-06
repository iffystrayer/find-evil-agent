"""Bounded LangGraph checkpointer (C1).

The orchestrator workflows compile against a global checkpointer so HITL
sessions can be resumed across requests. The original implementation used
an unbounded ``MemorySaver`` at module scope which leaks memory in a
long-running process and loses every in-flight session on restart.

``BoundedMemorySaver`` keeps the convenient in-memory semantics for now
but adds two safeguards:

* Per-thread TTL — a thread is evicted once it has been idle longer than
  ``settings.session_ttl_minutes``.
* Hard cap — once ``settings.max_active_sessions`` is reached, the
  least-recently-written thread is evicted (LRU).

Eviction is lazy: each ``put`` / ``aput`` triggers a sweep so the wrapper
incurs no background tasks. ``delete_thread`` (provided by upstream
``InMemorySaver``) clears the thread's checkpoint store and pending
writes atomically.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Optional

from langgraph.checkpoint.base import (
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
)
from langgraph.checkpoint.memory import MemorySaver

from find_evil_agent.config.settings import get_settings


class BoundedMemorySaver(MemorySaver):
    """``MemorySaver`` with TTL + LRU eviction of idle threads."""

    def __init__(
        self,
        ttl_minutes: int,
        max_threads: int,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        if ttl_minutes <= 0:
            raise ValueError("ttl_minutes must be positive")
        if max_threads <= 0:
            raise ValueError("max_threads must be positive")
        self.ttl_minutes = ttl_minutes
        self.max_threads = max_threads
        self._last_write: OrderedDict[str, float] = OrderedDict()
        self._lock = threading.Lock()

    # -- helpers ---------------------------------------------------------

    def _ttl_seconds(self) -> float:
        return self.ttl_minutes * 60.0

    def _touch(self, thread_id: str) -> None:
        """Record (or refresh) the last-write time for ``thread_id``."""
        now = time.monotonic()
        with self._lock:
            self._last_write.pop(thread_id, None)
            self._last_write[thread_id] = now

    def _evict_expired(self) -> None:
        """Drop threads that have outlived ``ttl_minutes``."""
        cutoff = time.monotonic() - self._ttl_seconds()
        with self._lock:
            expired = [tid for tid, ts in self._last_write.items() if ts < cutoff]
            for tid in expired:
                self._last_write.pop(tid, None)
        for tid in expired:
            try:
                self.delete_thread(tid)
            except Exception:
                # delete_thread is best-effort; storage may already be empty
                pass

    def _enforce_cap(self) -> None:
        """Evict least-recently-written threads until under ``max_threads``."""
        evicted: list[str] = []
        with self._lock:
            while len(self._last_write) > self.max_threads:
                tid, _ = self._last_write.popitem(last=False)
                evicted.append(tid)
        for tid in evicted:
            try:
                self.delete_thread(tid)
            except Exception:
                pass

    def _mark_thread_age(self, thread_id: str, *, seconds_ago: float) -> None:
        """Test hook — backdate a thread's last-write time."""
        with self._lock:
            if thread_id in self._last_write:
                self._last_write[thread_id] = time.monotonic() - seconds_ago

    def thread_count(self) -> int:
        with self._lock:
            return len(self._last_write)

    # -- LangGraph contract ---------------------------------------------

    def put(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> dict:
        result = super().put(config, checkpoint, metadata, new_versions)
        thread_id = config.get("configurable", {}).get("thread_id")
        if thread_id is not None:
            self._touch(str(thread_id))
            self._evict_expired()
            self._enforce_cap()
        return result

    async def aput(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> dict:
        result = await super().aput(config, checkpoint, metadata, new_versions)
        thread_id = config.get("configurable", {}).get("thread_id")
        if thread_id is not None:
            self._touch(str(thread_id))
            self._evict_expired()
            self._enforce_cap()
        return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_singleton: Optional[BoundedMemorySaver] = None
_singleton_lock = threading.Lock()


def get_checkpointer() -> BoundedMemorySaver:
    """Return the process-wide bounded checkpointer."""
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:
                settings = get_settings()
                _singleton = BoundedMemorySaver(
                    ttl_minutes=settings.session_ttl_minutes,
                    max_threads=settings.max_active_sessions,
                )
    return _singleton


def _reset_singleton() -> None:
    """Drop the cached singleton — used by tests that mutate settings."""
    global _singleton
    with _singleton_lock:
        _singleton = None
