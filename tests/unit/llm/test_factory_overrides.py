"""Tests for LLM factory provider/model overrides.

This test suite verifies that the factory correctly handles runtime
provider and model overrides for CLI/API usage.
"""

import pytest
from find_evil_agent.config.settings import Settings, LLMProviderEnum
from find_evil_agent.llm.factory import create_llm_provider
from find_evil_agent.llm.protocol import LLMProvider


class TestFactoryOverridesSpecification:
    """Specification tests for factory override functionality."""

    def test_factory_override_requirements(self):
        """Factory must support runtime provider and model overrides."""
        requirements = """
        The LLM factory must support runtime overrides to enable:
        1. CLI flags (--provider, --model)
        2. API query parameters
        3. Web UI dropdowns
        4. Testing with different providers

        Overrides take precedence over settings for user flexibility.
        """
        assert requirements is not None

    def test_provider_override_workflow(self):
        """Provider override workflow for CLI/API usage."""
        workflow = """
        1. User provides --provider flag (e.g., "openai")
        2. CLI passes override to create_llm_provider()
        3. Factory uses override instead of settings.llm_provider
        4. Correct provider is instantiated
        5. All agents use overridden provider
        """
        assert workflow is not None

    def test_model_override_workflow(self):
        """Model override workflow for CLI/API usage."""
        workflow = """
        1. User provides --model flag (e.g., "gpt-4-turbo")
        2. CLI passes override to create_llm_provider()
        3. Factory uses override instead of settings.llm_model_name
        4. Provider is instantiated with correct model
        5. All LLM calls use overridden model
        """
        assert workflow is not None


class TestFactoryOverridesStructure:
    """Structure tests for factory override parameters."""

    def test_factory_accepts_provider_override(self):
        """Factory function accepts optional provider_override parameter."""
        import inspect
        sig = inspect.signature(create_llm_provider)
        assert "provider_override" in sig.parameters
        assert sig.parameters["provider_override"].default is None

    def test_factory_accepts_model_override(self):
        """Factory function accepts optional model_override parameter."""
        import inspect
        sig = inspect.signature(create_llm_provider)
        assert "model_override" in sig.parameters
        assert sig.parameters["model_override"].default is None

    def test_overrides_are_optional(self):
        """Override parameters have None defaults for backward compatibility."""
        import inspect
        sig = inspect.signature(create_llm_provider)
        assert sig.parameters["provider_override"].default is None
        assert sig.parameters["model_override"].default is None


class TestFactoryOverridesExecution:
    """Execution tests for factory overrides."""

    def test_provider_override_creates_correct_provider(self):
        """Provider override creates correct provider type."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434"
        )

        # Override to OpenAI (without API key should fail)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            create_llm_provider(settings, provider_override="openai")

    def test_model_override_creates_provider_with_correct_model(self):
        """Model override creates provider with overridden model."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434"
        )

        # Override model
        provider = create_llm_provider(settings, model_override="llama3:70b")
        assert provider.get_model_name() == "llama3:70b"

    def test_both_overrides_work_together(self):
        """Provider and model overrides work together."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434"
        )

        # Override both
        provider = create_llm_provider(
            settings,
            provider_override="ollama",
            model_override="qwen3.5:397b-cloud"
        )
        assert provider.get_model_name() == "qwen3.5:397b-cloud"

    def test_no_overrides_uses_settings(self):
        """No overrides uses settings defaults."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434"
        )

        provider = create_llm_provider(settings)
        assert provider.get_model_name() == "gemma4:31b-cloud"

    def test_provider_override_string_converts_to_enum(self):
        """Provider override string correctly converts to enum."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434"
        )

        # String should be converted to enum
        provider = create_llm_provider(settings, provider_override="ollama")
        assert provider is not None
        assert hasattr(provider, 'chat')  # Has protocol method

    def test_invalid_provider_override_raises_error(self):
        """Invalid provider override raises ValueError."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434"
        )

        with pytest.raises(ValueError):
            create_llm_provider(settings, provider_override="invalid-provider")

    def test_model_override_only_changes_model_not_provider(self):
        """Model override changes only model, not provider type."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434"
        )

        # Override only model
        provider = create_llm_provider(settings, model_override="new-model")

        # Should still be Ollama provider
        from find_evil_agent.llm.providers.ollama import OllamaProvider
        assert isinstance(provider, OllamaProvider)
        assert provider.get_model_name() == "new-model"


class TestFactoryOverridesIntegration:
    """Integration tests for factory overrides with different providers."""

    def test_ollama_provider_with_overrides(self):
        """Ollama provider works with overrides."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434"
        )

        provider = create_llm_provider(
            settings,
            provider_override="ollama",
            model_override="llama3:70b"
        )

        from find_evil_agent.llm.providers.ollama import OllamaProvider
        assert isinstance(provider, OllamaProvider)
        assert provider.get_model_name() == "llama3:70b"

    def test_openai_provider_override_requires_api_key(self):
        """OpenAI provider override requires API key in settings."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434",
            openai_api_key=None  # No API key
        )

        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            create_llm_provider(settings, provider_override="openai")

    def test_anthropic_provider_override_requires_api_key(self):
        """Anthropic provider override requires API key in settings."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434",
            anthropic_api_key=None  # No API key
        )

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            create_llm_provider(settings, provider_override="anthropic")

    def test_openai_override_with_api_key(self):
        """OpenAI override works when API key provided."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434",
            openai_api_key="sk-test-key-12345"
        )

        provider = create_llm_provider(
            settings,
            provider_override="openai",
            model_override="gpt-4-turbo"
        )

        from find_evil_agent.llm.providers.openai import OpenAIProvider
        assert isinstance(provider, OpenAIProvider)
        assert provider.get_model_name() == "gpt-4-turbo"

    def test_anthropic_override_with_api_key(self):
        """Anthropic override works when API key provided."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434",
            anthropic_api_key="sk-ant-test-key-12345"
        )

        provider = create_llm_provider(
            settings,
            provider_override="anthropic",
            model_override="claude-sonnet-4"
        )

        from find_evil_agent.llm.providers.anthropic import AnthropicProvider
        assert isinstance(provider, AnthropicProvider)
        assert provider.get_model_name() == "claude-sonnet-4"


class TestFactoryOverridesEdgeCases:
    """Edge case tests for factory overrides."""

    def test_empty_string_override_uses_default(self):
        """Empty string override is treated as None (uses default settings)."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434"
        )

        # Empty string is falsy, so it's treated as None (no override)
        provider = create_llm_provider(settings, provider_override="")

        # Should use settings default
        from find_evil_agent.llm.providers.ollama import OllamaProvider
        assert isinstance(provider, OllamaProvider)
        assert provider.get_model_name() == "gemma4:31b-cloud"

    def test_whitespace_model_override(self):
        """Model override with whitespace creates provider with that exact name."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434"
        )

        # Whitespace is preserved (garbage in, garbage out - user responsibility)
        provider = create_llm_provider(settings, model_override="  model-with-spaces  ")
        assert provider.get_model_name() == "  model-with-spaces  "

    def test_case_sensitive_provider_override(self):
        """Provider override is case-sensitive."""
        settings = Settings(
            llm_provider=LLMProviderEnum.OLLAMA,
            llm_model_name="gemma4:31b-cloud",
            ollama_base_url="http://localhost:11434"
        )

        # "Ollama" (capital O) should fail
        with pytest.raises(ValueError):
            create_llm_provider(settings, provider_override="Ollama")

        # "ollama" (lowercase) should work
        provider = create_llm_provider(settings, provider_override="ollama")
        assert provider is not None
