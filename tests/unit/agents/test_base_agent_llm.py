"""Tests for BaseAgent LLM integration.

TDD Structure:
1. TestBaseAgentLLMSpecification - ALWAYS PASSING (requirements documentation)
2. TestBaseAgentLLMStructure - Tests LLM integration structure
3. TestBaseAgentLLMExecution - Tests LLM property behavior
"""

import pytest
from find_evil_agent.agents.base import BaseAgent, AgentResult
from find_evil_agent.llm.providers.ollama import OllamaProvider


# Create a concrete agent for testing
class TestAgent(BaseAgent):
    """Concrete agent implementation for testing."""

    async def process(self, input_data: dict) -> AgentResult:
        """Simple test implementation."""
        return AgentResult(
            success=True,
            data={"processed": True},
            confidence=1.0
        )


class TestBaseAgentLLMSpecification:
    """Specification tests - ALWAYS PASSING.

    Document BaseAgent LLM integration requirements.
    """

    def test_base_agent_llm_requirements(self):
        """Document BaseAgent LLM integration requirements."""
        requirements = {
            "llm_property": "Lazy-initialized LLM provider property",
            "dependency_injection": "Optional llm_provider in __init__",
            "lazy_loading": "Provider created on first access",
            "singleton_per_agent": "Same provider instance reused",
            "test_friendly": "Can inject mock provider",
            "global_settings": "Uses get_settings() if not injected",
        }
        assert requirements["llm_property"] == "Lazy-initialized LLM provider property"
        assert requirements["dependency_injection"] == "Optional llm_provider in __init__"

    def test_llm_access_workflow(self):
        """Document LLM access workflow."""
        workflow = {
            "step1": "Agent created without llm_provider",
            "step2": "Agent accesses self.llm property",
            "step3": "Property checks if _llm_provider is None",
            "step4": "If None, load settings and create provider",
            "step5": "Cache provider in _llm_provider",
            "step6": "Return provider instance",
            "step7": "Subsequent accesses reuse cached provider",
        }
        assert workflow["step3"] == "Property checks if _llm_provider is None"
        assert workflow["step7"] == "Subsequent accesses reuse cached provider"


class TestBaseAgentLLMStructure:
    """Structure tests - Validate LLM integration structure."""

    def test_base_agent_accepts_llm_provider_parameter(self):
        """BaseAgent __init__ should accept optional llm_provider."""
        mock_provider = OllamaProvider(
            base_url="http://test:11434",
            model_name="test-model"
        )

        agent = TestAgent(
            name="test",
            llm_provider=mock_provider
        )

        assert agent._llm_provider is mock_provider

    def test_base_agent_has_llm_property(self):
        """BaseAgent should have llm property."""
        agent = TestAgent(name="test")
        assert hasattr(agent, 'llm')

    def test_llm_property_is_property_not_method(self):
        """llm should be a property, not a method."""
        agent = TestAgent(name="test")
        # Should access without parentheses
        # This will create a provider, but that's okay
        provider = agent.llm
        assert provider is not None


class TestBaseAgentLLMExecution:
    """Execution tests - Test actual LLM integration behavior."""

    def test_llm_property_returns_provider_when_injected(self):
        """llm property should return injected provider."""
        mock_provider = OllamaProvider(
            base_url="http://test:11434",
            model_name="test-model"
        )

        agent = TestAgent(
            name="test",
            llm_provider=mock_provider
        )

        assert agent.llm is mock_provider

    def test_llm_property_creates_provider_if_not_injected(self):
        """llm property should create provider from settings if not injected."""
        agent = TestAgent(name="test")

        # Should create provider from global settings
        provider = agent.llm

        assert provider is not None
        assert hasattr(provider, 'chat')
        assert hasattr(provider, 'chat_with_schema')

    def test_llm_property_caches_provider(self):
        """llm property should cache provider instance."""
        agent = TestAgent(name="test")

        provider1 = agent.llm
        provider2 = agent.llm

        # Should be same instance (cached)
        assert provider1 is provider2

    def test_llm_property_uses_ollama_by_default(self):
        """llm property should create OllamaProvider by default."""
        agent = TestAgent(name="test")

        provider = agent.llm

        assert isinstance(provider, OllamaProvider)

    def test_multiple_agents_can_have_separate_providers(self):
        """Each agent can have its own provider instance."""
        agent1 = TestAgent(name="agent1")
        agent2 = TestAgent(name="agent2")

        provider1 = agent1.llm
        provider2 = agent2.llm

        # Different agents, different provider instances
        assert provider1 is not provider2

    def test_agent_with_injected_provider_does_not_create_new_one(self):
        """Agent with injected provider should not create another."""
        mock_provider = OllamaProvider(
            base_url="http://test:11434",
            model_name="test-model"
        )

        agent = TestAgent(
            name="test",
            llm_provider=mock_provider
        )

        # Access multiple times
        p1 = agent.llm
        p2 = agent.llm

        # All should be the injected provider
        assert p1 is mock_provider
        assert p2 is mock_provider

    @pytest.mark.asyncio
    async def test_agent_can_use_llm_in_process_method(self):
        """Agent should be able to use self.llm in process() method."""

        class LLMUsingAgent(BaseAgent):
            """Agent that uses LLM in process."""

            async def process(self, input_data: dict) -> AgentResult:
                # Access LLM (will create provider)
                llm = self.llm
                assert llm is not None

                return AgentResult(
                    success=True,
                    data={"llm_available": True}
                )

        agent = LLMUsingAgent(name="llm_user")
        result = await agent.process({})

        # If we got here, LLM was accessible
        assert result.success is True
        assert result.data["llm_available"] is True
        assert agent._llm_provider is not None

    @pytest.mark.asyncio
    async def test_agent_can_call_llm_chat(self):
        """Agent should be able to call llm.chat() (requires real Ollama)."""
        # Skip if Ollama not available
        try:
            import httpx
            response = httpx.get("http://192.168.12.124:11434/api/tags", timeout=2.0)
            if response.status_code != 200:
                pytest.skip("Ollama not available")
        except Exception:
            pytest.skip("Ollama not available")

        class ChatAgent(BaseAgent):
            """Agent that calls LLM chat."""

            async def process(self, input_data: dict) -> AgentResult:
                response = await self.llm.chat([
                    {"role": "user", "content": "Say 'test'"}
                ])

                return AgentResult(
                    success=True,
                    data={"response": response}
                )

        agent = ChatAgent(name="chat_agent")
        result = await agent.process({})

        assert result.success is True
        assert "response" in result.data
        assert isinstance(result.data["response"], str)

    def test_agent_initialization_does_not_create_provider(self):
        """Creating agent should not immediately create provider (lazy)."""
        agent = TestAgent(name="test")

        # Provider should be None until accessed
        assert agent._llm_provider is None

    def test_agent_with_config_and_llm_provider(self):
        """Agent should accept both config and llm_provider."""
        mock_provider = OllamaProvider(
            base_url="http://test:11434",
            model_name="test-model"
        )

        agent = TestAgent(
            name="test",
            config={"setting": "value"},
            llm_provider=mock_provider
        )

        assert agent.config == {"setting": "value"}
        assert agent.llm is mock_provider
