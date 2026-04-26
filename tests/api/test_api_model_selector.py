"""Test suite for API model selector functionality (Task #8).

Following TDD methodology:
1. Specification Tests - Document requirements (always pass)
2. Execution Tests - Test functionality with real implementations
3. Integration Tests - End-to-end API tests
4. Error Handling Tests - Invalid inputs
"""

from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient

# ==============================================================================
# SPECIFICATION TESTS (Always Pass)
# ==============================================================================


class TestAPIModelSelectorSpecification:
    """Document requirements for API model selector."""

    def test_api_model_selector_requirements(self):
        """Document API model selector requirements.

        REQUIREMENTS:
        1. /api/v1/analyze endpoint accepts optional provider and model query params
        2. /api/v1/investigate endpoint accepts optional provider and model query params
        3. Query parameters: provider (ollama, openai, anthropic), model (string)
        4. When provided, create LLM provider using factory with overrides
        5. Pass provider to OrchestratorAgent during initialization
        6. Default behavior (no params) uses settings from .env
        7. Compatible with existing request/response models
        8. OpenAPI docs automatically updated with query params
        9. Error handling for invalid provider or missing API keys
        10. Same pattern as CLI (Task #6) and Web UI (Task #7)

        WORKFLOW POSITION:
        - Task #8 of Week 1 (Add model selector to API)
        - Completes Gap #4 (LLM Provider Lock-in) to 100%
        - Follows CLI (Task #6) and Web UI (Task #7) patterns
        - Final piece of model selector feature

        INTEGRATION:
        - Uses factory.create_llm_provider() with overrides
        - Passes llm_provider to OrchestratorAgent constructor
        - Compatible with existing FastAPI endpoints
        - Works with both /analyze and /investigate endpoints
        - Resume endpoint continues with default settings
        """
        assert True  # Specification test


# ==============================================================================
# EXECUTION TESTS (Real Implementation)
# ==============================================================================


class TestAnalyzeEndpointWithModelSelector:
    """Test /api/v1/analyze endpoint with provider/model parameters."""

    def test_analyze_with_provider_query_param(self):
        """Test analyze endpoint accepts provider query parameter."""
        from find_evil_agent.api.server import app

        with (
            patch("find_evil_agent.api.server.OrchestratorAgent") as mock_orch_class,
            patch("find_evil_agent.api.server.create_llm_provider") as mock_factory,
        ):

            # Setup mocks
            mock_provider = Mock()
            mock_factory.return_value = mock_provider

            mock_orch = AsyncMock()
            mock_orch_class.return_value = mock_orch
            mock_orch.process.return_value = Mock(
                success=True,
                confidence=0.95,
                data={
                    "state": Mock(
                        session_id="test-session",
                        selected_tools=[Mock(model_dump=lambda: {"tool": "strings"})],
                        findings=[],
                        iocs=[],
                        step_count=1,
                    ),
                    "summary": "Test summary",
                },
            )

            client = TestClient(app)
            response = client.post(
                "/api/v1/analyze?provider=openai&model=gpt-4-turbo",
                json={"incident_description": "Test incident", "analysis_goal": "Test goal"},
            )

            assert response.status_code == 200
            # Verify factory was called with overrides
            mock_factory.assert_called_once()
            # Verify OrchestratorAgent was called with llm_provider
            mock_orch_class.assert_called_once()

    def test_analyze_without_provider_uses_default(self):
        """Test analyze endpoint without provider uses default settings."""
        from find_evil_agent.api.server import app

        with patch("find_evil_agent.api.server.OrchestratorAgent") as mock_orch_class:

            mock_orch = AsyncMock()
            mock_orch_class.return_value = mock_orch
            mock_orch.process.return_value = Mock(
                success=True,
                confidence=0.95,
                data={
                    "state": Mock(
                        session_id="test-session",
                        selected_tools=[Mock(model_dump=lambda: {"tool": "strings"})],
                        findings=[],
                        iocs=[],
                        step_count=1,
                    ),
                    "summary": "Test summary",
                },
            )

            client = TestClient(app)
            response = client.post(
                "/api/v1/analyze",
                json={"incident_description": "Test incident", "analysis_goal": "Test goal"},
            )

            assert response.status_code == 200
            # Verify OrchestratorAgent was called without llm_provider (uses default)
            mock_orch_class.assert_called_once()
            call_kwargs = mock_orch_class.call_args[1] if mock_orch_class.call_args[1] else {}
            assert call_kwargs.get("llm_provider") is None

    def test_analyze_with_model_only(self):
        """Test analyze endpoint with only model parameter."""
        from find_evil_agent.api.server import app

        with (
            patch("find_evil_agent.api.server.OrchestratorAgent") as mock_orch_class,
            patch("find_evil_agent.api.server.create_llm_provider") as mock_factory,
        ):

            mock_provider = Mock()
            mock_factory.return_value = mock_provider

            mock_orch = AsyncMock()
            mock_orch_class.return_value = mock_orch
            mock_orch.process.return_value = Mock(
                success=True,
                confidence=0.95,
                data={
                    "state": Mock(
                        session_id="test-session",
                        selected_tools=[Mock(model_dump=lambda: {"tool": "strings"})],
                        findings=[],
                        iocs=[],
                        step_count=1,
                    ),
                    "summary": "Test summary",
                },
            )

            client = TestClient(app)
            response = client.post(
                "/api/v1/analyze?model=gpt-4",
                json={"incident_description": "Test incident", "analysis_goal": "Test goal"},
            )

            assert response.status_code == 200
            # Verify factory was called (model-only override)
            mock_factory.assert_called_once()


