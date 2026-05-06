"""B4: tighten CORS + add Pydantic length bounds.

Two related hardening fixes from the May 2026 remediation cycle:

1. CORS — drop ``allow_methods=["*"]`` / ``allow_headers=["*"]`` in favor of
   explicit allow-lists. With ``allow_credentials=True`` the wildcard is
   fragile if origins are ever widened.

2. Pydantic bounds — add ``min_length`` / ``max_length`` to
   ``incident_description`` and ``analysis_goal`` on ``AnalyzeRequest`` and
   ``InvestigateRequest``. Reject control characters in ``evidence_paths``
   inputs as a defense-in-depth check.

No mocks. Drives the real FastAPI app via TestClient.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_settings_singleton():
    """Reset Settings singleton before and after each test."""
    from find_evil_agent.config import settings as settings_module
    settings_module._settings = None
    yield
    settings_module._settings = None


def _build_app() -> TestClient:
    """Reload the API server module fresh and return a TestClient."""
    import importlib
    from find_evil_agent.api import server as server_module
    importlib.reload(server_module)
    return TestClient(server_module.app)


# ---------------------------------------------------------------------------
# CORS preflight
# ---------------------------------------------------------------------------

ALLOWED_ORIGIN = "http://localhost:15173"


class TestCORSExplicitAllowList:
    """Preflight responses must enumerate allowed methods and headers."""

    def test_preflight_only_advertises_methods_we_actually_serve(self):
        """Starlette expands ``allow_methods=['*']`` into every HTTP verb
        (DELETE, PATCH, PUT, ...). We only serve GET + POST + OPTIONS, so
        a hardened middleware config must not advertise DELETE/PATCH/PUT."""
        client = _build_app()
        resp = client.options(
            "/api/v1/analyze",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, X-API-Key",
            },
        )
        allow_methods = resp.headers.get("access-control-allow-methods", "")
        assert allow_methods != "*", "wildcard methods forbidden"
        upper = allow_methods.upper()
        assert "POST" in upper, "POST must be advertised"
        assert "GET" in upper, "GET must be advertised"
        # These are the verbs we explicitly do NOT serve. With ``allow_methods=*``
        # CORSMiddleware advertises them anyway; that is what B4 fixes.
        for forbidden in ("DELETE", "PUT", "PATCH"):
            assert forbidden not in upper, (
                f"CORS preflight advertised unsupported method {forbidden}: "
                f"got {allow_methods!r}"
            )

    def test_preflight_headers_are_explicit_not_wildcard(self):
        client = _build_app()
        resp = client.options(
            "/api/v1/analyze",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, X-API-Key",
            },
        )
        allow_headers = resp.headers.get("access-control-allow-headers", "")
        assert allow_headers != "*", (
            "CORS allow_headers must be an explicit list, not wildcard"
        )
        lowered = allow_headers.lower()
        assert "x-api-key" in lowered
        assert "content-type" in lowered

    def test_source_does_not_use_wildcard_cors(self):
        """Static guard: ``allow_methods=['*']`` / ``allow_headers=['*']``
        must not reappear in the API server source."""
        from pathlib import Path
        src = (
            Path(__file__).resolve().parents[2]
            / "src"
            / "find_evil_agent"
            / "api"
            / "server.py"
        )
        text = src.read_text()
        assert 'allow_methods=["*"]' not in text, (
            "CORS allow_methods=['*'] regressed (B4)"
        )
        assert 'allow_headers=["*"]' not in text, (
            "CORS allow_headers=['*'] regressed (B4)"
        )

    def test_unconfigured_origin_does_not_get_credentials(self):
        client = _build_app()
        resp = client.options(
            "/api/v1/analyze",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        # Origin not on allow-list: middleware should not echo
        # Allow-Origin header for it.
        assert resp.headers.get("access-control-allow-origin") not in (
            "http://evil.example.com",
            "*",
        )


# ---------------------------------------------------------------------------
# Pydantic length / control-char bounds
# ---------------------------------------------------------------------------

VALID_DESC = "Ransomware activity detected on a workstation"
VALID_GOAL = "Identify the malicious process and lateral movement"


class TestAnalyzeRequestBounds:
    def test_empty_incident_description_is_rejected(self):
        client = _build_app()
        resp = client.post(
            "/api/v1/analyze",
            json={"incident_description": "", "analysis_goal": VALID_GOAL},
        )
        assert resp.status_code == 422

    def test_too_short_incident_description_is_rejected(self):
        client = _build_app()
        resp = client.post(
            "/api/v1/analyze",
            json={"incident_description": "x", "analysis_goal": VALID_GOAL},
        )
        assert resp.status_code == 422

    def test_oversized_incident_description_is_rejected(self):
        client = _build_app()
        resp = client.post(
            "/api/v1/analyze",
            json={
                "incident_description": "a" * 20_000,
                "analysis_goal": VALID_GOAL,
            },
        )
        assert resp.status_code == 422

    def test_oversized_analysis_goal_is_rejected(self):
        client = _build_app()
        resp = client.post(
            "/api/v1/analyze",
            json={
                "incident_description": VALID_DESC,
                "analysis_goal": "g" * 20_000,
            },
        )
        assert resp.status_code == 422

    def test_control_characters_in_incident_description_are_rejected(self):
        client = _build_app()
        resp = client.post(
            "/api/v1/analyze",
            json={
                "incident_description": VALID_DESC + "\x00bad",
                "analysis_goal": VALID_GOAL,
            },
        )
        assert resp.status_code == 422

    def test_valid_request_is_not_blocked_by_validators(self):
        """Length/control-char checks must not regress the happy path. We
        accept any non-422 response — the request likely fails downstream
        because the test environment has no SIFT VM, but the framework
        boundary should not reject the payload itself.
        """
        client = _build_app()
        resp = client.post(
            "/api/v1/analyze",
            json={"incident_description": VALID_DESC, "analysis_goal": VALID_GOAL},
        )
        assert resp.status_code != 422


class TestInvestigateRequestBounds:
    def test_short_description_rejected(self):
        client = _build_app()
        resp = client.post(
            "/api/v1/investigate",
            json={
                "incident_description": "hi",
                "analysis_goal": VALID_GOAL,
                "max_iterations": 3,
            },
        )
        assert resp.status_code == 422

    def test_oversized_description_rejected(self):
        client = _build_app()
        resp = client.post(
            "/api/v1/investigate",
            json={
                "incident_description": "a" * 20_000,
                "analysis_goal": VALID_GOAL,
                "max_iterations": 3,
            },
        )
        assert resp.status_code == 422

    def test_control_char_in_goal_rejected(self):
        client = _build_app()
        resp = client.post(
            "/api/v1/investigate",
            json={
                "incident_description": VALID_DESC,
                "analysis_goal": VALID_GOAL + "\x07alert",
                "max_iterations": 3,
            },
        )
        assert resp.status_code == 422
