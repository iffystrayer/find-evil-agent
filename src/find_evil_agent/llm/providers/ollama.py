"""Ollama provider implementation using direct HTTP API.

This provider connects to an Ollama server via HTTP and supports:
- Simple text chat via /api/chat endpoint
- Structured output using JSON mode with Pydantic schema validation
- Automatic retry on validation failures with error feedback
- Connection error handling and logging

Design Notes:
    - Uses httpx for async HTTP (already in project dependencies)
    - Uses orjson for fast JSON parsing (already in dependencies)
    - Uses structlog for structured logging
    - No LangChain wrapper needed (Ollama API is simple REST)

Configuration:
    - Default server: http://192.168.12.124:11434
    - Default model: gemma4:31b-cloud
    - Default temperature: 0.1 (deterministic for tool selection)
    - Default timeout: 120 seconds

Example:
    >>> provider = OllamaProvider(
    ...     base_url="http://192.168.12.124:11434",
    ...     model_name="gemma4:31b-cloud"
    ... )
    >>> response = await provider.chat([
    ...     {"role": "user", "content": "What is DFIR?"}
    ... ])
    >>> print(response)
"""

import httpx
import orjson
from typing import Any
from pydantic import BaseModel, ValidationError
import structlog

logger = structlog.get_logger()


class OllamaProvider:
    """Ollama LLM provider using HTTP API.

    Connects to Ollama server for LLM inference.
    Supports both text chat and structured output via JSON mode.

    Attributes:
        _base_url: Ollama server URL
        _model_name: Model to use for inference
        _temperature: Sampling temperature
        _client: Async HTTP client
    """

    def __init__(
        self,
        base_url: str,
        model_name: str,
        temperature: float = 0.1,
        timeout: float = 120.0
    ):
        """Initialize Ollama provider.

        Args:
            base_url: Ollama server URL (e.g., http://192.168.12.124:11434)
            model_name: Model to use (e.g., gemma4:31b-cloud, llama3.2:latest)
            temperature: Sampling temperature (0.0-1.0), lower is more deterministic
            timeout: Request timeout in seconds

        Example:
            >>> provider = OllamaProvider(
            ...     base_url="http://192.168.12.124:11434",
            ...     model_name="gemma4:31b-cloud",
            ...     temperature=0.1
            ... )
        """
        self._base_url = base_url.rstrip('/')
        self._model_name = model_name
        self._temperature = temperature
        self._client = httpx.AsyncClient(timeout=timeout)

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Send chat request to Ollama API.

        Uses /api/chat endpoint with streaming disabled.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Override temperature or other options

        Returns:
            Text response from LLM

        Raises:
            RuntimeError: If Ollama request fails

        Example:
            >>> response = await provider.chat([
            ...     {"role": "system", "content": "You are a DFIR expert"},
            ...     {"role": "user", "content": "Explain volatility"}
            ... ])
        """
        temperature = kwargs.get('temperature', self._temperature)

        payload = {
            "model": self._model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        try:
            response = await self._client.post(
                f"{self._base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            return data["message"]["content"]

        except httpx.HTTPError as e:
            logger.error("ollama_request_failed", error=str(e), url=self._base_url)
            raise RuntimeError(f"Ollama request failed: {e}")

    async def chat_with_schema(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel],
        **kwargs
    ) -> BaseModel:
        """Chat with structured output using JSON mode.

        Strategy:
        1. Add JSON schema to system message
        2. Request JSON format from Ollama (format: "json")
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
        temperature = kwargs.get('temperature', self._temperature)
        payload = {
            "model": self._model_name,
            "messages": messages_with_schema,
            "stream": False,
            "format": "json",  # Ollama JSON mode
            "options": {
                "temperature": temperature
            }
        }

        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = await self._client.post(
                    f"{self._base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                json_str = data["message"]["content"]

                # Parse and validate
                json_obj = orjson.loads(json_str)
                validated = schema.model_validate(json_obj)

                logger.info(
                    "ollama_structured_output_success",
                    schema=schema.__name__,
                    attempt=attempt + 1
                )
                return validated

            except (orjson.JSONDecodeError, ValidationError) as e:
                logger.warning(
                    "ollama_structured_output_failed",
                    schema=schema.__name__,
                    attempt=attempt + 1,
                    error=str(e)
                )

                if attempt < max_retries - 1:
                    # Add error feedback for retry
                    error_msg = (
                        f"Previous response was invalid: {e}. "
                        f"Please respond with valid JSON matching the schema exactly."
                    )
                    messages_with_schema.append({
                        "role": "user",
                        "content": error_msg
                    })
                    # Update payload for next attempt
                    payload["messages"] = messages_with_schema
                else:
                    raise RuntimeError(
                        f"Failed to get valid structured output from {self._model_name} "
                        f"after {max_retries} attempts: {e}"
                    )

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
        self,
        messages: list[dict[str, str]],
        schema_prompt: str
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
            messages_copy.insert(0, {
                "role": "system",
                "content": schema_prompt
            })

        return messages_copy

    def get_model_name(self) -> str:
        """Return configured model name.

        Returns:
            Model identifier string

        Example:
            >>> provider.get_model_name()
            "gemma4:31b-cloud"
        """
        return self._model_name

    async def close(self):
        """Close HTTP client (cleanup).

        Call this when done with the provider to release resources.

        Example:
            >>> await provider.close()
        """
        await self._client.aclose()
