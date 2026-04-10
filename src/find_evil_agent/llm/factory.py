"""Factory for creating LLM providers based on configuration."""

from find_evil_agent.config.settings import Settings, LLMProviderEnum
from find_evil_agent.llm.protocol import LLMProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    """Create LLM provider instance based on settings.

    This is the central factory for all LLM provider creation.
    Reads the settings.llm_provider enum and instantiates
    the corresponding provider implementation.

    Args:
        settings: Application settings with LLM configuration

    Returns:
        LLMProvider instance ready for use

    Raises:
        ValueError: If provider configuration is invalid or provider unknown
        ImportError: If required provider dependencies are missing

    Example:
        >>> from find_evil_agent.config.settings import get_settings
        >>> settings = get_settings()
        >>> provider = create_llm_provider(settings)
        >>> response = await provider.chat([
        ...     {"role": "user", "content": "Hello"}
        ... ])

    Design Notes:
        - Uses match/case for clean provider selection
        - Validates API keys before instantiation
        - Provider implementations are imported lazily (only when needed)
        - Settings validator already checked API keys, but we double-check here
    """
    match settings.llm_provider:
        case LLMProviderEnum.OLLAMA:
            from find_evil_agent.llm.providers.ollama import OllamaProvider
            return OllamaProvider(
                base_url=settings.ollama_base_url,
                model_name=settings.llm_model_name,
                temperature=settings.llm_temperature
            )

        case LLMProviderEnum.OPENAI:
            if not settings.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY required for openai provider. "
                    "Set environment variable or update .env file."
                )
            from find_evil_agent.llm.providers.openai import OpenAIProvider
            return OpenAIProvider(
                api_key=settings.openai_api_key,
                model_name=settings.llm_model_name,
                temperature=settings.llm_temperature
            )

        case LLMProviderEnum.ANTHROPIC:
            if not settings.anthropic_api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY required for anthropic provider. "
                    "Set environment variable or update .env file."
                )
            from find_evil_agent.llm.providers.anthropic import AnthropicProvider
            return AnthropicProvider(
                api_key=settings.anthropic_api_key,
                model_name=settings.llm_model_name,
                temperature=settings.llm_temperature
            )

        case _:
            raise ValueError(
                f"Unknown LLM provider: {settings.llm_provider}. "
                f"Supported providers: {', '.join([p.value for p in LLMProviderEnum])}"
            )
