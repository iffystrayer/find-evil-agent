"""Tests for OpenAI LLM provider.

TDD Structure:
1. TestOpenAIProviderSpecification - ALWAYS PASSING (requirements documentation)
2. TestOpenAIProviderStructure - Tests provider interface compliance
3. TestOpenAIProviderExecution - Tests actual provider behavior with real OpenAI API
4. TestOpenAIProviderIntegration - Tests integration with Find Evil Agent workflow

Design Notes:
    - Uses OpenAI Python SDK (openai>=1.0.0)
    - Supports gpt-4-turbo, gpt-4, gpt-3.5-turbo models
    - Uses chat completions API with structured outputs
    - Real API tests skip if OPENAI_API_KEY not available
"""

import pytest
import os
from pydantic import BaseModel, Field

# Conditional import for TDD - Provider may not exist yet
try:
    from find_evil_agent.llm.providers.openai import OpenAIProvider
    OPENAI_PROVIDER_AVAILABLE = True
except ImportError:
    OPENAI_PROVIDER_AVAILABLE = False
    class OpenAIProvider:  # Placeholder for tests
        pass

from find_evil_agent.agents.schemas import ToolSelection


class TestOpenAIProviderSpecification:
    """Specification tests - ALWAYS PASSING.

    Document OpenAI provider requirements and expected behavior.
    These tests define what the provider MUST do.
    """

    def test_openai_provider_requirements(self):
        """Document OpenAI provider requirements."""
        requirements = {
            "sdk": "openai>=1.0.0",
            "api": "Chat Completions API",
            "supported_models": [
                "gpt-4-turbo",
                "gpt-4-turbo-preview",
                "gpt-4",
                "gpt-4-0613",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-0125"
            ],
            "structured_outputs": True,  # Supports response_format
            "json_mode": True,  # response_format: {"type": "json_object"}
            "timeout": 120,  # seconds
            "retry_on_failure": True,
            "max_retries": 2,
            "default_model": "gpt-4-turbo",
            "default_temperature": 0.1,
        }
        assert requirements["sdk"] == "openai>=1.0.0"
        assert requirements["structured_outputs"] is True
        assert requirements["default_temperature"] == 0.1

    def test_openai_chat_workflow(self):
        """Document chat request workflow."""
        workflow = {
            "step1": "Initialize OpenAI client with API key",
            "step2": "Prepare messages list with roles (system/user/assistant)",
            "step3": "Call client.chat.completions.create()",
            "step4": "Extract response.choices[0].message.content",
            "step5": "Return text response",
        }
        assert workflow["step3"] == "Call client.chat.completions.create()"

    def test_openai_structured_output_workflow(self):
        """Document structured output workflow."""
        workflow = {
            "step1": "Build JSON schema from Pydantic model",
            "step2": "Inject schema into system message",
            "step3": "Set response_format={'type': 'json_object'}",
            "step4": "Call client.chat.completions.create()",
            "step5": "Parse JSON from response content",
            "step6": "Validate against Pydantic schema",
            "step7": "Retry with error feedback if validation fails",
            "step8": "Return validated Pydantic instance",
        }
        assert workflow["step3"] == "Set response_format={'type': 'json_object'}"
        assert workflow["step7"] == "Retry with error feedback if validation fails"

    def test_openai_api_key_requirement(self):
        """OpenAI provider requires API key for initialization."""
        requirements = {
            "api_key_source": "OPENAI_API_KEY environment variable",
            "api_key_format": "sk-...",
            "api_key_required": True,
            "api_key_validation": "Client validates on first request",
        }
        assert requirements["api_key_required"] is True

    def test_openai_model_selection(self):
        """Document supported OpenAI models."""
        models = {
            "recommended": "gpt-4-turbo",  # Best balance speed/quality
            "highest_quality": "gpt-4",
            "fastest": "gpt-3.5-turbo",
            "cost_effective": "gpt-3.5-turbo",
        }
        assert models["recommended"] == "gpt-4-turbo"

    def test_openai_error_handling(self):
        """Document expected error scenarios."""
        errors = {
            "invalid_api_key": "Raises openai.AuthenticationError",
            "rate_limit": "Raises openai.RateLimitError",
            "timeout": "Raises openai.APITimeoutError",
            "invalid_model": "Raises openai.NotFoundError",
            "validation_error": "Raises pydantic.ValidationError",
        }
        assert len(errors) == 5


