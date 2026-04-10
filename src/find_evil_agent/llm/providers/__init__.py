"""LLM Provider Implementations.

This package contains concrete implementations of the LLMProvider protocol
for different LLM backends:

- OllamaProvider: Direct HTTP API to Ollama server (development default)
- OpenAIProvider: LangChain wrapper for OpenAI API
- AnthropicProvider: LangChain wrapper for Anthropic Claude API

Each provider implements the LLMProvider protocol with:
- async chat(messages) -> str
- async chat_with_schema(messages, schema) -> BaseModel
- get_model_name() -> str
"""

from .ollama import OllamaProvider

__all__ = ["OllamaProvider"]
