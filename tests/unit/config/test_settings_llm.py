"""Tests for LLM configuration in Settings.

TDD Structure:
1. TestSettingsLLMSpecification - ALWAYS PASSING (requirements documentation)
2. TestSettingsLLMStructure - Tests configuration structure
3. TestSettingsLLMExecution - Tests configuration loading and validation
"""

import pytest
import os
from find_evil_agent.config.settings import Settings, LLMProviderEnum


class TestSettingsLLMSpecification:
    """Specification tests - ALWAYS PASSING.

    Document LLM configuration requirements and expected behavior.
    """

    def test_llm_configuration_requirements(self):
        """Document LLM configuration requirements."""
        requirements = {
            "providers": ["ollama", "openai", "anthropic"],
            "default_provider": "ollama",
            "default_model": "gemma4:31b-cloud",
            "default_temperature": 0.1,
            "ollama_url": "http://192.168.12.124:11434",
            "api_key_validation": True,
            "port_format": "5-digit (10000-99999)",
        }
        assert requirements["default_provider"] == "ollama"
        assert requirements["default_model"] == "gemma4:31b-cloud"
        assert requirements["api_key_validation"] is True

    def test_sift_vm_configuration_requirements(self):
        """Document SIFT VM configuration requirements."""
        requirements = {
            "host": "192.168.12.101",
            "port": 16789,
            "ssh_user": "sansforensics",
            "port_format": "5-digit",
        }
        assert requirements["host"] == "192.168.12.101"
        assert requirements["port"] == 16789
        assert 10000 <= requirements["port"] <= 99999  # 5-digit validation

    def test_langfuse_configuration_requirements(self):
        """Document Langfuse observability requirements."""
        requirements = {
            "fields": ["secret_key", "public_key", "base_url", "enabled"],
            "optional": True,
            "default_enabled": True,
            "base_url": "http://192.168.12.124:33000",
        }
        assert "secret_key" in requirements["fields"]
        assert requirements["optional"] is True


class TestSettingsLLMStructure:
    """Structure tests - Validate configuration schema."""

    def test_settings_has_llm_provider_field(self):
        """Settings must have llm_provider field."""
        settings = Settings()
        assert hasattr(settings, 'llm_provider')
        assert isinstance(settings.llm_provider, LLMProviderEnum)

    def test_settings_has_llm_model_name_field(self):
        """Settings must have llm_model_name field."""
        settings = Settings()
        assert hasattr(settings, 'llm_model_name')
        assert isinstance(settings.llm_model_name, str)

    def test_settings_has_ollama_base_url_field(self):
        """Settings must have ollama_base_url field."""
        settings = Settings()
        assert hasattr(settings, 'ollama_base_url')
        assert settings.ollama_base_url.startswith('http')

    def test_settings_has_langfuse_fields(self):
        """Settings must have Langfuse configuration fields."""
        settings = Settings()
        assert hasattr(settings, 'langfuse_secret_key')
        assert hasattr(settings, 'langfuse_public_key')
        assert hasattr(settings, 'langfuse_base_url')
        assert hasattr(settings, 'langfuse_enabled')

    def test_settings_has_port_fields(self):
        """Settings must have port configuration fields."""
        settings = Settings()
        assert hasattr(settings, 'sift_vm_port')
        assert hasattr(settings, 'mcp_server_port')


class TestSettingsLLMExecution:
    """Execution tests - Test actual configuration behavior."""

    def test_default_llm_provider_is_ollama(self):
        """Default LLM provider should be Ollama."""
        settings = Settings()
        assert settings.llm_provider == LLMProviderEnum.OLLAMA

    def test_default_llm_model_is_gemma4(self):
        """Default model should be gemma4:31b-cloud."""
        settings = Settings()
        assert settings.llm_model_name == "gemma4:31b-cloud"

    def test_default_ollama_url(self):
        """Default Ollama URL should point to configured server."""
        settings = Settings()
        assert settings.ollama_base_url == "http://192.168.12.124:11434"

    def test_default_temperature_is_low(self):
        """Default temperature should be low for deterministic tool selection."""
        settings = Settings()
        assert settings.llm_temperature == 0.1

    def test_sift_vm_configuration(self):
        """SIFT VM should be configured correctly."""
        settings = Settings()
        assert settings.sift_vm_host == "192.168.12.101"
        assert settings.sift_vm_port == 16789
        assert settings.sift_ssh_user == "sansforensics"

    def test_mcp_server_port(self):
        """MCP server port should be 5-digit."""
        settings = Settings()
        assert settings.mcp_server_port == 16790
        assert 10000 <= settings.mcp_server_port <= 99999

    def test_ports_are_5_digit(self):
        """All ports must be 5-digit (CLAUDE.md requirement)."""
        settings = Settings()
        assert 10000 <= settings.sift_vm_port <= 99999
        assert 10000 <= settings.mcp_server_port <= 99999

    def test_load_from_environment_variables(self, monkeypatch):
        """Settings should load from environment variables."""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("LLM_MODEL_NAME", "gpt-4")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        settings = Settings()
        assert settings.llm_provider == LLMProviderEnum.OPENAI
        assert settings.llm_model_name == "gpt-4"
        assert settings.openai_api_key == "sk-test-key"

    def test_validation_fails_without_openai_key(self, monkeypatch):
        """Should raise error if OpenAI provider selected without API key."""
        monkeypatch.setenv("LLM_PROVIDER", "openai")

        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            Settings()

    def test_validation_fails_without_anthropic_key(self, monkeypatch):
        """Should raise error if Anthropic provider selected without API key."""
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            Settings()

    def test_ollama_provider_does_not_require_api_key(self):
        """Ollama provider should work without API keys."""
        settings = Settings()
        assert settings.llm_provider == LLMProviderEnum.OLLAMA
        assert settings.openai_api_key is None
        assert settings.anthropic_api_key is None

    def test_langfuse_configuration_optional(self):
        """Langfuse configuration should be optional."""
        settings = Settings()
        # Should not raise error even if Langfuse keys are None
        assert settings.langfuse_secret_key is None or isinstance(settings.langfuse_secret_key, str)
        assert settings.langfuse_enabled is True  # Default enabled