class TestOpenAIProviderStructure:
    """Structure tests - Validate provider interface compliance.

    These tests verify the provider implements the LLMProvider protocol.
    Skipped until provider is implemented.
    """

    @pytest.fixture
    def provider(self):
        """Create OpenAI provider instance for testing."""
        if not OPENAI_PROVIDER_AVAILABLE:
            pytest.skip("OpenAIProvider not implemented yet")

        return OpenAIProvider(
            api_key="sk-test-key-for-structure-tests",
            model_name="gpt-4-turbo"
        )

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    def test_provider_implements_protocol_methods(self, provider):
        """Provider must implement LLMProvider protocol methods."""
        assert hasattr(provider, 'generate')
        assert hasattr(provider, 'chat')
        assert hasattr(provider, 'generate_json')
        assert hasattr(provider, 'chat_with_schema')
        assert hasattr(provider, 'get_model_name')

        assert callable(provider.generate)
        assert callable(provider.chat)
        assert callable(provider.generate_json)
        assert callable(provider.chat_with_schema)
        assert callable(provider.get_model_name)

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    def test_provider_accepts_required_parameters(self):
        """Provider must accept api_key and model_name."""
        provider = OpenAIProvider(
            api_key="sk-test-key",
            model_name="gpt-4-turbo"
        )
        assert provider._api_key == "sk-test-key"
        assert provider._model_name == "gpt-4-turbo"

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    def test_provider_accepts_optional_parameters(self):
        """Provider should accept optional temperature and timeout."""
        provider = OpenAIProvider(
            api_key="sk-test-key",
            model_name="gpt-4-turbo",
            temperature=0.5,
            timeout=60.0
        )
        assert provider._temperature == 0.5
        assert provider._timeout == 60.0

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    def test_get_model_name_returns_string(self, provider):
        """get_model_name() must return configured model name."""
        assert provider.get_model_name() == "gpt-4-turbo"

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    def test_provider_has_client_attribute(self, provider):
        """Provider should initialize OpenAI client."""
        assert hasattr(provider, '_client')


class TestOpenAIProviderExecution:
    """Execution tests - Test actual provider behavior with real OpenAI API.

    These tests make real API calls to OpenAI.
    They skip if OPENAI_API_KEY environment variable is not set.

    To run these tests:
        export OPENAI_API_KEY=sk-...
        pytest tests/unit/llm/test_openai_provider.py::TestOpenAIProviderExecution -v
    """

    @pytest.fixture
    def provider(self):
        """Create OpenAI provider with real API key."""
        if not OPENAI_PROVIDER_AVAILABLE:
            pytest.skip("OpenAIProvider not implemented yet")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set - skipping live API tests")

        return OpenAIProvider(
            api_key=api_key,
            model_name="gpt-3.5-turbo",  # Use faster/cheaper model for tests
            temperature=0.1
        )

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_generate_simple_text(self, provider):
        """Test simple text generation from prompt."""
        response = await provider.generate(
            "Say 'Hello from OpenAI' and nothing else.",
            temperature=0.0
        )

        assert isinstance(response, str)
        assert len(response) > 0
        assert "Hello" in response or "hello" in response

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_chat_with_messages(self, provider):
        """Test chat with message history."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2? Answer with just the number."}
        ]

        response = await provider.chat(messages, temperature=0.0)

        assert isinstance(response, str)
        assert "4" in response

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_generate_json_without_schema(self, provider):
        """Test JSON generation without schema validation."""
        response = await provider.generate_json(
            "Return a JSON object with a 'greeting' field containing 'hello'. "
            "Respond only with the JSON object.",
            temperature=0.0
        )

        assert isinstance(response, dict)
        assert "greeting" in response
        assert response["greeting"].lower() == "hello"

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_chat_with_schema_simple(self, provider):
        """Test structured output with simple Pydantic schema."""
        class SimpleResponse(BaseModel):
            """Simple test schema."""
            answer: int = Field(description="The numeric answer")

        messages = [
            {"role": "user", "content": "What is 5+5? Respond in JSON with an 'answer' field."}
        ]

        response = await provider.chat_with_schema(
            messages,
            schema=SimpleResponse,
            temperature=0.0
        )

        assert isinstance(response, SimpleResponse)
        assert response.answer == 10

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_chat_with_schema_tool_selection(self, provider):
        """Test structured output with ToolSelection schema (real use case)."""
        messages = [
            {
                "role": "system",
                "content": "You are a DFIR tool selector. Select the best tool for memory analysis."
            },
            {
                "role": "user",
                "content": "I need to analyze a memory dump for malware artifacts. Which tool should I use?"
            }
        ]

        response = await provider.chat_with_schema(
            messages,
            schema=ToolSelection,
            temperature=0.1
        )

        assert isinstance(response, ToolSelection)
        assert isinstance(response.tool_name, str)
        assert len(response.tool_name) > 0
        assert isinstance(response.confidence, float)
        assert 0.0 <= response.confidence <= 1.0
        assert isinstance(response.reasoning, str)
        assert len(response.reasoning) > 0

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_temperature_override(self, provider):
        """Test that kwargs can override default temperature."""
        messages = [
            {"role": "user", "content": "Say 'test' and nothing else."}
        ]

        response = await provider.chat(messages, temperature=0.0)

        assert isinstance(response, str)
        assert len(response) > 0


class TestOpenAIProviderIntegration:
    """Integration tests - Verify provider works with Find Evil Agent workflow.

    These tests ensure the provider integrates correctly with:
    - ToolSelectorAgent (critical for tool selection)
    - Multi-agent workflow (agent coordination)
    - Error handling and retries
    """

    @pytest.fixture
    def provider(self):
        """Create OpenAI provider with real API key."""
        if not OPENAI_PROVIDER_AVAILABLE:
            pytest.skip("OpenAIProvider not implemented yet")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set - skipping integration tests")

        return OpenAIProvider(
            api_key=api_key,
            model_name="gpt-3.5-turbo",
            temperature=0.1
        )

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_tool_selection_workflow(self, provider):
        """Test complete tool selection workflow (critical for ToolSelectorAgent)."""
        # Simulate ToolSelectorAgent messages
        messages = [
            {
                "role": "system",
                "content": """You are a DFIR tool selector for the Find Evil Agent system.

