"""OpenAI provider implementation using OpenAI Python SDK.

This provider connects to OpenAI's API and supports:
- Simple text chat via Chat Completions API
- Structured output using JSON mode with Pydantic schema validation
- Automatic retry on validation failures with error feedback
- Error handling with OpenAI exceptions

Design Notes:
    - Uses openai>=1.0.0 Python SDK
    - Uses chat completions API (not legacy completions)
    - Supports GPT-4, GPT-4-turbo, GPT-3.5-turbo models
    - Uses JSON mode for structured outputs (response_format)
    - Async client for non-blocking operations

Configuration:
    - API key: OPENAI_API_KEY environment variable
    - Default model: gpt-4-turbo (best balance speed/quality)
    - Default temperature: 0.1 (deterministic for tool selection)
    - Default timeout: 120 seconds

Example:
    >>> provider = OpenAIProvider(
    ...     api_key="sk-...",
    ...     model_name="gpt-4-turbo"
    ... )
    >>> response = await provider.chat([
    ...     {"role": "user", "content": "What is DFIR?"}
    ... ])
    >>> print(response)
"""

from typing import Any

import orjson
import structlog
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError

logger = structlog.get_logger()


class OpenAIProvider:
    """OpenAI LLM provider using OpenAI Python SDK.

    Connects to OpenAI API for LLM inference.
    Supports both text chat and structured output via JSON mode.

    Attributes:
        _client: AsyncOpenAI client instance
        _model_name: Model to use for inference
        _temperature: Sampling temperature
        _api_key: OpenAI API key
        _timeout: Request timeout in seconds
    """

    def __init__(
        self, api_key: str, model_name: str, temperature: float = 0.1, timeout: float = 120.0
    ):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (sk-...)
            model_name: Model to use (e.g., gpt-4-turbo, gpt-4, gpt-3.5-turbo)
            temperature: Sampling temperature (0.0-1.0), lower is more deterministic
            timeout: Request timeout in seconds

        Example:
            >>> provider = OpenAIProvider(
            ...     api_key="sk-...",
            ...     model_name="gpt-4-turbo",
            ...     temperature=0.1
            ... )
        """
        self._api_key = api_key
        self._model_name = model_name
        self._temperature = temperature
        self._timeout = timeout
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout)

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
            RuntimeError: If OpenAI request fails

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
        """Send chat request to OpenAI API.

        Uses Chat Completions API with configured model.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Override temperature or other options

        Returns:
            Text response from LLM

        Raises:
            RuntimeError: If OpenAI request fails

        Example:
            >>> response = await provider.chat([
            ...     {"role": "system", "content": "You are a DFIR expert"},
            ...     {"role": "user", "content": "Explain volatility"}
            ... ])
        """
        temperature = kwargs.get("temperature", self._temperature)

        try:
            response = await self._client.chat.completions.create(
                model=self._model_name, messages=messages, temperature=temperature
            )

            return response.choices[0].message.content

        except (
            APIError,
            APITimeoutError,
            RateLimitError,
            AuthenticationError,
            APIConnectionError,
        ) as e:
            logger.error("openai_request_failed", error=str(e), model=self._model_name)
            raise RuntimeError(f"OpenAI request failed: {e}")

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
            # Return raw JSON dict
            temperature = kwargs.get("temperature", self._temperature)

            try:
                response = await self._client.chat.completions.create(
                    model=self._model_name,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )

                json_str = response.choices[0].message.content
                return orjson.loads(json_str)

            except (
                APIError,
                APITimeoutError,
                RateLimitError,
                AuthenticationError,
                APIConnectionError,
            ) as e:
                logger.error("openai_json_request_failed", error=str(e))
                raise RuntimeError(f"OpenAI JSON request failed: {e}")

    async def chat_with_schema(
        self, messages: list[dict[str, str]], schema: type[BaseModel], **kwargs
    ) -> BaseModel:
        """Chat with structured output using JSON mode.

        Strategy:
        1. Add JSON schema to system message
        2. Request JSON format from OpenAI (response_format: json_object)
        3. Parse and validate against Pydantic schema
        4. Retry once if validation fails (with error feedback)

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
        # Inject schema into system message
        schema_prompt = self._build_schema_prompt(schema)
        messages_with_schema = self._inject_schema_prompt(messages, schema_prompt)

        # Request JSON output
        temperature = kwargs.get("temperature", self._temperature)

        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self._model_name,
                    messages=messages_with_schema,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )

                json_str = response.choices[0].message.content

                # Parse and validate
                json_obj = orjson.loads(json_str)
                validated = schema.model_validate(json_obj)

                logger.info(
                    "openai_structured_output_success", schema=schema.__name__, attempt=attempt + 1
                )
                return validated

            except (orjson.JSONDecodeError, ValidationError) as e:
                logger.warning(
                    "openai_structured_output_failed",
                    schema=schema.__name__,
                    attempt=attempt + 1,
                    error=str(e),
                )

                if attempt < max_retries - 1:
                    # Add error feedback for retry
                    error_msg = (
                        f"Previous response was invalid: {e}. "
                        f"Please respond with valid JSON matching the schema exactly."
                    )
                    messages_with_schema.append({"role": "user", "content": error_msg})
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
                logger.error("openai_structured_request_failed", error=str(e))
                raise RuntimeError(f"OpenAI structured request failed: {e}")

    def _build_schema_prompt(self, schema: type[BaseModel]) -> str:
        """Build JSON schema prompt from Pydantic model.

        Args:
            schema: Pydantic model class

        Returns:
            Formatted prompt with JSON schema

        Example:
            >>> from find_evil_agent.agents.schemas import ToolSelection
            >>> prompt = provider._build_schema_prompt(ToolSelection)
            >>> print(prompt)
            You must respond with valid JSON matching this schema:
            {
              "properties": {
                "tool_name": {"type": "string"},
                ...
              }
            }
            ...
        """
        schema_json = schema.model_json_schema()
        return f"""You must respond with valid JSON matching this schema:

{orjson.dumps(schema_json, option=orjson.OPT_INDENT_2).decode()}

IMPORTANT:
- Respond ONLY with the JSON object
- Do NOT include markdown code fences (```json)
- Do NOT include any explanatory text
- Ensure all required fields are present
- Follow the exact field names and types"""

    def _inject_schema_prompt(
        self, messages: list[dict[str, str]], schema_prompt: str
    ) -> list[dict[str, str]]:
        """Inject schema into system message or prepend.

        Args:
            messages: Original messages
            schema_prompt: Schema prompt to inject

        Returns:
            Messages with schema injected

        Example:
            >>> messages = [{"role": "user", "content": "Help"}]
            >>> result = provider._inject_schema_prompt(messages, "Schema: ...")
            >>> len(result)
            2  # System message prepended
        """
        messages_copy = messages.copy()

        if messages_copy and messages_copy[0]["role"] == "system":
            # Append to existing system message
            messages_copy[0]["content"] += f"\n\n{schema_prompt}"
        else:
            # Prepend new system message
            messages_copy.insert(0, {"role": "system", "content": schema_prompt})

        return messages_copy

    def get_model_name(self) -> str:
        """Return configured model name.

        Returns:
            Model identifier string

        Example:
            >>> provider.get_model_name()
            "gpt-4-turbo"
        """
        return self._model_name

    async def close(self):
        """Close HTTP client (cleanup).

        Call this when done with the provider to release resources.

        Example:
            >>> await provider.close()
        """
        await self._client.close()
