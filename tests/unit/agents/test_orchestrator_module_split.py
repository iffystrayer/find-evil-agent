"""Test orchestrator module split structure (C3c refactor).

Verifies:
1. agent.py LOC ceiling (prevent re-bloat)
2. OrchestratorAgent re-accessible from package
3. Split modules contain expected functions
4. No workflow/prompt building logic in agent.py
"""

import pytest
import inspect
from pathlib import Path

from find_evil_agent.agents.orchestrator import OrchestratorAgent
from find_evil_agent.agents.orchestrator import agent as agent_module
from find_evil_agent.agents.orchestrator import workflows, prompting


class TestOrchestratorSplitStructure:
    """Verify orchestrator module split structure."""

    def test_agent_module_loc_ceiling(self):
        """agent.py must stay under 750 LOC to prevent re-bloat."""
        agent_file = Path(agent_module.__file__)
        with open(agent_file, 'r') as f:
            loc = len(f.readlines())

        assert loc < 750, (
            f"agent.py has {loc} lines (limit: 750). "
            "If adding new functionality, extract to workflows.py or prompting.py."
        )

    def test_orchestrator_agent_accessible_from_package(self):
        """OrchestratorAgent must be importable from package root."""
        from find_evil_agent.agents.orchestrator import OrchestratorAgent as PkgAgent
        from find_evil_agent.agents.orchestrator.agent import OrchestratorAgent as ModAgent

        # Both imports should work and reference the same class
        assert PkgAgent is ModAgent
        assert PkgAgent.__name__ == "OrchestratorAgent"

    def test_workflows_module_has_builders(self):
        """workflows.py must export workflow builder functions."""
        assert hasattr(workflows, "build_workflow")
        assert hasattr(workflows, "build_iterative_workflow")

        # Verify they're callable
        assert callable(workflows.build_workflow)
        assert callable(workflows.build_iterative_workflow)

    def test_prompting_module_has_helpers(self):
        """prompting.py must export prompt building and parsing helpers."""
        assert hasattr(prompting, "build_lead_extraction_prompt")
        assert hasattr(prompting, "parse_leads_from_response")
        assert hasattr(prompting, "extract_leads_fallback")

        # Verify they're callable
        assert callable(prompting.build_lead_extraction_prompt)
        assert callable(prompting.parse_leads_from_response)
        assert callable(prompting.extract_leads_fallback)

    def test_no_workflow_building_in_agent_module(self):
        """agent.py should not contain workflow building logic."""
        agent_file = Path(agent_module.__file__)
        with open(agent_file, 'r') as f:
            content = f.read()

        # Should not have StateGraph or workflow.add_node in agent.py
        # (These should be in workflows.py)
        assert "StateGraph(dict)" not in content, (
            "StateGraph instantiation found in agent.py - should be in workflows.py"
        )
        assert "workflow.add_node(" not in content, (
            "workflow.add_node found in agent.py - should be in workflows.py"
        )

    def test_no_prompt_building_in_agent_module(self):
        """agent.py should not contain prompt building logic."""
        agent_file = Path(agent_module.__file__)
        with open(agent_file, 'r') as f:
            content = f.read()

        # Should not have lead extraction prompt templates
        assert "You are a DFIR expert" not in content, (
            "Prompt template found in agent.py - should be in prompting.py"
        )
        assert "LEAD: <type> |" not in content, (
            "Lead parsing format found in agent.py - should be in prompting.py"
        )

    def test_orchestrator_uses_extracted_functions(self):
        """OrchestratorAgent should use extracted workflow/prompting functions."""
        # Check __init__ uses build_workflow
        init_source = inspect.getsource(OrchestratorAgent.__init__)
        assert "build_workflow(" in init_source
        assert "build_iterative_workflow(" in init_source

        # Check _extract_leads uses prompting functions
        extract_leads_source = inspect.getsource(OrchestratorAgent._extract_leads)
        assert "build_lead_extraction_prompt" in extract_leads_source
        assert "parse_leads_from_response" in extract_leads_source
        assert "extract_leads_fallback" in extract_leads_source

    def test_split_module_sizes_reasonable(self):
        """Split modules should be reasonably sized."""
        workflows_file = Path(workflows.__file__)
        prompting_file = Path(prompting.__file__)

        with open(workflows_file, 'r') as f:
            workflows_loc = len(f.readlines())

        with open(prompting_file, 'r') as f:
            prompting_loc = len(f.readlines())

        # workflows.py should be substantial (extracted node implementations)
        assert workflows_loc > 200, f"workflows.py seems too small ({workflows_loc} LOC)"
        assert workflows_loc < 600, f"workflows.py seems too large ({workflows_loc} LOC)"

        # prompting.py should be focused (prompt building/parsing)
        assert prompting_loc > 100, f"prompting.py seems too small ({prompting_loc} LOC)"
        assert prompting_loc < 300, f"prompting.py seems too large ({prompting_loc} LOC)"


class TestOrchestratorBackwardCompatibility:
    """Verify backward compatibility of split."""

    def test_old_imports_still_work(self):
        """All old import paths should still work."""
        # Package-level import
        from find_evil_agent.agents.orchestrator import OrchestratorAgent
        assert OrchestratorAgent is not None

        # Module import pattern (if anyone used it)
        from find_evil_agent.agents import orchestrator
        assert hasattr(orchestrator, "OrchestratorAgent")

    def test_orchestrator_agent_functionality_preserved(self):
        """OrchestratorAgent should have all expected methods."""
        expected_methods = [
            "process",
            "validate",
            "process_iterative",
            "_extract_leads",
            "_select_next_lead",
            "_create_follow_up_goal",
            "_calculate_confidence",
            "_generate_summary",
            "_merge_iocs",
            "_merge_iocs_dict",
            "_should_continue",
            "_get_stopping_reason",
            "_synthesize_investigation",
            "_build_tool_command",  # Deprecated but kept
        ]

        for method_name in expected_methods:
            assert hasattr(OrchestratorAgent, method_name), (
                f"OrchestratorAgent missing expected method: {method_name}"
            )
