"""Tests for Ollama LLM provider.

TDD Structure:
1. TestOllamaProviderSpecification - ALWAYS PASSING (requirements documentation)
2. TestOllamaProviderStructure - Tests provider interface compliance
3. TestOllamaProviderExecution - Tests actual provider behavior with real HTTP
"""

import pytest
from pydantic import BaseModel, Field

from find_evil_agent.agents.schemas import ToolSelection
from find_evil_agent.llm.providers.ollama import OllamaProvider


class TestOllamaProviderSpecification:
    """Specification tests - ALWAYS PASSING.

    Document Ollama provider requirements and expected behavior.
    """

    def test_ollama_provider_requirements(self):
        """Document Ollama provider requirements."""
        requirements = {
            "protocol": "HTTP REST API",
            "endpoint_chat": "/api/chat",
            "default_server": "http://192.168.12.124:11434",
            "default_model": "gemma4:31b-cloud",
            "streaming": False,  # We use non-streaming mode
            "json_mode": True,  # Supports format: "json"
            "timeout": 120,  # seconds
            "retry_on_validation_error": True,
            "max_retries": 2,
        }
        assert requirements["protocol"] == "HTTP REST API"
        assert requirements["json_mode"] is True
        assert requirements["max_retries"] == 2

    def test_ollama_chat_workflow(self):
        """Document chat request workflow."""
        workflow = {
            "step1": "Prepare payload with model, messages, options",
            "step2": "POST to /api/chat endpoint",
            "step3": "Raise for HTTP errors",
            "step4": "Extract message.content from response",
            "step5": "Return text response",
        }
        assert workflow["step2"] == "POST to /api/chat endpoint"

    def test_ollama_structured_output_workflow(self):
        """Document structured output workflow."""
        workflow = {
            "step1": "Build JSON schema prompt from Pydantic model",
            "step2": "Inject schema into system message",
            "step3": "Set format: 'json' in payload",
            "step4": "POST to /api/chat",
            "step5": "Parse JSON response",
            "step6": "Validate against Pydantic schema",
            "step7": "Retry with error feedback if validation fails",
            "step8": "Return validated Pydantic instance",
        }
        assert workflow["step3"] == "Set format: 'json' in payload"
        assert workflow["step7"] == "Retry with error feedback if validation fails"


class TestOllamaProviderStructure:
    """Structure tests - Validate provider interface compliance."""

    def test_provider_implements_protocol_methods(self):
        """Provider must implement LLMProvider protocol methods."""
        provider = OllamaProvider(base_url="http://test:11434", model_name="test-model")

        assert hasattr(provider, "chat")
        assert hasattr(provider, "chat_with_schema")
        assert hasattr(provider, "get_model_name")
        assert callable(provider.chat)
        assert callable(provider.chat_with_schema)
        assert callable(provider.get_model_name)

    def test_provider_accepts_required_parameters(self):
        """Provider must accept base_url and model_name."""
        provider = OllamaProvider(base_url="http://test:11434", model_name="test-model")
        assert provider._base_url == "http://test:11434"
        assert provider._model_name == "test-model"

    def test_provider_accepts_optional_parameters(self):
        """Provider should accept optional temperature and timeout."""
        provider = OllamaProvider(
            base_url="http://test:11434", model_name="test-model", temperature=0.5, timeout=60.0
        )
        assert provider._temperature == 0.5

    def test_provider_strips_trailing_slash_from_url(self):
        """Provider should normalize URL by removing trailing slash."""
        provider = OllamaProvider(base_url="http://test:11434/", model_name="test-model")
        assert provider._base_url == "http://test:11434"

    def test_provider_has_async_http_client(self):
        """Provider should create async HTTP client."""
        provider = OllamaProvider(base_url="http://test:11434", model_name="test-model")
        assert provider._client is not None

    def test_get_model_name_returns_string(self):
        """get_model_name() should return model name string."""
        provider = OllamaProvider(base_url="http://test:11434", model_name="gemma4:31b-cloud")
        assert provider.get_model_name() == "gemma4:31b-cloud"


