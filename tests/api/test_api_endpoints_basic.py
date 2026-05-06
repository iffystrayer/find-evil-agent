"""C6.2: contract tests for the public-facing endpoints.

The existing API test files cover authentication, CORS, Pydantic bounds,
session-id typing, and the LLM model-selector query params. None pin the
*shape* of the ``/health`` and ``/api/v1/config`` response bodies or the
OpenAPI schema — so a refactor that silently drops a field could ship
without a regression. These tests close that gap.

No mocks. Drives the real FastAPI app via TestClient and reads the
public OpenAPI document.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_settings_singleton():
    from find_evil_agent.config import settings as settings_module

    settings_module._settings = None
    yield
    settings_module._settings = None


def _build_client() -> TestClient:
    from find_evil_agent.api import server as server_module

    importlib.reload(server_module)
    return TestClient(server_module.app)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_returns_200(self):
        client = _build_client()
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_response_shape(self):
        """All ``HealthResponse`` fields must be present and non-empty."""
        client = _build_client()
        body = client.get("/health").json()

        for field in ("status", "version", "llm_provider", "sift_vm_host"):
            assert field in body, f"missing {field!r} in health response"
            assert body[field], f"{field!r} must not be empty"

        assert body["status"] == "healthy"

    def test_health_has_no_auth_dependency(self, monkeypatch):
        """Even with auth enabled, ``/health`` must remain reachable for
        liveness probes — without the right key."""
        monkeypatch.setenv("API_KEYS", "secret-key-123")
        client = _build_client()
        resp = client.get("/health")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /api/v1/config
# ---------------------------------------------------------------------------


class TestConfigEndpoint:
    def test_config_returns_200_in_dev_mode(self):
        client = _build_client()
        resp = client.get("/api/v1/config")
        assert resp.status_code == 200

    def test_config_response_shape(self):
        client = _build_client()
        body = client.get("/api/v1/config").json()

        # All ``ConfigResponse`` fields must be present
        expected = {
            "llm_provider",
            "llm_model_name",
            "sift_vm_host",
            "sift_vm_port",
            "langfuse_enabled",
        }
        assert expected.issubset(body.keys()), (
            f"missing keys {expected - body.keys()!r} in config response"
        )

    def test_config_does_not_leak_api_keys(self, monkeypatch):
        """Operator API keys must never appear in the public config response."""
        monkeypatch.setenv("API_KEYS", "super-secret-key,another-secret")
        client = _build_client()
        body = client.get("/api/v1/config", headers={"X-API-Key": "super-secret-key"}).json()

        joined = " ".join(str(v) for v in body.values()).lower()
        assert "super-secret-key" not in joined
        assert "another-secret" not in joined
        assert "api_keys" not in body
        assert "api_key" not in body


# ---------------------------------------------------------------------------
# OpenAPI registration — regression guard for accidental endpoint deletion
# ---------------------------------------------------------------------------


class TestOpenAPIRegistration:
    def test_openapi_lists_all_advertised_endpoints(self):
        """If a route is removed by accident this guard catches it before
        a downstream client (frontend, MCP) breaks in production."""
        client = _build_client()
        spec = client.get("/api/openapi.json").json()
        paths = set(spec["paths"].keys())

        for route in (
            "/health",
            "/api/v1/config",
            "/api/v1/analyze",
            "/api/v1/investigate",
            "/api/v1/investigate/{session_id}/resume",
        ):
            assert route in paths, f"route {route!r} missing from OpenAPI schema"

    def test_resume_endpoint_session_id_typed_as_uuid_in_schema(self):
        """B5 contract: session_id is a UUID at the framework boundary."""
        client = _build_client()
        spec = client.get("/api/openapi.json").json()
        params = spec["paths"]["/api/v1/investigate/{session_id}/resume"]["post"]["parameters"]

        session_param = next(p for p in params if p["name"] == "session_id")
        assert session_param["schema"]["format"] == "uuid"
