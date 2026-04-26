"""Integration tests for Ollama provider with live server.

These tests require Ollama running at 192.168.12.124:11434.
Run with: pytest tests/integration/llm/test_ollama_live.py -v

Skip in CI if Ollama unavailable:
pytest tests/integration/llm/test_ollama_live.py -v -m "not integration"
"""

import httpx
import pytest
from pydantic import BaseModel, Field

from find_evil_agent.agents.schemas import ToolSelection
from find_evil_agent.llm.providers.ollama import OllamaProvider


# Check if Ollama is available
def check_ollama_available():
    """Check if Ollama server is reachable."""
    try:
        response = httpx.get("http://192.168.12.124:11434/api/tags", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


OLLAMA_AVAILABLE = check_ollama_available()
SKIP_REASON = "Ollama not available at 192.168.12.124:11434"


@pytest.mark.integration
@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason=SKIP_REASON)
class TestOllamaLiveConnection:
    """Test basic connectivity to Ollama server."""

    @pytest.mark.asyncio
    async def test_ollama_server_reachable(self):
        """Ollama server should be reachable."""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://192.168.12.124:11434/api/tags")
            assert response.status_code == 200
            data = response.json()
            assert "models" in data

    @pytest.mark.asyncio
    async def test_gemma4_model_available(self):
        """gemma4:31b-cloud model should be available."""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://192.168.12.124:11434/api/tags")
            data = response.json()
            models = [m["name"] for m in data["models"]]
            assert "gemma4:31b-cloud" in models


@pytest.mark.integration
@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason=SKIP_REASON)
class TestOllamaLiveChat:
    """Test chat functionality with live Ollama."""

    @pytest.mark.asyncio
    async def test_simple_chat_with_llama3(self):
        """Test simple chat with llama3.2 (fastest model)."""
        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434", model_name="llama3.2:latest", temperature=0.1
        )

        response = await provider.chat(
            [{"role": "user", "content": "Say 'hello' and nothing else."}]
        )

        assert isinstance(response, str)
        assert len(response) > 0
        assert "hello" in response.lower()

        await provider.close()

    @pytest.mark.asyncio
    async def test_simple_chat_with_gemma4(self):
        """Test simple chat with gemma4:31b-cloud."""
        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434", model_name="gemma4:31b-cloud", temperature=0.1
        )

        response = await provider.chat(
            [{"role": "user", "content": "What is DFIR? Answer in one sentence."}]
        )

        assert isinstance(response, str)
        assert len(response) > 0
        assert "forensic" in response.lower() or "incident" in response.lower()

        await provider.close()

    @pytest.mark.asyncio
    async def test_chat_with_system_message(self):
        """Test chat with system message."""
        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434", model_name="llama3.2:latest", temperature=0.1
        )

        response = await provider.chat(
            [
                {"role": "system", "content": "You are a helpful assistant. Be concise."},
                {"role": "user", "content": "What is 2+2?"},
            ]
        )

        assert isinstance(response, str)
        assert "4" in response

        await provider.close()

    @pytest.mark.asyncio
    async def test_chat_with_custom_temperature(self):
        """Test chat with custom temperature override."""
        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434", model_name="llama3.2:latest", temperature=0.1
        )

        # Override temperature in kwargs
        response = await provider.chat([{"role": "user", "content": "Say 'test'"}], temperature=0.9)

        assert isinstance(response, str)
        assert len(response) > 0

        await provider.close()


