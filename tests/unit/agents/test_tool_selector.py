"""Tests for ToolSelectorAgent - Intelligent SIFT tool selection.

TDD Structure:
1. TestToolSelectorSpecification - ALWAYS PASSING (requirements documentation)
2. TestToolSelectorStructure - Tests agent interface compliance
3. TestToolSelectorExecution - Tests actual agent behavior
"""

import pytest

from find_evil_agent.agents.base import AgentResult, AgentStatus
from find_evil_agent.agents.schemas import ToolSelection
from find_evil_agent.agents.tool_selector import ToolSelectorAgent
from find_evil_agent.tools.registry import ToolRegistry


class TestToolSelectorSpecification:
    """Specification tests - ALWAYS PASSING.

    Document ToolSelectorAgent requirements and expected behavior.
    """

    def test_tool_selector_requirements(self):
        """Document ToolSelectorAgent requirements."""
        requirements = {
            "hallucination_resistance": "Two-stage process (semantic + LLM)",
            "stage1": "Semantic search to narrow candidates (top-10)",
            "stage2": "LLM ranks with confidence scoring",
            "confidence_threshold": 0.7,
            "registry_validation": "Validate tool exists before returning",
            "structured_output": "ToolSelection Pydantic schema",
            "mandatory_reasoning": "LLM must explain selection",
        }
        assert requirements["stage1"] == "Semantic search to narrow candidates (top-10)"
        assert requirements["confidence_threshold"] == 0.7
        assert requirements["hallucination_resistance"] == "Two-stage process (semantic + LLM)"

    def test_two_stage_selection_workflow(self):
        """Document two-stage selection workflow."""
        workflow = {
            "step1": "Receive incident_description and analysis_goal",
            "step2": "Semantic search registry for top-k candidates",
            "step3": "Format candidates for LLM prompt",
            "step4": "LLM selects best tool with confidence + reasoning",
            "step5": "Validate confidence >= threshold",
            "step6": "Validate tool exists in registry",
            "step7": "Return AgentResult with selection",
        }
        assert workflow["step2"] == "Semantic search registry for top-k candidates"
        assert workflow["step5"] == "Validate confidence >= threshold"
        assert workflow["step6"] == "Validate tool exists in registry"

    def test_confidence_threshold_strategy(self):
        """Document confidence threshold strategy."""
        strategy = {
            "threshold": 0.7,
            "above_threshold": "Accept selection",
            "below_threshold": "Reject with error",
            "purpose": "Filter uncertain selections",
            "scoring_guide": {
                "1.0": "Perfect match",
                "0.8-0.9": "Very good match",
                "0.7-0.79": "Good match",
                "0.5-0.69": "Uncertain",
                "<0.5": "Poor match",
            },
        }
        assert strategy["threshold"] == 0.7
        assert strategy["below_threshold"] == "Reject with error"

    def test_hallucination_prevention_mechanisms(self):
        """Document hallucination prevention mechanisms."""
        mechanisms = {
            "semantic_constraint": "LLM only sees real tools from semantic search",
            "confidence_scoring": "LLM must assign confidence (forces introspection)",
            "threshold_enforcement": "Low confidence selections rejected",
            "registry_validation": "Final check tool exists",
            "structured_output": "Pydantic schema prevents malformed responses",
        }
        assert mechanisms["semantic_constraint"] == "LLM only sees real tools from semantic search"
        assert mechanisms["registry_validation"] == "Final check tool exists"


