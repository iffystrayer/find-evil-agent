"""LLM Provider Protocol - Interface for all provider implementations."""

from typing import Any, Protocol

from pydantic import BaseModel


class LLMProvider(Protocol):
    """Protocol for LLM provider implementations.

    All providers must implement these methods to be compatible
    with Find Evil Agent's multi-agent workflow.

    Design Pattern:
        Uses Python Protocol (PEP 544) for structural subtyping.
        Providers don't need to inherit from this class, just implement
        the required methods with matching signatures.

    Methods:
        - generate(): Simple text generation (convenience)
        - chat(): Chat with message history
        - generate_json(): Structured JSON generation (convenience)
        - chat_with_schema(): Chat with structured output
        - get_model_name(): Return model identifier

    Example Implementation:
        >>> class MyProvider:
        ...     async def generate(self, prompt: str, **kwargs) -> str:
        ...         return "response"
        ...
        ...     async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        ...         return "response"
        ...
        ...     async def generate_json(self, prompt: str, schema=None, **kwargs):
        ...         return schema.model_validate({"field": "value"})
        ...
        ...     async def chat_with_schema(self, messages, schema, **kwargs):
        ...         return schema.model_validate({"field": "value"})
        ...
        ...     def get_model_name(self) -> str:
        ...         return "my-model"
    """

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from simple prompt (convenience wrapper).

        Args:
            prompt: Text prompt for generation
            **kwargs: Provider-specific parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response

        Raises:
            RuntimeError: If LLM request fails

        Example:
            >>> response = await provider.generate(
            ...     "List 3 DFIR tools",
            ...     temperature=0.7
            ... )
            >>> print(response)
            "1. Volatility\\n2. Sleuth Kit\\n3. Autopsy"
        """
        ...

    async def generate_json(
        self, prompt: str, schema: type[BaseModel] | None = None, **kwargs
    ) -> dict[str, Any] | BaseModel:
        """Generate structured JSON from prompt (convenience wrapper).

        Args:
            prompt: Text prompt for generation
            schema: Optional Pydantic model for validation
            **kwargs: Provider-specific parameters

        Returns:
            If schema provided: Validated Pydantic model instance
            If no schema: Raw dict from JSON response

        Raises:
            RuntimeError: If request fails or validation fails

        Example:
            >>> from find_evil_agent.agents.schemas import ToolSelection
            >>> selection = await provider.generate_json(
            ...     "Select a tool. Respond in JSON.",
            ...     schema=ToolSelection
            ... )
            >>> print(selection.tool_name)
            "volatility"
        """
        ...

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
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
        self, messages: list[dict[str, str]], schema: type[BaseModel], **kwargs
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