@pytest.mark.integration
@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason=SKIP_REASON)
class TestOllamaLiveStructuredOutput:
    """Test structured output (JSON mode) with live Ollama."""

    @pytest.mark.asyncio
    async def test_structured_output_simple_schema(self):
        """Test structured output with simple schema."""
        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434", model_name="llama3.2:latest", temperature=0.1
        )

        class SimpleSchema(BaseModel):
            answer: str = Field(description="The answer")
            confidence: float = Field(description="Confidence 0-1", ge=0.0, le=1.0)

        result = await provider.chat_with_schema(
            messages=[{"role": "user", "content": "What is 2+2? Be confident."}],
            schema=SimpleSchema,
        )

        assert isinstance(result, SimpleSchema)
        assert isinstance(result.answer, str)
        assert "4" in result.answer
        assert 0.0 <= result.confidence <= 1.0

        await provider.close()

    @pytest.mark.asyncio
    async def test_structured_output_tool_selection(self):
        """Test structured output with ToolSelection schema (real use case)."""
        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434", model_name="gemma4:31b-cloud", temperature=0.1
        )

        selection = await provider.chat_with_schema(
            messages=[
                {
                    "role": "system",
                    "content": "You are a DFIR expert selecting SIFT tools for forensic analysis.",
                },
                {
                    "role": "user",
                    "content": "I need to analyze a memory dump to find running processes. Which tool should I use?",
                },
            ],
            schema=ToolSelection,
        )

        assert isinstance(selection, ToolSelection)
        assert selection.tool_name == "volatility"  # Should select volatility
        assert 0.0 <= selection.confidence <= 1.0
        assert selection.confidence >= 0.7  # Should meet threshold
        assert len(selection.reason) > 0
        assert isinstance(selection.inputs, dict)
        assert isinstance(selection.alternatives, list)

        await provider.close()

    @pytest.mark.asyncio
    async def test_structured_output_with_nested_fields(self):
        """Test structured output with nested schema."""
        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434", model_name="llama3.2:latest", temperature=0.1
        )

        class Address(BaseModel):
            street: str
            city: str

        class Person(BaseModel):
            name: str
            age: int
            address: Address

        result = await provider.chat_with_schema(
            messages=[
                {
                    "role": "user",
                    "content": "Create a person named John, age 30, living at 123 Main St, Springfield",
                }
            ],
            schema=Person,
        )

        assert isinstance(result, Person)
        assert result.name == "John"
        assert result.age == 30
        assert isinstance(result.address, Address)
        assert "Main" in result.address.street
        assert result.address.city == "Springfield"

        await provider.close()

    @pytest.mark.asyncio
    async def test_structured_output_validation_enforced(self):
        """Test that schema validation is enforced."""
        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434", model_name="llama3.2:latest", temperature=0.1
        )

        class StrictSchema(BaseModel):
            count: int = Field(description="Must be positive integer", gt=0)
            percentage: float = Field(description="Must be 0-100", ge=0.0, le=100.0)

        result = await provider.chat_with_schema(
            messages=[{"role": "user", "content": "Give me count=5 and percentage=75"}],
            schema=StrictSchema,
        )

        assert isinstance(result, StrictSchema)
        assert result.count > 0
        assert 0.0 <= result.percentage <= 100.0

        await provider.close()


@pytest.mark.integration
@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason=SKIP_REASON)
class TestOllamaLiveErrorHandling:
    """Test error handling with live Ollama."""

    @pytest.mark.asyncio
    async def test_connection_error_for_invalid_url(self):
        """Should raise RuntimeError for unreachable server."""
        provider = OllamaProvider(
            base_url="http://invalid-server:11434", model_name="test-model", timeout=2.0
        )

        with pytest.raises(RuntimeError, match="Ollama request failed"):
            await provider.chat([{"role": "user", "content": "Hello"}])

        await provider.close()

    @pytest.mark.asyncio
    async def test_invalid_model_handled_gracefully(self):
        """Should handle invalid model name appropriately."""
        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434", model_name="nonexistent-model", timeout=10.0
        )

        # Ollama returns 404 for unknown models
        with pytest.raises(RuntimeError):
            await provider.chat([{"role": "user", "content": "Hello"}])

        await provider.close()


@pytest.mark.integration
@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason=SKIP_REASON)
class TestOllamaLivePerformance:
    """Test performance characteristics with live Ollama."""

    @pytest.mark.asyncio
    async def test_chat_completes_within_timeout(self):
        """Chat request should complete within reasonable time."""
        import time

        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434",
            model_name="llama3.2:latest",
            temperature=0.1,
            timeout=30.0,
        )

        start = time.time()
        response = await provider.chat([{"role": "user", "content": "Say 'done' briefly"}])
        duration = time.time() - start

        assert isinstance(response, str)
        assert duration < 10.0  # Should complete in under 10 seconds

        await provider.close()

    @pytest.mark.asyncio
    async def test_structured_output_completes_within_timeout(self):
        """Structured output should complete within reasonable time."""
        import time

        provider = OllamaProvider(
            base_url="http://192.168.12.124:11434",
            model_name="gemma4:31b-cloud",
            temperature=0.1,
            timeout=60.0,
        )

        class SimpleSchema(BaseModel):
            answer: str

        start = time.time()
        result = await provider.chat_with_schema(
            messages=[{"role": "user", "content": "What is 1+1?"}], schema=SimpleSchema
        )
        duration = time.time() - start

        assert isinstance(result, SimpleSchema)
        assert duration < 30.0  # Should complete in under 30 seconds

        await provider.close()