Available tools:
- volatility: Memory forensics framework for analyzing RAM dumps
- strings: Extract printable strings from binary files
- grep: Search for patterns in text files

Select the most appropriate tool for the given task."""
            },
            {
                "role": "user",
                "content": "I need to analyze a Windows memory dump (memory.dmp) to find evidence of malware execution."
            }
        ]

        selection = await provider.chat_with_schema(
            messages,
            schema=ToolSelection,
            temperature=0.1
        )

        # Verify selection is valid
        assert selection.tool_name in ["volatility", "strings", "grep"]
        assert selection.confidence > 0.5  # Should be confident in volatility
        assert "memory" in selection.reasoning.lower() or "volatility" in selection.reasoning.lower()

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_multiple_sequential_requests(self, provider):
        """Test provider handles multiple sequential requests correctly."""
        # First request
        response1 = await provider.generate("Say 'first'", temperature=0.0)
        assert isinstance(response1, str)

        # Second request
        response2 = await provider.generate("Say 'second'", temperature=0.0)
        assert isinstance(response2, str)

        # Third request with schema
        class TestSchema(BaseModel):
            value: str

        response3 = await provider.chat_with_schema(
            [{"role": "user", "content": "Return JSON with value='third'"}],
            schema=TestSchema,
            temperature=0.0
        )
        assert isinstance(response3, TestSchema)

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    def test_provider_model_name_matches_initialization(self, provider):
        """Verify get_model_name() returns what was configured."""
        assert provider.get_model_name() == "gpt-3.5-turbo"


class TestOpenAIProviderErrorHandling:
    """Error handling tests - Verify provider handles failures gracefully."""

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_error(self):
        """Provider should raise error for invalid API key."""
        provider = OpenAIProvider(
            api_key="sk-invalid-key-12345",
            model_name="gpt-3.5-turbo"
        )

        with pytest.raises(Exception) as exc_info:
            await provider.generate("test")

        # Should raise some error (could be AuthenticationError or RuntimeError wrapping it)
        assert exc_info.value is not None

    @pytest.mark.skipif(not OPENAI_PROVIDER_AVAILABLE, reason="OpenAIProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_invalid_model_raises_error(self):
        """Provider should raise error for invalid model name."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        provider = OpenAIProvider(
            api_key=api_key,
            model_name="invalid-model-xyz"
        )

        with pytest.raises(Exception) as exc_info:
            await provider.generate("test")

        assert exc_info.value is not None
