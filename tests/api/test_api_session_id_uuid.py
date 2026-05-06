"""B5: UUID-typed session_id path parameter on /resume.

The plan requires session_id on
``/api/v1/investigate/{session_id}/resume`` to be typed as ``UUID`` so
FastAPI rejects malformed values at the framework boundary with 422
before the handler runs. Otherwise an attacker can probe the endpoint
with arbitrary strings (path-traversal-y values, control chars,
absurdly long input), each of which would otherwise produce a 500 from
the orchestrator's failure to look up a thread.

No mocks. Drives the real FastAPI app via TestClient.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_settings_singleton():
    from find_evil_agent.config import settings as settings_module
    settings_module._settings = None
    yield
    settings_module._settings = None


def _build_client() -> TestClient:
    import importlib
    from find_evil_agent.api import server as server_module
    importlib.reload(server_module)
    return TestClient(server_module.app)


# ---------------------------------------------------------------------------
# Specification
# ---------------------------------------------------------------------------

class TestResumeSessionIdValidation:
    """Path parameter must be UUID-typed so framework rejects junk inputs."""

    def test_non_uuid_session_id_returns_422(self):
        client = _build_client()
        resp = client.post(
            "/api/v1/investigate/not-a-uuid/resume",
            json={"approved": True},
        )
        assert resp.status_code == 422, (
            "Non-UUID session_id should be rejected at the framework boundary, "
            f"got {resp.status_code} with body {resp.text[:200]!r}"
        )

    def test_path_traversal_session_id_rejected(self):
        client = _build_client()
        # URL-encoded ``../``-style probe — must not be accepted as a session id.
        resp = client.post(
            "/api/v1/investigate/..%2Fetc%2Fpasswd/resume",
            json={"approved": True},
        )
        # Either a 422 (UUID validation) or a 404 (FastAPI router can't match
        # the path). Both are acceptable rejections — what we forbid is the
        # request reaching the resume handler with a string value.
        assert resp.status_code in (404, 422)

    def test_control_char_in_session_id_rejected(self):
        client = _build_client()
        # %0a = newline; %00 = NUL. Either UUID validation or path routing
        # must reject these.
        resp = client.post(
            "/api/v1/investigate/abc%0aevil/resume",
            json={"approved": True},
        )
        assert resp.status_code in (404, 422)

    def test_overlong_session_id_rejected(self):
        client = _build_client()
        long_id = "a" * 4096
        resp = client.post(
            f"/api/v1/investigate/{long_id}/resume",
            json={"approved": True},
        )
        assert resp.status_code in (404, 422)

    def test_empty_session_id_segment_rejected(self):
        client = _build_client()
        # Trailing-slash collapse — FastAPI will not match this route at
        # all, which is the correct behavior (404).
        resp = client.post(
            "/api/v1/investigate//resume",
            json={"approved": True},
        )
        assert resp.status_code in (404, 422, 405)

    def test_valid_uuid_passes_path_validation(self):
        """A well-formed UUID must NOT be rejected by the path validator —
        any failure must come from downstream (orchestrator), not 422."""
        client = _build_client()
        valid_id = uuid4()
        resp = client.post(
            f"/api/v1/investigate/{valid_id}/resume",
            json={"approved": True},
        )
        # The orchestrator will fail to load a non-existent thread, so we
        # expect 500 (internal error) — but NOT 422, which would mean the
        # path validator wrongly rejected a syntactically valid UUID.
        assert resp.status_code != 422

    def test_uppercase_uuid_accepted(self):
        client = _build_client()
        valid_id = str(uuid4()).upper()
        resp = client.post(
            f"/api/v1/investigate/{valid_id}/resume",
            json={"approved": True},
        )
        assert resp.status_code != 422

    def test_validation_does_not_leak_traceback(self):
        """422 responses must come from the framework, not a 500 with a
        pydantic traceback."""
        client = _build_client()
        resp = client.post(
            "/api/v1/investigate/garbage-id/resume",
            json={"approved": True},
        )
        # Framework rejection path — 422 with structured error, not a 500.
        assert resp.status_code == 422
        body = resp.text
        assert "traceback" not in body.lower()
        assert "/users/" not in body.lower()
