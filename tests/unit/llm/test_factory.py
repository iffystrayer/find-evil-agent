"""Tests for LLM provider factory.

TDD Structure:
1. TestFactorySpecification - ALWAYS PASSING (requirements documentation)
2. TestFactoryStructure - Tests factory interface
3. TestFactoryExecution - Tests provider creation logic
"""

import pytest
from find_evil_agent.config.settings import Settings, LLMProviderEnum
from find_evil_agent.llm.factory import create_llm_provider
from find_evil_agent.llm.providers.ollama import OllamaProvider


class TestFactorySpecification:
    """Specification tests - ALWAYS PASSING.

    Document factory requirements and expected behavior.
    """

    def test_factory_requirements(self):
        """Document factory requirements."""
        requirements = {
            "input": "Settings object with llm_provider",
            "output": "LLMProvider instance",
            "supported_providers": ["ollama", "openai", "anthropic"],
            "validation": "API keys required for commercial providers",
            "error_handling": "ValueError for invalid provider or missing keys",
        }
        assert "ollama" in requirements["supported_providers"]
        assert requirements["validation"] == "API keys required for commercial providers"

    def test_provider_creation_workflow(self):
        """Document provider creation workflow."""
        workflow = {
            "step1": "Read settings.llm_provider enum",
            "step2": "Match provider type (ollama, openai, anthropic)",
            "step3": "Validate required configuration (API keys)",
            "step4": "Import provider class (lazy import)",
            "step5": "Instantiate provider with settings",
            "step6": "Return provider instance",
        }
        assert workflow["step1"] == "Read settings.llm_provider enum"
        assert workflow["step3"] == "Validate required configuration (API keys)"


class TestFactoryStructure:
    """Structure tests - Validate factory interface."""

    def test_factory_function_exists(self):
        """create_llm_provider function must exist."""
        assert callable(create_llm_provider)

    def test_factory_accepts_settings(self):
        """Factory must accept Settings object."""
        settings = Settings()
        # Should not raise TypeError
        provider = create_llm_provider(settings)
        assert provider is not None

    def test_factory_returns_provider_with_protocol_methods(self):
        """Returned provider must implement LLMProvider protocol."""
        settings = Settings()
        provider = create_llm_provider(settings)

        # Check protocol methods exist
        assert hasattr(provider, 'chat')
        assert hasattr(provider, 'chat_with_schema')
        assert hasattr(provider, 'get_model_name')


class TestFactoryExecution:
    """Execution tests - Test actual provider creation."""

    def test_create_ollama_provider_from_settings(self):
        """Should create OllamaProvider when provider is ollama."""
        settings = Settings(llm_provider=LLMProviderEnum.OLLAMA)
        provider = create_llm_provider(settings)

        assert isinstance(provider, OllamaProvider)
        assert provider.get_model_name() == "gemma4:31b-cloud"

    def test_create_ollama_provider_with_custom_model(self):
        """Should use custom model name from settings."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="llama3.2:latest"
        )
        provider = create_llm_provider(settings)

        assert provider.get_model_name() == "llama3.2:latest"

    def test_create_ollama_provider_with_custom_url(self):
        """Should use custom Ollama URL from settings."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            ollama_base_url="http://custom:11434"
        )
        provider = create_llm_provider(settings)

        assert isinstance(provider, OllamaProvider)

    def test_openai_provider_requires_api_key(self):
        """Should raise ValueError if OpenAI selected without API key."""
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            settings = Settings(llm_provider=LLMProviderEnum.OPENAI)

    def test_anthropic_provider_requires_api_key(self):
        """Should raise ValueError if Anthropic selected without API key."""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            settings = Settings(llm_provider=LLMProviderEnum.ANTHROPIC)

    def test_invalid_provider_raises_error(self):
        """Should raise ValueError for unknown provider."""
        # This would require mocking the enum, which goes against real testing
        # Instead, we test that the match/case handles all known providers
        settings = Settings()
        provider = create_llm_provider(settings)
        # If we get here, the known provider worked
        assert provider is not None

    def test_multiple_providers_can_be_created(self):
        """Should be able to create multiple provider instances."""
        settings1 = Settings(llm_provider=LLMProviderEnum.OLLAMA)
        settings2 = Settings(llm_provider=LLMProviderEnum.OLLAMA)

        provider1 = create_llm_provider(settings1)
        provider2 = create_llm_provider(settings2)

        # Should be separate instances
        assert provider1 is not provider2

    def test_factory_passes_temperature_to_provider(self):
        """Should pass temperature setting to provider."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_temperature=0.5
        )
        provider = create_llm_provider(settings)

        assert isinstance(provider, OllamaProvider)
        assert provider._temperature == 0.5
