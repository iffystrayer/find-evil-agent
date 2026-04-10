"""LLM Provider Protocol - Interface for all provider implementations."""

from typing import Protocol, Any
from pydantic import BaseModel


class LLMProvider(Protocol):
    """Protocol for LLM provider implementations.

    All providers must implement these methods to be compatible
    with Find Evil Agent's multi-agent workflow.

    Design Pattern:
        Uses Python Protocol (PEP 544) for structural subtyping.
        Providers don't need to inherit from this class, just implement
        the required methods with matching signatures.

    Example Implementation:
        >>> class MyProvider:
        ...     async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        ...         # Send to LLM and return response
        ...         return "response"
        ...
        ...     async def chat_with_schema(self, messages, schema, **kwargs):
        ...         # Send to LLM with structured output constraint
        ...         return schema.model_validate({"field": "value"})
        ...
        ...     def get_model_name(self) -> str:
        ...         return "my-model"
    """

    async def chat(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> str:
        """Send chat messages and get text response.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                     Example: [
                         {"role": "system", "content": "You are a DFIR expert"},
                         {"role": "user", "content": "Analyze this memory dump"}
                     ]
            **kwargs: Provider-specific parameters:
                     - temperature: float (0.0-1.0)
                     - max_tokens: int
                     - top_p: float
                     - etc.

        Returns:
            Text response from LLM

        Raises:
            RuntimeError: If LLM request fails

        Example:
            >>> provider = OllamaProvider(...)
            >>> response = await provider.chat([
            ...     {"role": "user", "content": "Hello"}
            ... ], temperature=0.7)
            >>> print(response)
            "Hello! How can I help you today?"
        """
        ...

    async def chat_with_schema(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel],
        **kwargs
    ) -> BaseModel:
        """Chat with structured output validated against Pydantic schema.

        This is the critical method for ToolSelectorAgent, which needs
        structured ToolSelection responses with confidence scores.

        Args:
            messages: Chat messages (same format as chat())
            schema: Pydantic model class for response structure
                   Example: ToolSelection, Finding, ExecutionResult
            **kwargs: Provider-specific parameters

        Returns:
            Validated Pydantic model instance

        Raises:
            RuntimeError: If LLM request fails or response doesn't match schema

        Example:
            >>> from find_evil_agent.agents.schemas import ToolSelection
            >>> provider = OllamaProvider(...)
            >>> selection = await provider.chat_with_schema(
            ...     messages=[
            ...         {"role": "system", "content": "Select a SIFT tool"},
            ...         {"role": "user", "content": "I need to analyze memory"}
            ...     ],
            ...     schema=ToolSelection
            ... )
            >>> print(selection.tool_name)
            "volatility"
            >>> print(selection.confidence)
            0.85
        """
        ...

    def get_model_name(self) -> str:
        """Return configured model name.

        Returns:
            Model identifier string (e.g., "gemma4:31b-cloud", "gpt-4", "claude-3-opus")

        Example:
            >>> provider = OllamaProvider(model_name="llama3.2:latest", ...)
            >>> provider.get_model_name()
            "llama3.2:latest"
        """
        ...
