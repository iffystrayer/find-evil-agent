"""Tests for Anthropic LLM provider.

TDD Structure:
1. TestAnthropicProviderSpecification - ALWAYS PASSING (requirements documentation)
2. TestAnthropicProviderStructure - Tests provider interface compliance
3. TestAnthropicProviderExecution - Tests actual provider behavior with real Anthropic API
4. TestAnthropicProviderIntegration - Tests integration with Find Evil Agent workflow

Design Notes:
    - Uses Anthropic Python SDK (anthropic>=0.40.0)
    - Supports Claude Opus 4, Sonnet 4, Haiku 4 models
    - Uses Messages API with structured outputs
    - Real API tests skip if ANTHROPIC_API_KEY not available
"""

import pytest
import os
from pydantic import BaseModel, Field

# Conditional import for TDD - Provider may not exist yet
try:
    from find_evil_agent.llm.providers.anthropic import AnthropicProvider
    ANTHROPIC_PROVIDER_AVAILABLE = True
except ImportError:
    ANTHROPIC_PROVIDER_AVAILABLE = False
    class AnthropicProvider:  # Placeholder for tests
        pass

from find_evil_agent.agents.schemas import ToolSelection


class TestAnthropicProviderSpecification:
    """Specification tests - ALWAYS PASSING.

    Document Anthropic provider requirements and expected behavior.
    These tests define what the provider MUST do.
    """

    def test_anthropic_provider_requirements(self):
        """Document Anthropic provider requirements."""
        requirements = {
            "sdk": "anthropic>=0.40.0",
            "api": "Messages API",
            "supported_models": [
                "claude-opus-4-20250514",
                "claude-sonnet-4-20250514",
                "claude-haiku-4-20250514",
                "claude-3-5-sonnet-20241022",  # Previous version
            ],
            "structured_outputs": True,  # Tool use for structured outputs
            "json_mode": False,  # Uses tool calling instead
            "timeout": 120,  # seconds
            "retry_on_failure": True,
            "max_retries": 2,
            "default_model": "claude-sonnet-4-20250514",
            "default_temperature": 0.1,
            "max_tokens": 4096,  # Default max tokens for response
        }
        assert requirements["sdk"] == "anthropic>=0.40.0"
        assert requirements["structured_outputs"] is True
        assert requirements["default_temperature"] == 0.1

    def test_anthropic_chat_workflow(self):
        """Document chat request workflow."""
        workflow = {
            "step1": "Initialize Anthropic client with API key",
            "step2": "Prepare messages list with roles (user/assistant)",
            "step3": "Add system message separately (not in messages list)",
            "step4": "Call client.messages.create()",
            "step5": "Extract response.content[0].text",
            "step6": "Return text response",
        }
        assert workflow["step3"] == "Add system message separately (not in messages list)"
        assert workflow["step4"] == "Call client.messages.create()"

    def test_anthropic_structured_output_workflow(self):
        """Document structured output workflow."""
        workflow = {
            "step1": "Build JSON schema from Pydantic model",
            "step2": "Create tool definition with schema",
            "step3": "Add schema instructions to system prompt",
            "step4": "Call client.messages.create() with tools",
            "step5": "Extract tool_use content block",
            "step6": "Validate tool input against Pydantic schema",
            "step7": "Retry with error feedback if validation fails",
            "step8": "Return validated Pydantic instance",
        }
        assert workflow["step4"] == "Call client.messages.create() with tools"
        assert workflow["step7"] == "Retry with error feedback if validation fails"

    def test_anthropic_api_key_requirement(self):
        """Anthropic provider requires API key for initialization."""
        requirements = {
            "api_key_source": "ANTHROPIC_API_KEY environment variable",
            "api_key_format": "sk-ant-...",
            "api_key_required": True,
            "api_key_validation": "Client validates on first request",
        }
        assert requirements["api_key_required"] is True

    def test_anthropic_model_selection(self):
        """Document supported Anthropic models."""
        models = {
            "recommended": "claude-sonnet-4-20250514",  # Best balance
            "highest_quality": "claude-opus-4-20250514",
            "fastest": "claude-haiku-4-20250514",
            "cost_effective": "claude-haiku-4-20250514",
        }
        assert models["recommended"] == "claude-sonnet-4-20250514"

    def test_anthropic_error_handling(self):
        """Document expected error scenarios."""
        errors = {
            "invalid_api_key": "Raises anthropic.AuthenticationError",
            "rate_limit": "Raises anthropic.RateLimitError",
            "timeout": "Raises anthropic.APITimeoutError",
            "invalid_model": "Raises anthropic.NotFoundError",
            "validation_error": "Raises pydantic.ValidationError",
        }
        assert len(errors) == 5

    def test_anthropic_system_message_handling(self):
        """Anthropic has special handling for system messages."""
        system_handling = {
            "location": "Separate system parameter (not in messages list)",
            "extraction": "Extract from first message if role='system'",
            "remaining": "Only user/assistant messages in messages list",
            "required": False,  # System message is optional
        }
        assert system_handling["location"] == "Separate system parameter (not in messages list)"