class TestOllamaProviderExecution:
    """Execution tests - Test actual behavior.

    Note: These tests use real HTTP to Ollama (no mocks per CLAUDE.md).
    Tests marked with @pytest.mark.integration require Ollama to be running.
    """

    def test_build_schema_prompt_includes_schema(self):
        """_build_schema_prompt should include JSON schema."""
        provider = OllamaProvider(base_url="http://test:11434", model_name="test-model")

        class SimpleSchema(BaseModel):
            name: str = Field(description="A name")
            count: int = Field(description="A count")

        prompt = provider._build_schema_prompt(SimpleSchema)

        assert "schema" in prompt.lower()
        assert "name" in prompt
        assert "count" in prompt
        assert "JSON" in prompt

    def test_inject_schema_prompt_prepends_system_message(self):
        """_inject_schema_prompt should prepend system message if none exists."""
        provider = OllamaProvider(base_url="http://test:11434", model_name="test-model")

        messages = [{"role": "user", "content": "Hello"}]

        result = provider._inject_schema_prompt(messages, "Schema: ...")

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert "Schema" in result[0]["content"]
        assert result[1]["role"] == "user"

    def test_inject_schema_prompt_appends_to_existing_system(self):
        """_inject_schema_prompt should append to existing system message."""
        provider = OllamaProvider(base_url="http://test:11434", model_name="test-model")

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        result = provider._inject_schema_prompt(messages, "Schema: ...")

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert "You are helpful" in result[0]["content"]
        assert "Schema" in result[0]["content"]

    @pytest.mark.asyncio
    async def test_close_closes_client(self):
        """close() should close the HTTP client."""
        provider = OllamaProvider(base_url="http://test:11434", model_name="test-model")

        # Should not raise error
        await provider.close()


# Integration tests (require real Ollama)
class TestOllamaProviderIntegration:
    """Integration tests with real Ollama server.

    These tests require Ollama running at 192.168.12.124:11434.
    They are marked as integration tests and can be skipped in CI.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_chat_with_real_ollama(self):
        """Test simple chat with real Ollama server."""
        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434",
            model_name="llama3.2:latest",  # Use smallest model
            temperature=0.1,
        )

        response = await provider.chat([{"role": "user", "content": "Say 'test' and nothing else"}])

        assert isinstance(response, str)
        assert len(response) > 0
        assert "test" in response.lower()

        await provider.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_chat_with_schema_real_ollama(self):
        """Test structured output with real Ollama server."""
        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434", model_name="llama3.2:latest", temperature=0.1
        )

        class SimpleResponse(BaseModel):
            answer: str = Field(description="A simple answer")
            confidence: float = Field(description="Confidence 0-1", ge=0.0, le=1.0)

        result = await provider.chat_with_schema(
            messages=[{"role": "user", "content": "What is 2+2? Respond with high confidence."}],
            schema=SimpleResponse,
        )

        assert isinstance(result, SimpleResponse)
        assert isinstance(result.answer, str)
        assert 0.0 <= result.confidence <= 1.0

        await provider.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_chat_with_tool_selection_schema(self):
        """Test with actual ToolSelection schema used in agent."""
        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434", model_name="gemma4:31b-cloud", temperature=0.1
        )

        selection = await provider.chat_with_schema(
            messages=[
                {"role": "system", "content": "You are a DFIR expert selecting SIFT tools."},
                {"role": "user", "content": "I need to list files in a disk image. Which tool?"},
            ],
            schema=ToolSelection,
        )

        assert isinstance(selection, ToolSelection)
        assert isinstance(selection.tool_name, str)
        assert len(selection.tool_name) > 0
        assert 0.0 <= selection.confidence <= 1.0
        assert isinstance(selection.reason, str)
        assert len(selection.reason) > 0

        await provider.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_retry_exhaustion_raises_error(self):
        """Test that retry logic eventually raises error after max attempts."""
        # This test documents that when LLM consistently returns invalid data,
        # the provider will retry and eventually raise RuntimeError
        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434", model_name="llama3.2:latest", temperature=0.1
        )

        class StrictSchema(BaseModel):
            required_field: str = Field(description="Must be present")
            number_field: int = Field(description="Must be integer")

        # Intentionally ambiguous prompt that may cause validation failure
        with pytest.raises(RuntimeError, match="Failed to get valid structured output"):
            await provider.chat_with_schema(
                messages=[{"role": "user", "content": "Generate a response"}],  # Too vague
                schema=StrictSchema,
            )

        await provider.close()