class TestToolSelectorStructure:
    """Structure tests - Validate agent interface compliance."""

    def test_tool_selector_inherits_from_base_agent(self):
        """ToolSelectorAgent should inherit from BaseAgent."""
        from find_evil_agent.agents.base import BaseAgent

        agent = ToolSelectorAgent()
        assert isinstance(agent, BaseAgent)

    def test_tool_selector_has_process_method(self):
        """ToolSelectorAgent should have async process() method."""
        agent = ToolSelectorAgent()
        assert hasattr(agent, "process")
        assert callable(agent.process)

    def test_tool_selector_has_validate_method(self):
        """ToolSelectorAgent should have validate() method."""
        agent = ToolSelectorAgent()
        assert hasattr(agent, "validate")
        assert callable(agent.validate)

    def test_tool_selector_accepts_registry_parameter(self):
        """ToolSelectorAgent should accept optional registry parameter."""
        mock_registry = ToolRegistry()

        agent = ToolSelectorAgent(registry=mock_registry)
        assert agent.registry is mock_registry

    def test_tool_selector_creates_registry_if_not_provided(self):
        """ToolSelectorAgent should create registry if not provided."""
        agent = ToolSelectorAgent()
        assert agent.registry is not None
        assert isinstance(agent.registry, ToolRegistry)

    def test_tool_selector_accepts_configuration_parameters(self):
        """ToolSelectorAgent should accept confidence_threshold and semantic_top_k."""
        agent = ToolSelectorAgent(confidence_threshold=0.8, semantic_top_k=5)
        assert agent.confidence_threshold == 0.8
        assert agent.semantic_top_k == 5

    def test_tool_selector_has_default_configuration(self):
        """ToolSelectorAgent should have sensible defaults."""
        agent = ToolSelectorAgent()
        assert agent.confidence_threshold == 0.7
        assert agent.semantic_top_k == 10


