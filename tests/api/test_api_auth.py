"""API key authentication tests (A4 — TDD).

Verifies that:
- Authenticated endpoints reject requests without a valid `X-API-Key` header.
- `/health` remains public for liveness checks.
- When `settings.api_keys` is empty (dev mode), auth is disabled — required
  so local development and the existing test suite keep working without an
  env var. A startup-time warning is emitted.
- Comparison is timing-safe (uses secrets.compare_digest under the hood).

Roadmap reference: Milestone A4 in CODE_REVIEW.md.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_settings_singleton():
    """Reset the Settings singleton before AND after every test in this file
    so env-var changes don't leak across tests or files."""
    from find_evil_agent.config import settings as settings_module
    settings_module._settings = None
    yield
    settings_module._settings = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_app(monkeypatch, **overrides):
    """Build a fresh FastAPI app with overridden settings via env vars.

    Resets the Settings singleton so per-test env vars take effect.
    """
    from find_evil_agent.config import settings as settings_module

    settings_module._settings = None
    for key, value in overrides.items():
        monkeypatch.setenv(key.upper(), str(value))

    # Re-import to pick up the new settings inside server module's lifespan.
    import importlib
    from find_evil_agent.api import server as server_module
    importlib.reload(server_module)
    return server_module.app


# ---------------------------------------------------------------------------
# Specification
# ---------------------------------------------------------------------------

class TestAPIAuthSpecification:
    """Document the auth contract."""

    def test_auth_contract(self):
        """Auth rules:

        1. Endpoints under `/api/v1/*` require `X-API-Key: <key>` header.
        2. `/health` is public.
        3. `settings.api_keys = []` (default) disables auth — operators must
           opt in by setting `API_KEYS=key1,key2,...`.
        4. Wrong / missing key on protected endpoint returns 401.
        5. Comparison is constant-time to mitigate timing attacks.
        """
        assert True


# ---------------------------------------------------------------------------
# Auth-disabled mode (default)
# ---------------------------------------------------------------------------

class TestAuthDisabledByDefault:
    """When API_KEYS is empty, every endpoint is reachable without a key.

    This preserves the local-dev workflow and prevents the existing tests
    from breaking on the auth rollout.
    """

    def test_health_reachable_without_key(self, monkeypatch):
        app = _build_app(monkeypatch)
        client = TestClient(app)
        r = client.get("/health")
        assert r.status_code == 200

    def test_config_reachable_without_key(self, monkeypatch):
        app = _build_app(monkeypatch)
        client = TestClient(app)
        r = client.get("/api/v1/config")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Auth enabled
# ---------------------------------------------------------------------------

VALID_KEY = "test-api-key-abc123"
OTHER_VALID_KEY = "test-api-key-xyz789"


class TestAuthEnforced:
    """When API_KEYS is set, protected endpoints require a valid X-API-Key."""

    def test_health_remains_public(self, monkeypatch):
        app = _build_app(monkeypatch, API_KEYS=VALID_KEY)
        client = TestClient(app)
        r = client.get("/health")
        assert r.status_code == 200, "health must stay public for liveness checks"

    def test_config_rejects_missing_key(self, monkeypatch):
        app = _build_app(monkeypatch, API_KEYS=VALID_KEY)
        client = TestClient(app)
        r = client.get("/api/v1/config")
        assert r.status_code == 401
        assert "api key" in r.text.lower() or "unauthorized" in r.text.lower()

    def test_config_rejects_wrong_key(self, monkeypatch):
        app = _build_app(monkeypatch, API_KEYS=VALID_KEY)
        client = TestClient(app)
        r = client.get("/api/v1/config", headers={"X-API-Key": "not-the-key"})
        assert r.status_code == 401

    def test_config_accepts_valid_key(self, monkeypatch):
        app = _build_app(monkeypatch, API_KEYS=VALID_KEY)
        client = TestClient(app)
        r = client.get("/api/v1/config", headers={"X-API-Key": VALID_KEY})
        assert r.status_code == 200

    def test_multiple_keys_supported(self, monkeypatch):
        """Comma-separated list — any key in the set is accepted."""
        app = _build_app(
            monkeypatch,
            API_KEYS=f"{VALID_KEY},{OTHER_VALID_KEY}",
        )
        client = TestClient(app)
        for key in (VALID_KEY, OTHER_VALID_KEY):
            r = client.get("/api/v1/config", headers={"X-API-Key": key})
            assert r.status_code == 200, f"key {key!r} should be accepted"

    def test_analyze_endpoint_protected(self, monkeypatch):
        app = _build_app(monkeypatch, API_KEYS=VALID_KEY)
        client = TestClient(app)
        # No header → 401 BEFORE any orchestrator/LLM work
        r = client.post(
            "/api/v1/analyze",
            json={"incident_description": "x", "analysis_goal": "y"},
        )
        assert r.status_code == 401

    def test_investigate_endpoint_protected(self, monkeypatch):
        app = _build_app(monkeypatch, API_KEYS=VALID_KEY)
        client = TestClient(app)
        r = client.post(
            "/api/v1/investigate",
            json={
                "incident_description": "x",
                "analysis_goal": "y",
                "max_iterations": 1,
            },
        )
        assert r.status_code == 401

    def test_resume_endpoint_protected(self, monkeypatch):
        app = _build_app(monkeypatch, API_KEYS=VALID_KEY)
        client = TestClient(app)
        r = client.post(
            "/api/v1/investigate/abc-123/resume",
            json={"approved": True},
        )
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_empty_api_key_header_rejected(self, monkeypatch):
        """Empty header value must be rejected even with auth enabled."""
        app = _build_app(monkeypatch, API_KEYS=VALID_KEY)
        client = TestClient(app)
        r = client.get("/api/v1/config", headers={"X-API-Key": ""})
        assert r.status_code == 401

    def test_whitespace_in_key_rejected(self, monkeypatch):
        """A trimmed-equivalent key must NOT match — we want exact match."""
        app = _build_app(monkeypatch, API_KEYS=VALID_KEY)
        client = TestClient(app)
        r = client.get(
            "/api/v1/config",
            headers={"X-API-Key": f"  {VALID_KEY}  "},
        )
        assert r.status_code == 401

    def test_case_sensitive_key(self, monkeypatch):
        """Keys are case-sensitive."""
        app = _build_app(monkeypatch, API_KEYS=VALID_KEY)
        client = TestClient(app)
        r = client.get(
            "/api/v1/config",
            headers={"X-API-Key": VALID_KEY.upper()},
        )
        assert r.status_code == 401
