"""500 response sanitization tests (B1 — TDD).

The API endpoints used `raise HTTPException(500, detail=str(e))`, which
shipped raw exception messages — including filesystem paths, internal
class names, and config snippets — to clients. Replace with a generic
detail and log the full traceback server-side via logger.exception.

Roadmap reference: Milestone B1 in CODE_REVIEW.md.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_settings_singleton():
    """Per-test Settings reload so env doesn't leak across tests/files."""
    from find_evil_agent.config import settings as settings_module
    settings_module._settings = None
    yield
    settings_module._settings = None


def _client_with_auth_disabled(monkeypatch):
    """Build a TestClient with API_KEYS empty (default dev mode)."""
    import importlib
    from find_evil_agent.api import server as server_module
    importlib.reload(server_module)
    return TestClient(server_module.app)


# ---------------------------------------------------------------------------
# Specification
# ---------------------------------------------------------------------------

class TestErrorSanitizationSpecification:
    """Document the contract."""

    def test_500_responses_must_be_generic(self):
        """Rules for 500 / unhandled-exception responses on `/api/v1/*`:

        1. Status code is 500 (not 200, not unhandled).
        2. `detail` is a generic string — never `str(e)` of the underlying
           exception.
        3. Specifically, the response body MUST NOT contain:
             - Internal class names (e.g., "LLMProviderEnum", "Pydantic")
             - File paths (e.g., "/Users/", "/root/")
             - The original invalid input value
        4. Server-side log MUST capture the full traceback (verified by
           the existence of `logger.exception` calls in production code).
        """
        assert True


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

# Tokens that must NEVER appear in a 500 response body — they leak
# implementation detail. Compared case-insensitively.
LEAK_INDICATORS = [
    "LLMProviderEnum",
    "Traceback",
    "/Users/",
    "/root/",
    "find_evil_agent.",
    "ValueError",
    "TypeError",
    "AttributeError",
    "KeyError",
]


def _assert_response_is_sanitized(response):
    body = response.text
    lowered = body.lower()
    for token in LEAK_INDICATORS:
        assert token.lower() not in lowered, (
            f"500 response leaked {token!r}:\n{body[:500]}"
        )


class TestAnalyzeEndpoint500:

    def test_invalid_provider_returns_generic_500(self, monkeypatch):
        """Hitting analyze with an unknown LLM provider is a real
        runtime error path. The 500 response must be sanitized."""
        client = _client_with_auth_disabled(monkeypatch)
        response = client.post(
            "/api/v1/analyze?provider=garbage_provider_name",
            json={
                "incident_description": "test incident",
                "analysis_goal": "test goal",
            },
        )
        assert response.status_code == 500
        _assert_response_is_sanitized(response)
        assert "garbage_provider_name" not in response.text


class TestInvestigateEndpoint500:

    def test_invalid_provider_returns_generic_500(self, monkeypatch):
        client = _client_with_auth_disabled(monkeypatch)
        response = client.post(
            "/api/v1/investigate?provider=garbage_provider_name",
            json={
                "incident_description": "test incident",
                "analysis_goal": "test goal",
                "max_iterations": 1,
            },
        )
        assert response.status_code == 500
        _assert_response_is_sanitized(response)
        assert "garbage_provider_name" not in response.text


class TestResumeEndpoint500:
    """The resume handler reaches into orchestrator state — an unknown
    session_id often triggers internal exceptions. Make sure those are
    sanitized too."""

    def test_unknown_session_returns_generic_500(self, monkeypatch):
        client = _client_with_auth_disabled(monkeypatch)
        response = client.post(
            "/api/v1/investigate/00000000-not-a-real-session/resume",
            json={"approved": True},
        )
        # Either 500 (orchestrator error) or 404. We accept both as long
        # as the 500 case is sanitized. If it's a 404, it's already
        # well-behaved.
        if response.status_code == 500:
            _assert_response_is_sanitized(response)


# ---------------------------------------------------------------------------
# Verify the production code uses logger.exception (not just logger.error)
# ---------------------------------------------------------------------------

class TestLoggerExceptionUsed:
    """B1 requires that traceback is captured server-side. Check the
    handlers call logger.exception(...) which logs sys.exc_info()
    automatically."""

    def test_handlers_use_logger_exception(self):
        from pathlib import Path
        server_path = Path(__file__).parent.parent.parent / "src" / "find_evil_agent" / "api" / "server.py"
        source = server_path.read_text()

        # These three handlers had `logger.error(f"... {e}")` previously
        # and must use `logger.exception(...)` after B1 so tracebacks are
        # captured.
        assert source.count("logger.exception(") >= 3, (
            "expected at least 3 logger.exception(...) calls — one per "
            f"protected handler. Found {source.count('logger.exception(')}."
        )

        # And no remaining `detail=str(e)` leak vector.
        assert "detail=str(e)" not in source, (
            "detail=str(e) still present — leaks raw exception text to clients"
        )
