"""Anthropic provider implementation using Anthropic Python SDK.

This provider connects to Anthropic's API and supports:
- Simple text chat via Messages API
- Structured output using tool calling with Pydantic schema validation
- Automatic retry on validation failures with error feedback
- Error handling with Anthropic exceptions

Design Notes:
    - Uses anthropic>=0.40.0 Python SDK
    - Uses Messages API (not legacy Completions)
    - Supports Claude Opus 4, Sonnet 4, Haiku 4 models
    - Uses tool calling for structured outputs (not JSON mode)
    - System messages are separate parameter (extracted from messages)
    - Async client for non-blocking operations

Configuration:
    - API key: ANTHROPIC_API_KEY environment variable
    - Default model: claude-sonnet-4-20250514 (best balance)
    - Default temperature: 0.1 (deterministic for tool selection)
    - Default timeout: 120 seconds
    - Default max_tokens: 4096

Example:
    >>> provider = AnthropicProvider(
    ...     api_key="sk-ant-...",
    ...     model_name="claude-sonnet-4-20250514"
    ... )
    >>> response = await provider.chat([
    ...     {"role": "user", "content": "What is DFIR?"}
    ... ])
    >>> print(response)
"""

from typing import Any

import orjson
import structlog
from anthropic import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncAnthropic,
    AuthenticationError,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError

logger = structlog.get_logger()