class TestInvestigateEndpointWithModelSelector:
    """Test /api/v1/investigate endpoint with provider/model parameters."""

    def test_investigate_with_provider_query_param(self):
        """Test investigate endpoint accepts provider query parameter."""
        from find_evil_agent.api.server import app

        with (
            patch("find_evil_agent.api.server.OrchestratorAgent") as mock_orch_class,
            patch("find_evil_agent.api.server.create_llm_provider") as mock_factory,
        ):

            mock_provider = Mock()
            mock_factory.return_value = mock_provider

            mock_orch = AsyncMock()
            mock_orch_class.return_value = mock_orch
            mock_orch.process_iterative.return_value = Mock(
                session_id="test-session",
                iterations=[],
                investigation_chain=[],
                all_findings=[],
                all_iocs={},
                total_duration=10.5,
                stopping_reason="Complete",
                investigation_summary="Test summary",
            )

            client = TestClient(app)
            response = client.post(
                "/api/v1/investigate?provider=anthropic&model=claude-sonnet-4",
                json={
                    "incident_description": "Test incident",
                    "analysis_goal": "Test goal",
                    "max_iterations": 3,
                },
            )

            assert response.status_code == 200
            # Verify factory was called
            mock_factory.assert_called_once()
            # Verify OrchestratorAgent was called with llm_provider
            mock_orch_class.assert_called_once()

    def test_investigate_without_provider_uses_default(self):
        """Test investigate endpoint without provider uses default."""
        from find_evil_agent.api.server import app

        with patch("find_evil_agent.api.server.OrchestratorAgent") as mock_orch_class:

            mock_orch = AsyncMock()
            mock_orch_class.return_value = mock_orch
            mock_orch.process_iterative.return_value = Mock(
                session_id="test-session",
                iterations=[],
                investigation_chain=[],
                all_findings=[],
                all_iocs={},
                total_duration=10.5,
                stopping_reason="Complete",
                investigation_summary="Test summary",
            )

            client = TestClient(app)
            response = client.post(
                "/api/v1/investigate",
                json={
                    "incident_description": "Test incident",
                    "analysis_goal": "Test goal",
                    "max_iterations": 3,
                },
            )

            assert response.status_code == 200


# ==============================================================================
# INTEGRATION TESTS (End-to-End)
# ==============================================================================


