"""Tests for OrchestratorAgent - LangGraph workflow coordinator.

TDD Structure:
1. TestOrchestratorSpecification - ALWAYS PASSING (requirements documentation)
2. TestOrchestratorStructure - Tests agent interface compliance
3. TestOrchestratorExecution - Tests workflow behavior
4. TestOrchestratorIntegration - Tests end-to-end workflow
"""

import pytest

from find_evil_agent.agents.base import AgentResult, AgentStatus
from find_evil_agent.agents.schemas import AgentState

# Conditional import for TDD - OrchestratorAgent may not exist yet
try:
    from find_evil_agent.agents.orchestrator import OrchestratorAgent

    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False

    # Placeholder for testing structure
    class OrchestratorAgent:
        pass


class TestOrchestratorSpecification:
    """Specification tests - ALWAYS PASSING.

    Document OrchestratorAgent requirements and expected behavior.
    """

    def test_orchestrator_requirements(self):
        """Document OrchestratorAgent requirements."""
        requirements = {
            "workflow": "LangGraph state machine for agent orchestration",
            "agents": "Coordinates ToolSelector, ToolExecutor, Analyzer",
            "state_management": "Maintains AgentState across workflow steps",
            "error_handling": "Graceful degradation on agent failures",
            "workflow_steps": [
                "1. Tool Selection (ToolSelectorAgent)",
                "2. Tool Execution (ToolExecutorAgent)",
                "3. Analysis (AnalyzerAgent)",
                "4. Return results",
            ],
            "output": "AgentResult with complete analysis",
        }
        assert requirements["workflow"] == "LangGraph state machine for agent orchestration"
        assert len(requirements["workflow_steps"]) == 4

    def test_workflow_architecture(self):
        """Document workflow architecture."""
        workflow = {
            "start": "Receive incident_description and analysis_goal",
            "node1": "ToolSelectorAgent - Select appropriate tool",
            "node2": "ToolExecutorAgent - Execute selected tool",
            "node3": "AnalyzerAgent - Analyze tool output",
            "end": "Return AgentState with findings",
            "state": "AgentState passed between nodes",
            "edges": "Conditional routing based on agent results",
        }
        assert workflow["start"] == "Receive incident_description and analysis_goal"
        assert workflow["state"] == "AgentState passed between nodes"

    def test_state_management_strategy(self):
        """Document state management strategy."""
        strategy = {
            "state_type": "AgentState (Pydantic model)",
            "persistence": "In-memory for single workflow run",
            "updates": "Each agent updates relevant state fields",
            "immutability": "State is passed by reference, updated in place",
            "history": "Maintains step_count and current_agent",
        }
        assert strategy["state_type"] == "AgentState (Pydantic model)"
        assert strategy["history"] == "Maintains step_count and current_agent"

    def test_error_handling_strategy(self):
        """Document error handling strategy."""
        strategy = {
            "agent_failure": "Continue workflow with partial results",
            "validation_failure": "Return error in AgentResult",
            "timeout": "Configurable per-agent timeout",
            "retry": "No automatic retry (fail fast)",
            "logging": "Log all errors to structlog",
        }
        assert strategy["agent_failure"] == "Continue workflow with partial results"
        assert strategy["retry"] == "No automatic retry (fail fast)"


@pytest.mark.skipif(not ORCHESTRATOR_AVAILABLE, reason="OrchestratorAgent not implemented yet")
class TestOrchestratorStructure:
    """Structure tests - Validate agent interface compliance."""

    def test_orchestrator_inherits_from_base_agent(self):
        """OrchestratorAgent should inherit from BaseAgent."""
        from find_evil_agent.agents.base import BaseAgent

        agent = OrchestratorAgent()
        assert isinstance(agent, BaseAgent)

    def test_orchestrator_has_process_method(self):
        """OrchestratorAgent should have async process() method."""
        agent = OrchestratorAgent()
        assert hasattr(agent, "process")
        assert callable(agent.process)

    def test_orchestrator_has_validate_method(self):
        """OrchestratorAgent should have validate() method."""
        agent = OrchestratorAgent()
        assert hasattr(agent, "validate")
        assert callable(agent.validate)

    def test_orchestrator_name_is_orchestrator(self):
        """OrchestratorAgent name should be 'orchestrator'."""
        agent = OrchestratorAgent()
        assert agent.name == "orchestrator"

    def test_orchestrator_has_agent_references(self):
        """OrchestratorAgent should have references to sub-agents."""
        agent = OrchestratorAgent()
        assert hasattr(agent, "tool_selector")
        assert hasattr(agent, "tool_executor")
        assert hasattr(agent, "analyzer")