class AnthropicProvider:
    """Anthropic LLM provider using Anthropic Python SDK.

    Connects to Anthropic API for LLM inference.
    Supports both text chat and structured output via tool calling.

    Attributes:
        _client: AsyncAnthropic client instance
        _model_name: Model to use for inference
        _temperature: Sampling temperature
        _api_key: Anthropic API key
        _timeout: Request timeout in seconds
        _max_tokens: Maximum tokens in response
    """

    def __init__(
        self,
        api_key: str,
        model_name: str,
        temperature: float = 0.1,
        timeout: float = 120.0,
        max_tokens: int = 4096,
    ):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (sk-ant-...)
            model_name: Model to use (e.g., claude-sonnet-4-20250514)
            temperature: Sampling temperature (0.0-1.0), lower is more deterministic
            timeout: Request timeout in seconds
            max_tokens: Maximum tokens in response

        Example:
            >>> provider = AnthropicProvider(
            ...     api_key="sk-ant-...",
            ...     model_name="claude-sonnet-4-20250514",
            ...     temperature=0.1
            ... )
        """
        self._api_key = api_key
        self._model_name = model_name
        self._temperature = temperature
        self._timeout = timeout
        self._max_tokens = max_tokens
        self._client = AsyncAnthropic(api_key=api_key, timeout=timeout)

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from simple prompt (convenience wrapper).

        This is a simpler interface than chat() for single-shot prompts.
        Internally converts to chat format with user message.

        Args:
            prompt: Text prompt for generation
            **kwargs: Override temperature or other options

        Returns:
            Generated text response

        Raises:
            RuntimeError: If Anthropic request fails

        Example:
            >>> response = await provider.generate(
            ...     "List 3 DFIR tools for memory analysis",
            ...     temperature=0.7
            ... )
            >>> print(response)
            "1. Volatility\\n2. Rekall\\n3. MemProcFS"
        """
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, **kwargs)

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Send chat request to Anthropic API.

        Uses Messages API with configured model.
        Extracts system message if present (Anthropic requires separate parameter).

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Override temperature, max_tokens, or other options

        Returns:
            Text response from LLM

        Raises:
            RuntimeError: If Anthropic request fails

        Example:
            >>> response = await provider.chat([
            ...     {"role": "system", "content": "You are a DFIR expert"},
            ...     {"role": "user", "content": "Explain volatility"}
            ... ])
        """
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)

        # Extract system message if present (Anthropic requires separate parameter)
        system_message, filtered_messages = self._extract_system_message(messages)

        try:
            response = await self._client.messages.create(
                model=self._model_name,
                messages=filtered_messages,
                system=system_message,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract text from first content block
            return response.content[0].text

        except (
            APIError,
            APITimeoutError,
            RateLimitError,
            AuthenticationError,
            APIConnectionError,
        ) as e:
            logger.error("anthropic_request_failed", error=str(e), model=self._model_name)
            raise RuntimeError(f"Anthropic request failed: {e}")

    async def generate_json(
        self, prompt: str, schema: type[BaseModel] | None = None, **kwargs
    ) -> dict[str, Any] | BaseModel:
        """Generate structured JSON from prompt (convenience wrapper).

        Simpler interface than chat_with_schema() for single-shot JSON generation.

        Args:
            prompt: Text prompt for generation
            schema: Optional Pydantic model for validation
            **kwargs: Override temperature or other options

        Returns:
            If schema provided: Validated Pydantic model instance
            If no schema: Raw dict from JSON response

        Raises:
            RuntimeError: If request fails or validation fails

        Example:
            >>> from find_evil_agent.agents.schemas import ToolSelection
            >>> selection = await provider.generate_json(
            ...     "Select a tool for memory analysis. Respond in JSON.",
            ...     schema=ToolSelection
            ... )
            >>> print(selection.tool_name)
            "volatility"
        """
        messages = [{"role": "user", "content": prompt}]

        if schema:
            return await self.chat_with_schema(messages, schema, **kwargs)
        else:
            # Return raw JSON dict - ask for JSON in prompt
            enhanced_prompt = (
                f"{prompt}\n\n"
                "Respond ONLY with a valid JSON object. "
                "Do not include markdown formatting or explanatory text."
            )
            messages = [{"role": "user", "content": enhanced_prompt}]

            response_text = await self.chat(messages, **kwargs)

            try:
                return orjson.loads(response_text)
            except orjson.JSONDecodeError as e:
                logger.error("anthropic_json_parse_failed", error=str(e), response=response_text)
                raise RuntimeError(f"Failed to parse JSON from Anthropic response: {e}")

    async def chat_with_schema(
        self, messages: list[dict[str, str]], schema: type[BaseModel], **kwargs
    ) -> BaseModel:
        """Chat with structured output using tool calling.

        Strategy:
        1. Build tool definition from Pydantic schema
        2. Add schema instructions to system prompt
        3. Force tool use with tool_choice
        4. Parse and validate tool input against schema
        5. Retry once if validation fails (with error feedback)

        Args:
            messages: Chat messages
            schema: Pydantic model class for response structure
            **kwargs: Override temperature or other options

        Returns:
            Validated Pydantic model instance

        Raises:
            RuntimeError: If request fails or validation fails after retries

        Example:
            >>> from find_evil_agent.agents.schemas import ToolSelection
            >>> selection = await provider.chat_with_schema(
            ...     messages=[
            ...         {"role": "system", "content": "Select a SIFT tool"},
            ...         {"role": "user", "content": "Analyze memory dump"}
            ...     ],
            ...     schema=ToolSelection
            ... )
            >>> print(selection.tool_name)
            "volatility"
            >>> print(selection.confidence)
            0.85
        """
        temperature = kwargs.get("temperature", self._temperature)
        max_tokens = kwargs.get("max_tokens", self._max_tokens)

        # Build tool definition from schema
        tool_def = self._build_tool_definition(schema)

        # Add schema instructions to system message
        schema_instructions = self._build_schema_instructions(schema)
        messages_with_instructions = self._inject_schema_instructions(messages, schema_instructions)

        # Extract system message
        system_message, filtered_messages = self._extract_system_message(messages_with_instructions)

        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = await self._client.messages.create(
                    model=self._model_name,
                    messages=filtered_messages,
                    system=system_message,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=[tool_def],
                    tool_choice={"type": "tool", "name": tool_def["name"]},
                )

                # Find tool_use content block
                tool_use = None
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_use = content_block
                        break

                if not tool_use:
                    raise RuntimeError("No tool_use block found in Anthropic response")

                # Validate tool input against schema
                validated = schema.model_validate(tool_use.input)

                logger.info(
                    "anthropic_structured_output_success",
                    schema=schema.__name__,
                    attempt=attempt + 1,
                )
                return validated

            except ValidationError as e:
                logger.warning(
                    "anthropic_structured_output_failed",
                    schema=schema.__name__,
                    attempt=attempt + 1,
                    error=str(e),
                )

                if attempt < max_retries - 1:
                    # Add error feedback for retry
                    error_msg = (
                        f"Previous response was invalid: {e}. "
                        f"Please provide a response matching the exact schema structure."
                    )
                    filtered_messages.append({"role": "user", "content": error_msg})
                else:
                    raise RuntimeError(
                        f"Failed to get valid structured output from {self._model_name} "
                        f"after {max_retries} attempts: {e}"
                    )

            except (
                APIError,
                APITimeoutError,
                RateLimitError,
                AuthenticationError,
                APIConnectionError,
            ) as e:
                logger.error("anthropic_structured_request_failed", error=str(e))
                raise RuntimeError(f"Anthropic structured request failed: {e}")

    def _extract_system_message(
        self, messages: list[dict[str, str]]
    ) -> tuple[str | None, list[dict[str, str]]]:
        """Extract system message from messages list.

        Anthropic requires system message as separate parameter.
        If first message has role='system', extract it and return separately.

        Args:
            messages: List of messages

        Returns:
            Tuple of (system_message, filtered_messages)
            system_message is None if no system message present

        Example:
            >>> messages = [
            ...     {"role": "system", "content": "You are helpful"},
            ...     {"role": "user", "content": "Hi"}
            ... ]
            >>> system, filtered = provider._extract_system_message(messages)
            >>> system
            "You are helpful"
            >>> len(filtered)
            1
        """
        if messages and messages[0].get("role") == "system":
            system_message = messages[0]["content"]
            filtered_messages = messages[1:]
            return system_message, filtered_messages
        else:
            return None, messages

    def _build_tool_definition(self, schema: type[BaseModel]) -> dict:
        """Build Anthropic tool definition from Pydantic schema.

        Args:
            schema: Pydantic model class

        Returns:
            Tool definition dict for Anthropic API

        Example:
            >>> from find_evil_agent.agents.schemas import ToolSelection
            >>> tool_def = provider._build_tool_definition(ToolSelection)
            >>> tool_def["name"]
            "provide_structured_response"
        """
        schema_json = schema.model_json_schema()

        return {
            "name": "provide_structured_response",
            "description": f"Provide a structured response matching the {schema.__name__} schema",
            "input_schema": schema_json,
        }

    def _build_schema_instructions(self, schema: type[BaseModel]) -> str:
        """Build schema instructions for system prompt.

        Args:
            schema: Pydantic model class

        Returns:
            Instructions text

        Example:
            >>> from find_evil_agent.agents.schemas import ToolSelection
            >>> instructions = provider._build_schema_instructions(ToolSelection)
            >>> "ToolSelection" in instructions
            True
        """
        return f"""You must provide your response using the structured output tool.
The response must match the {schema.__name__} schema exactly.
Ensure all required fields are present with appropriate values."""

    def _inject_schema_instructions(
        self, messages: list[dict[str, str]], instructions: str
    ) -> list[dict[str, str]]:
        """Inject schema instructions into system message.

        Args:
            messages: Original messages
            instructions: Instructions to inject

        Returns:
            Messages with instructions injected

        Example:
            >>> messages = [{"role": "user", "content": "Help"}]
            >>> result = provider._inject_schema_instructions(messages, "Use tool")
            >>> result[0]["role"]
            "system"
        """
        messages_copy = messages.copy()

        if messages_copy and messages_copy[0].get("role") == "system":
            # Append to existing system message
            messages_copy[0]["content"] += f"\n\n{instructions}"
        else:
            # Prepend new system message
            messages_copy.insert(0, {"role": "system", "content": instructions})

        return messages_copy

    def get_model_name(self) -> str:
        """Return configured model name.

        Returns:
            Model identifier string

        Example:
            >>> provider.get_model_name()
            "claude-sonnet-4-20250514"
        """
        return self._model_name

    async def close(self):
        """Close HTTP client (cleanup).

        Call this when done with the provider to release resources.

        Example:
            >>> await provider.close()
        """
        await self._client.close()