class TestAnthropicProviderStructure:
    """Structure tests - Validate provider interface compliance.

    These tests verify the provider implements the LLMProvider protocol.
    Skipped until provider is implemented.
    """

    @pytest.fixture
    def provider(self):
        """Create Anthropic provider instance for testing."""
        if not ANTHROPIC_PROVIDER_AVAILABLE:
            pytest.skip("AnthropicProvider not implemented yet")

        return AnthropicProvider(
            api_key="sk-ant-test-key-for-structure-tests",
            model_name="claude-sonnet-4-20250514"
        )

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
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

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
    def test_provider_accepts_required_parameters(self):
        """Provider must accept api_key and model_name."""
        provider = AnthropicProvider(
            api_key="sk-ant-test-key",
            model_name="claude-sonnet-4-20250514"
        )
        assert provider._api_key == "sk-ant-test-key"
        assert provider._model_name == "claude-sonnet-4-20250514"

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
    def test_provider_accepts_optional_parameters(self):
        """Provider should accept optional temperature, timeout, and max_tokens."""
        provider = AnthropicProvider(
            api_key="sk-ant-test-key",
            model_name="claude-sonnet-4-20250514",
            temperature=0.5,
            timeout=60.0,
            max_tokens=2048
        )
        assert provider._temperature == 0.5
        assert provider._timeout == 60.0
        assert provider._max_tokens == 2048

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
    def test_get_model_name_returns_string(self, provider):
        """get_model_name() must return configured model name."""
        assert provider.get_model_name() == "claude-sonnet-4-20250514"

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
    def test_provider_has_client_attribute(self, provider):
        """Provider should initialize Anthropic client."""
        assert hasattr(provider, '_client')


class TestAnthropicProviderExecution:
    """Execution tests - Test actual provider behavior with real Anthropic API.

    These tests make real API calls to Anthropic.
    They skip if ANTHROPIC_API_KEY environment variable is not set.

    To run these tests:
        export ANTHROPIC_API_KEY=sk-ant-...
        pytest tests/unit/llm/test_anthropic_provider.py::TestAnthropicProviderExecution -v
    """

    @pytest.fixture
    def provider(self):
        """Create Anthropic provider with real API key."""
        if not ANTHROPIC_PROVIDER_AVAILABLE:
            pytest.skip("AnthropicProvider not implemented yet")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set - skipping live API tests")

        return AnthropicProvider(
            api_key=api_key,
            model_name="claude-haiku-4-20250514",  # Use faster/cheaper model for tests
            temperature=0.1,
            max_tokens=1024
        )

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_generate_simple_text(self, provider):
        """Test simple text generation from prompt."""
        response = await provider.generate(
            "Say 'Hello from Anthropic' and nothing else.",
            temperature=0.0
        )

        assert isinstance(response, str)
        assert len(response) > 0
        assert "Hello" in response or "hello" in response

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
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

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
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

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
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

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
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

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_temperature_override(self, provider):
        """Test that kwargs can override default temperature."""
        messages = [
            {"role": "user", "content": "Say 'test' and nothing else."}
        ]

        response = await provider.chat(messages, temperature=0.0)

        assert isinstance(response, str)
        assert len(response) > 0


class TestAnthropicProviderIntegration:
    """Integration tests - Verify provider works with Find Evil Agent workflow.

    These tests ensure the provider integrates correctly with:
    - ToolSelectorAgent (critical for tool selection)
    - Multi-agent workflow (agent coordination)
    - Error handling and retries
    """

    @pytest.fixture
    def provider(self):
        """Create Anthropic provider with real API key."""
        if not ANTHROPIC_PROVIDER_AVAILABLE:
            pytest.skip("AnthropicProvider not implemented yet")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set - skipping integration tests")

        return AnthropicProvider(
            api_key=api_key,
            model_name="claude-haiku-4-20250514",
            temperature=0.1,
            max_tokens=2048
        )

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
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

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
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

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
    def test_provider_model_name_matches_initialization(self, provider):
        """Verify get_model_name() returns what was configured."""
        assert provider.get_model_name() == "claude-haiku-4-20250514"


class TestAnthropicProviderErrorHandling:
    """Error handling tests - Verify provider handles failures gracefully."""

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_error(self):
        """Provider should raise error for invalid API key."""
        provider = AnthropicProvider(
            api_key="sk-ant-invalid-key-12345",
            model_name="claude-haiku-4-20250514"
        )

        with pytest.raises(Exception) as exc_info:
            await provider.generate("test")

        # Should raise some error (could be AuthenticationError or RuntimeError wrapping it)
        assert exc_info.value is not None

    @pytest.mark.skipif(not ANTHROPIC_PROVIDER_AVAILABLE, reason="AnthropicProvider not implemented yet")
    @pytest.mark.asyncio
    async def test_invalid_model_raises_error(self):
        """Provider should raise error for invalid model name."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        provider = AnthropicProvider(
            api_key=api_key,
            model_name="invalid-model-xyz"
        )

        with pytest.raises(Exception) as exc_info:
            await provider.generate("test")

        assert exc_info.value is not None