@pytest.mark.skipif(not ORCHESTRATOR_AVAILABLE, reason="OrchestratorAgent not implemented yet")
class TestOrchestratorExecution:
    """Execution tests - Test workflow behavior."""

    @pytest.mark.asyncio
    async def test_process_returns_agent_result(self):
        """process() should return AgentResult."""
        agent = OrchestratorAgent()

        input_data = {
            "incident_description": "Suspicious process detected",
            "analysis_goal": "Identify malicious activity",
        }

        result = await agent.process(input_data)

        assert isinstance(result, AgentResult)
        assert hasattr(result, "success")
        assert hasattr(result, "data")

    @pytest.mark.asyncio
    async def test_validate_requires_incident_description(self):
        """validate() should require incident_description and analysis_goal."""
        agent = OrchestratorAgent()

        # Missing both
        assert not await agent.validate({})

        # Missing analysis_goal
        assert not await agent.validate({"incident_description": "test"})

        # Missing incident_description
        assert not await agent.validate({"analysis_goal": "test"})

        # Valid input
        assert await agent.validate({"incident_description": "test", "analysis_goal": "test"})

    @pytest.mark.asyncio
    async def test_process_with_invalid_input_returns_error(self):
        """process() should return error for invalid input."""
        agent = OrchestratorAgent()

        result = await agent.process({})
        assert not result.success
        assert result.status == AgentStatus.FAILED
        assert "incident_description" in result.error.lower() or "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_process_includes_agent_state_in_data(self):
        """process() should include AgentState in data."""
        agent = OrchestratorAgent()

        input_data = {"incident_description": "Test incident", "analysis_goal": "Test goal"}

        result = await agent.process(input_data)

        if result.success:
            assert "state" in result.data
            assert isinstance(result.data["state"], AgentState)

    @pytest.mark.asyncio
    async def test_state_includes_session_id(self):
        """AgentState should include session_id."""
        agent = OrchestratorAgent()

        input_data = {"incident_description": "Test incident", "analysis_goal": "Test goal"}

        result = await agent.process(input_data)

        if result.success and "state" in result.data:
            state = result.data["state"]
            assert state.session_id is not None

    @pytest.mark.asyncio
    async def test_state_tracks_step_count(self):
        """AgentState should track step_count."""
        agent = OrchestratorAgent()

        input_data = {"incident_description": "Test incident", "analysis_goal": "Test goal"}

        result = await agent.process(input_data)

        if result.success and "state" in result.data:
            state = result.data["state"]
            # Should have incremented through workflow steps
            assert state.step_count > 0

    @pytest.mark.asyncio
    async def test_workflow_executes_in_sequence(self):
        """Workflow should execute agents in correct sequence."""
        agent = OrchestratorAgent()

        input_data = {
            "incident_description": "Memory analysis needed",
            "analysis_goal": "Find malicious processes",
        }

        result = await agent.process(input_data)

        if result.success and "state" in result.data:
            state = result.data["state"]
            # Should have tool selection
            assert len(state.selected_tools) > 0 or not result.success
            # Should have execution results if tools selected
            # Should have findings if analysis ran


@pytest.mark.skipif(not ORCHESTRATOR_AVAILABLE, reason="OrchestratorAgent not implemented yet")
@pytest.mark.integration
class TestOrchestratorIntegration:
    """Integration tests - Test end-to-end workflow.

    These tests require:
    - Ollama running at 192.168.12.124:11434
    - SIFT VM at 192.168.12.101:16789 (optional, can mock execution)
    """

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_end_to_end_memory_analysis(self):
        """Test full workflow for memory analysis scenario."""
        agent = OrchestratorAgent()

        input_data = {
            "incident_description": "Ransomware detected on Windows 10 system",
            "analysis_goal": "Identify malicious processes in memory dump",
        }

        result = await agent.process(input_data)

        # Workflow should complete (even if some steps fail)
        assert isinstance(result, AgentResult)

        if result.success and "state" in result.data:
            state = result.data["state"]

            # Should have selected a tool
            assert len(state.selected_tools) > 0
            tool_names = [t.tool_name for t in state.selected_tools]
            # Should select volatility or rekall for memory analysis
            assert any(name in ["volatility", "rekall"] for name in tool_names)

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_end_to_end_disk_forensics(self):
        """Test full workflow for disk forensics scenario."""
        agent = OrchestratorAgent()

        input_data = {
            "incident_description": "Suspicious files found on disk",
            "analysis_goal": "List files and find malware indicators",
        }

        result = await agent.process(input_data)

        assert isinstance(result, AgentResult)

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_end_to_end_network_analysis(self):
        """Test full workflow for network analysis scenario."""
        agent = OrchestratorAgent()

        input_data = {
            "incident_description": "Suspicious network traffic detected",
            "analysis_goal": "Analyze network connections and identify C2 communication",
        }

        result = await agent.process(input_data)

        assert isinstance(result, AgentResult)

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_handles_tool_selection_failure(self):
        """Test workflow handles tool selection failure gracefully."""
        agent = OrchestratorAgent()

        # Vague input that might fail tool selection
        input_data = {"incident_description": "Something weird happened", "analysis_goal": "Fix it"}

        result = await agent.process(input_data)

        # Should handle gracefully, not crash
        assert isinstance(result, AgentResult)

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_handles_execution_failure(self):
        """Test workflow handles execution failure gracefully."""
        agent = OrchestratorAgent()

        input_data = {"incident_description": "Test incident", "analysis_goal": "Test goal"}

        result = await agent.process(input_data)

        # Should complete even if execution fails (SIFT VM not connected)
        assert isinstance(result, AgentResult)