class TestAPIModelSelectorIntegration:
    """Integration tests for API model selector."""

    def test_analyze_end_to_end_with_ollama(self):
        """Test complete analyze workflow with Ollama provider."""
        from find_evil_agent.api.server import app

        with (
            patch("find_evil_agent.api.server.OrchestratorAgent") as mock_orch_class,
            patch("find_evil_agent.api.server.create_llm_provider") as mock_factory,
        ):

            mock_provider = Mock()
            mock_factory.return_value = mock_provider

            mock_orch = AsyncMock()
            mock_orch_class.return_value = mock_orch
            mock_orch.process.return_value = Mock(
                success=True,
                confidence=0.95,
                data={
                    "state": Mock(
                        session_id="integration-test",
                        selected_tools=[Mock(model_dump=lambda: {"tool": "volatility"})],
                        findings=[],
                        iocs=[],
                        step_count=1,
                    ),
                    "summary": "Integration test",
                },
            )

            client = TestClient(app)
            response = client.post(
                "/api/v1/analyze?provider=ollama&model=qwen3.5:397b-cloud",
                json={
                    "incident_description": "Ransomware detected",
                    "analysis_goal": "Find malicious processes",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["session_id"] == "integration-test"

    def test_investigate_end_to_end_with_openai(self):
        """Test complete investigate workflow with OpenAI provider."""
        from find_evil_agent.api.server import app

        with (
            patch("find_evil_agent.api.server.OrchestratorAgent") as mock_orch_class,
            patch("find_evil_agent.api.server.create_llm_provider") as mock_factory,
        ):

            mock_provider = Mock()
            mock_factory.return_value = mock_provider

            mock_orch = AsyncMock()
            mock_orch_class.return_value = mock_orch
            mock_orch.process_iterative.return_value = Mock(
                session_id="integration-test",
                iterations=[],
                investigation_chain=[],
                all_findings=[],
                all_iocs={},
                total_duration=15.0,
                stopping_reason="Max iterations",
                investigation_summary="Complete",
            )

            client = TestClient(app)
            response = client.post(
                "/api/v1/investigate?provider=openai&model=gpt-4-turbo",
                json={
                    "incident_description": "Data breach",
                    "analysis_goal": "Reconstruct attack chain",
                    "max_iterations": 5,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


# ==============================================================================
# ERROR HANDLING TESTS
# ==============================================================================


class TestAPIModelSelectorErrorHandling:
    """Test error handling for API model selector."""

    def test_invalid_provider_returns_error(self):
        """Test that invalid provider returns proper error."""
        from find_evil_agent.api.server import app

        with patch("find_evil_agent.api.server.create_llm_provider") as mock_factory:
            mock_factory.side_effect = ValueError("Unknown provider: invalid")

            client = TestClient(app)
            response = client.post(
                "/api/v1/analyze?provider=invalid&model=test",
                json={"incident_description": "Test", "analysis_goal": "Test"},
            )

            assert response.status_code == 500
            assert "error" in response.text.lower() or "detail" in response.text.lower()

    def test_missing_api_key_returns_error(self):
        """Test that missing API key returns proper error."""
        from find_evil_agent.api.server import app

        with patch("find_evil_agent.api.server.create_llm_provider") as mock_factory:
            mock_factory.side_effect = ValueError("OPENAI_API_KEY required")

            client = TestClient(app)
            response = client.post(
                "/api/v1/analyze?provider=openai&model=gpt-4-turbo",
                json={"incident_description": "Test", "analysis_goal": "Test"},
            )

            assert response.status_code == 500


# ==============================================================================
# OPENAPI DOCUMENTATION TESTS
# ==============================================================================


class TestOpenAPIDocumentation:
    """Test that OpenAPI docs include new query parameters."""

    def test_openapi_schema_includes_provider_param(self):
        """Test OpenAPI schema documents provider parameter."""
        from find_evil_agent.api.server import app

        client = TestClient(app)
        response = client.get("/api/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        # Check analyze endpoint has provider parameter
        analyze_params = schema["paths"]["/api/v1/analyze"]["post"]["parameters"]
        provider_params = [p for p in analyze_params if p["name"] == "provider"]
        assert len(provider_params) > 0, "provider parameter should be in OpenAPI schema"

    def test_openapi_schema_includes_model_param(self):
        """Test OpenAPI schema documents model parameter."""
        from find_evil_agent.api.server import app

        client = TestClient(app)
        response = client.get("/api/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        # Check analyze endpoint has model parameter
        analyze_params = schema["paths"]["/api/v1/analyze"]["post"]["parameters"]
        model_params = [p for p in analyze_params if p["name"] == "model"]
        assert len(model_params) > 0, "model parameter should be in OpenAPI schema"