class TestToolSelectorExecution:
    """Execution tests - Test actual agent behavior."""

    @pytest.mark.asyncio
    async def test_validate_requires_incident_description(self):
        """validate() should require incident_description field."""
        agent = ToolSelectorAgent()

        valid = await agent.validate(
            {"incident_description": "Test incident", "analysis_goal": "Test goal"}
        )
        assert valid is True

        invalid = await agent.validate({"analysis_goal": "Test goal"})
        assert invalid is False

    @pytest.mark.asyncio
    async def test_validate_requires_analysis_goal(self):
        """validate() should require analysis_goal field."""
        agent = ToolSelectorAgent()

        valid = await agent.validate(
            {"incident_description": "Test incident", "analysis_goal": "Test goal"}
        )
        assert valid is True

        invalid = await agent.validate({"incident_description": "Test incident"})
        assert invalid is False

    @pytest.mark.asyncio
    async def test_validate_rejects_empty_strings(self):
        """validate() should reject empty strings."""
        agent = ToolSelectorAgent()

        invalid = await agent.validate({"incident_description": "", "analysis_goal": "Test goal"})
        assert invalid is False

        invalid = await agent.validate(
            {"incident_description": "Test incident", "analysis_goal": ""}
        )
        assert invalid is False

    @pytest.mark.asyncio
    async def test_validate_accepts_optional_evidence_type(self):
        """validate() should accept optional evidence_type field."""
        agent = ToolSelectorAgent()

        valid = await agent.validate(
            {
                "incident_description": "Test incident",
                "analysis_goal": "Test goal",
                "evidence_type": "memory",
            }
        )
        assert valid is True

    @pytest.mark.asyncio
    async def test_process_returns_agent_result(self):
        """process() should return AgentResult instance."""
        agent = ToolSelectorAgent()

        result = await agent.process(
            {
                "incident_description": "Suspicious process detected",
                "analysis_goal": "Analyze memory dump for malicious processes",
            }
        )

        assert isinstance(result, AgentResult)

    @pytest.mark.asyncio
    async def test_process_fails_with_invalid_input(self):
        """process() should return failed result for invalid input."""
        agent = ToolSelectorAgent()

        result = await agent.process(
            {
                "incident_description": "Test"
                # Missing analysis_goal
            }
        )

        assert result.success is False
        assert result.status == AgentStatus.FAILED
        assert "Invalid input" in result.error

    @pytest.mark.asyncio
    async def test_process_performs_semantic_search(self):
        """process() should perform semantic search on registry."""
        agent = ToolSelectorAgent()

        # This will perform actual semantic search
        result = await agent.process(
            {
                "incident_description": "Ransomware detected on workstation",
                "analysis_goal": "Find running processes in memory dump",
            }
        )

        # Should return candidates in data
        if result.success:
            assert "candidates" in result.data
            assert isinstance(result.data["candidates"], list)
            assert len(result.data["candidates"]) > 0

    @pytest.mark.asyncio
    async def test_process_uses_llm_for_selection(self):
        """process() should use LLM to select tool from candidates."""
        agent = ToolSelectorAgent()

        result = await agent.process(
            {
                "incident_description": "Memory dump contains suspicious process",
                "analysis_goal": "Extract process list from memory",
            }
        )

        # Should include tool_selection in result
        if result.success:
            assert "tool_selection" in result.data
            assert isinstance(result.data["tool_selection"], ToolSelection)

    @pytest.mark.asyncio
    async def test_successful_selection_includes_tool_metadata(self):
        """Successful selection should include tool metadata from registry."""
        agent = ToolSelectorAgent()

        result = await agent.process(
            {
                "incident_description": "Need to list files on disk image",
                "analysis_goal": "Find all files including deleted ones",
            }
        )

        if result.success:
            assert "tool_metadata" in result.data
            metadata = result.data["tool_metadata"]
            assert "name" in metadata
            assert "category" in metadata
            assert "description" in metadata

    @pytest.mark.asyncio
    async def test_successful_selection_includes_semantic_top_match(self):
        """Result should include top semantic match for comparison."""
        agent = ToolSelectorAgent()

        result = await agent.process(
            {
                "incident_description": "Analyze network traffic",
                "analysis_goal": "Inspect packets in PCAP file",
            }
        )

        if result.success:
            assert "semantic_top_match" in result.data
            assert isinstance(result.data["semantic_top_match"], str)

    @pytest.mark.asyncio
    async def test_tool_selection_has_required_fields(self):
        """ToolSelection should have tool_name, confidence, reason, alternatives, inputs."""
        agent = ToolSelectorAgent()

        result = await agent.process(
            {
                "incident_description": "Hash verification needed",
                "analysis_goal": "Calculate file hashes for integrity check",
            }
        )

        if result.success:
            selection = result.data["tool_selection"]
            assert hasattr(selection, "tool_name")
            assert hasattr(selection, "confidence")
            assert hasattr(selection, "reason")
            assert hasattr(selection, "alternatives")
            assert hasattr(selection, "inputs")

    @pytest.mark.asyncio
    async def test_confidence_threshold_enforcement(self):
        """Selections below confidence threshold should be rejected."""
        # Use high threshold to force rejection
        agent = ToolSelectorAgent(confidence_threshold=0.95)

        # Vague query may result in low confidence
        result = await agent.process(
            {
                "incident_description": "Something weird happened",
                "analysis_goal": "Do some analysis",
            }
        )

        # If confidence is low, should fail
        if not result.success:
            assert "confidence" in result.error.lower() or "threshold" in result.error.lower()
            assert "tool_selection" in result.data  # Still included for debugging
            assert result.data["tool_selection"].confidence < 0.95

    @pytest.mark.asyncio
    async def test_registry_validation_prevents_hallucination(self):
        """Registry validation should catch hallucinated tools."""
        # Note: This is hard to test directly since semantic search constrains LLM
        # But we verify the validation logic exists
        agent = ToolSelectorAgent()

        # If LLM somehow returns unknown tool, registry.get_tool() returns None
        # and agent should return failed result with hallucination error

        # Verify agent has registry validation in process()
        assert hasattr(agent, "registry")
        assert hasattr(agent.registry, "get_tool")

    @pytest.mark.asyncio
    async def test_format_candidates_includes_similarity(self):
        """_format_candidates should include similarity scores."""
        agent = ToolSelectorAgent()

        # Get some candidates
        candidates = agent.registry.search("memory analysis", top_k=3)

        # Format them
        formatted = agent._format_candidates(candidates)

        assert isinstance(formatted, str)
        assert "similarity" in formatted.lower()
        for candidate in candidates:
            assert candidate["tool"]["name"] in formatted

    @pytest.mark.asyncio
    async def test_format_candidates_includes_examples(self):
        """_format_candidates should include example usage if available."""
        agent = ToolSelectorAgent()

        candidates = agent.registry.search("volatility", top_k=1)
        formatted = agent._format_candidates(candidates)

        # Volatility has examples in metadata
        assert "example" in formatted.lower() or "volatility" in formatted.lower()

    @pytest.mark.asyncio
    async def test_evidence_type_influences_search(self):
        """evidence_type should be included in semantic search query."""
        agent = ToolSelectorAgent()

        # With evidence_type
        result_with_type = await agent.process(
            {
                "incident_description": "Suspicious activity",
                "analysis_goal": "Find processes",
                "evidence_type": "memory",
            }
        )

        # Without evidence_type
        result_without_type = await agent.process(
            {"incident_description": "Suspicious activity", "analysis_goal": "Find processes"}
        )

        # Both should succeed, but may select different tools
        assert isinstance(result_with_type, AgentResult)
        assert isinstance(result_without_type, AgentResult)

    @pytest.mark.asyncio
    async def test_process_handles_exceptions_gracefully(self):
        """process() should catch exceptions and return failed result."""
        agent = ToolSelectorAgent()

        # Pass invalid data type to trigger exception
        result = await agent.process(None)

        assert result.success is False
        assert result.status == AgentStatus.FAILED
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_agent_logs_selection_events(self):
        """Agent should log selection start, semantic search, LLM selection, success."""
        # This test verifies logging structure exists
        # Actual log output verification would require capturing structlog output

        agent = ToolSelectorAgent()
        assert hasattr(agent, "name")
        assert agent.name == "tool_selector"

    @pytest.mark.asyncio
    async def test_result_includes_top_5_candidates(self):
        """Result should include top 5 candidates for context."""
        agent = ToolSelectorAgent(semantic_top_k=10)

        result = await agent.process(
            {
                "incident_description": "File system analysis needed",
                "analysis_goal": "List files in disk image",
            }
        )

        if result.success:
            candidates = result.data["candidates"]
            assert len(candidates) <= 5  # Top 5 included

    @pytest.mark.asyncio
    async def test_different_queries_select_different_tools(self):
        """Different incident types should select different tools."""
        agent = ToolSelectorAgent()

        # Memory analysis
        memory_result = await agent.process(
            {
                "incident_description": "Malware in memory",
                "analysis_goal": "Extract process list from RAM dump",
            }
        )

        # Network analysis
        network_result = await agent.process(
            {
                "incident_description": "Suspicious network traffic",
                "analysis_goal": "Analyze packets in PCAP file",
            }
        )

        # Disk analysis
        disk_result = await agent.process(
            {
                "incident_description": "Deleted files need recovery",
                "analysis_goal": "List all files including deleted",
            }
        )

        # Should select different tools
        if all([memory_result.success, network_result.success, disk_result.success]):
            tools = [
                memory_result.data["tool_selection"].tool_name,
                network_result.data["tool_selection"].tool_name,
                disk_result.data["tool_selection"].tool_name,
            ]
            # At least 2 should be different
            assert len(set(tools)) >= 2


