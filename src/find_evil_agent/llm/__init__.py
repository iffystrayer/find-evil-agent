"""LLM Provider Abstraction.

This module provides a model-agnostic interface for LLM providers,
allowing Find Evil Agent to work with Ollama, OpenAI, Anthropic, and others.

Example:
    >>> from find_evil_agent.llm import create_llm_provider
    >>> from find_evil_agent.config.settings import get_settings
    >>>
    >>> settings = get_settings()
    >>> provider = create_llm_provider(settings)
    >>>
    >>> # Simple chat
    >>> response = await provider.chat([
    ...     {"role": "user", "content": "Hello"}
    ... ])
    >>>
    >>> # Structured output
    >>> from find_evil_agent.agents.schemas import ToolSelection
    >>> selection = await provider.chat_with_schema(
    ...     messages=[...],
    ...     schema=ToolSelection
    ... )
"""

from .protocol import LLMProvider
from .factory import create_llm_provider

__all__ = ["LLMProvider", "create_llm_provider"]