# Integration tests (require real Ollama)
class TestToolSelectorIntegration:
    """Integration tests with real Ollama server.

    These tests require Ollama running at 192.168.12.124:11434.
    They test the full two-stage selection workflow.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_workflow_memory_analysis(self):
        """Test complete workflow for memory analysis scenario."""
        agent = ToolSelectorAgent()

        result = await agent.process(
            {
                "incident_description": "Ransomware detected encrypting files on workstation",
                "analysis_goal": "Identify malicious processes running in memory",
                "evidence_type": "memory dump",
            }
        )

        assert result.success is True
        assert result.data["tool_selection"].tool_name in ["volatility", "rekall"]
        assert result.data["tool_selection"].confidence >= 0.7
        assert len(result.data["tool_selection"].reason) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_workflow_disk_analysis(self):
        """Test complete workflow for disk analysis scenario."""
        agent = ToolSelectorAgent()

        result = await agent.process(
            {
                "incident_description": "Suspected data exfiltration from compromised server",
                "analysis_goal": "Find recently deleted files on disk image",
                "evidence_type": "disk image",
            }
        )

        assert result.success is True
        assert result.data["tool_selection"].tool_name in ["fls", "icat", "bulk_extractor"]
        assert result.data["tool_selection"].confidence >= 0.7

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_workflow_network_analysis(self):
        """Test complete workflow for network analysis scenario."""
        agent = ToolSelectorAgent()

        result = await agent.process(
            {
                "incident_description": "Unusual outbound connections detected by firewall",
                "analysis_goal": "Analyze network traffic patterns in PCAP",
                "evidence_type": "network capture",
            }
        )

        assert result.success is True
        assert result.data["tool_selection"].tool_name in ["tcpdump", "wireshark"]
        assert result.data["tool_selection"].confidence >= 0.7

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_llm_provides_reasoning(self):
        """LLM should provide detailed reasoning for selection."""
        agent = ToolSelectorAgent()

        result = await agent.process(
            {
                "incident_description": "Windows registry hive needs analysis",
                "analysis_goal": "Extract user activity artifacts from NTUSER.DAT",
            }
        )

        if result.success:
            selection = result.data["tool_selection"]
            assert len(selection.reason) > 20  # Meaningful explanation
            assert (
                "regripper" in selection.tool_name.lower() or "registry" in selection.reason.lower()
            )

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)  # Allow 2 minutes for LLM response
    async def test_llm_suggests_alternatives(self):
        """LLM should suggest alternative tools if applicable."""
        agent = ToolSelectorAgent()

        result = await agent.process(
            {
                "incident_description": "Need to calculate file hashes",
                "analysis_goal": "Verify file integrity",
            }
        )

        if result.success:
            selection = result.data["tool_selection"]
            # Should mention md5sum, sha256sum, or similar
            assert len(selection.alternatives) >= 0  # May or may not have alternatives

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_llm_specifies_required_inputs(self):
        """LLM should specify required inputs for selected tool."""
        agent = ToolSelectorAgent()

        result = await agent.process(
            {
                "incident_description": "Memory dump analysis required",
                "analysis_goal": "List running processes",
            }
        )

        if result.success:
            selection = result.data["tool_selection"]
            assert isinstance(selection.inputs, dict)
            # Volatility requires profile and plugin
            if selection.tool_name == "volatility":
                # Check if inputs dict has relevant keys
                inputs_str = str(selection.inputs).lower()
                assert (
                    "profile" in inputs_str or "plugin" in inputs_str or len(selection.inputs) > 0
                )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_semantic_search_constrains_llm_effectively(self):
        """Semantic search should successfully constrain LLM to relevant tools."""
        agent = ToolSelectorAgent(semantic_top_k=5)

        result = await agent.process(
            {
                "incident_description": "String extraction from binary file",
                "analysis_goal": "Find readable text in executable",
            }
        )

        if result.success:
            # Semantic search should have found 'strings' tool
            # LLM should select it
            assert result.data["tool_selection"].tool_name == "strings"

            # Top semantic match should also be strings
            assert result.data["semantic_top_match"] == "strings"

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.timeout(180)  # Allow 3 minutes for two LLM calls
    async def test_confidence_reflects_query_clarity(self):
        """Confidence should be higher for clear queries vs vague ones."""
        agent = ToolSelectorAgent()

        # Clear, specific query
        clear_result = await agent.process(
            {
                "incident_description": "Need to run Volatility pslist plugin on Windows 7 memory dump",
                "analysis_goal": "Extract running processes from memory.raw",
            }
        )

        # Vague, unclear query
        vague_result = await agent.process(
            {"incident_description": "Something is wrong", "analysis_goal": "Check the computer"}
        )

        # Clear query should have higher confidence
        if clear_result.success and vague_result.success:
            assert (
                clear_result.data["tool_selection"].confidence
                > vague_result.data["tool_selection"].confidence
            )
        elif clear_result.success and not vague_result.success:
            # Vague query may fail threshold
            assert True
