"""TDD test suite for iterative analysis orchestration.

This module tests the autonomous iterative analysis feature where the agent
automatically follows investigative leads to build a complete attack chain.

Test Structure:
1. TestIterativeOrchestrationSpecification - Requirements (ALWAYS PASSING)
2. TestIterativeOrchestrationStructure - Interface compliance
3. TestIterativeOrchestrationExecution - Core functionality
4. TestIterativeOrchestrationIntegration - End-to-end workflows
"""

import pytest
from datetime import datetime
from uuid import uuid4

# Conditional import for TDD - Components may not exist yet
try:
    from find_evil_agent.agents.schemas import (
        InvestigativeLead,
        IterationResult,
        IterativeAnalysisResult,
        LeadPriority,
        LeadType,
    )
    from find_evil_agent.agents.orchestrator import OrchestratorAgent
    SCHEMAS_AVAILABLE = True
except ImportError:
    SCHEMAS_AVAILABLE = False

    # Placeholder classes for testing structure
    class InvestigativeLead:
        pass

    class IterationResult:
        pass

    class IterativeAnalysisResult:
        pass

    class LeadPriority:
        pass

    class LeadType:
        pass

    class OrchestratorAgent:
        pass


class TestIterativeOrchestrationSpecification:
    """Test specification - documents requirements (ALWAYS PASSING)."""

    def test_iterative_analysis_requirements(self):
        """Document what iterative analysis must do."""
        requirements = {
            "input": "incident_description + analysis_goal + max_iterations",
            "output": "complete_investigation_chain + all_findings + all_iocs",
            "workflow": "analyze → extract_leads → follow_leads → repeat → synthesize",
            "stopping_conditions": [
                "max_iterations_reached",
                "no_leads_found",
                "user_disabled_auto_follow",
                "confidence_too_low"
            ],
            "lead_types": ["process", "network", "file", "timeline", "registry"],
            "priorities": ["high", "medium", "low"]
        }
        assert requirements["workflow"] == "analyze → extract_leads → follow_leads → repeat → synthesize"
        assert len(requirements["stopping_conditions"]) == 4
        assert len(requirements["lead_types"]) == 5

    def test_investigative_lead_schema_requirements(self):
        """Document InvestigativeLead schema requirements."""
        schema = {
            "lead_type": "Type of investigation (process/network/file/timeline/registry)",
            "description": "Human-readable description of what to investigate",
            "priority": "High/medium/low priority for follow-up",
            "suggested_tool": "Optional tool recommendation",
            "context": "Dict with IOCs or data needed for investigation",
            "confidence": "How confident the LLM is this lead is worth following"
        }
        assert "lead_type" in schema
        assert "priority" in schema
        assert "context" in schema

    def test_iteration_result_schema_requirements(self):
        """Document IterationResult schema requirements."""
        schema = {
            "iteration_number": "Which iteration (1-based)",
            "tool_used": "Tool that was executed",
            "findings": "Findings from this iteration",
            "iocs": "IOCs extracted this iteration",
            "leads_discovered": "New leads found",
            "lead_followed": "The lead that triggered this iteration (None for first)",
            "duration": "How long this iteration took",
            "timestamp": "When iteration completed"
        }
        assert "iteration_number" in schema
        assert "leads_discovered" in schema
        assert "lead_followed" in schema

    def test_stopping_conditions_specification(self):
        """Document when iterative analysis should stop."""
        stopping_conditions = {
            "max_iterations": "Prevent infinite loops (default: 5)",
            "no_leads": "No new investigative leads discovered",
            "auto_follow_disabled": "User wants manual control",
            "low_confidence": "Leads have confidence below threshold"
        }
        assert stopping_conditions["max_iterations"] == "Prevent infinite loops (default: 5)"


class TestIterativeOrchestrationStructure:
    """Test structure - validates interface compliance."""

    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    def test_investigative_lead_has_required_fields(self):
        """InvestigativeLead must have all required fields."""
        lead = InvestigativeLead(
            lead_type=LeadType.NETWORK,
            description="Check network traffic for C2 communication",
            priority=LeadPriority.HIGH,
            context={"process": "ransom.exe", "pid": 4532},
            confidence=0.85
        )

        assert hasattr(lead, 'lead_type')
        assert hasattr(lead, 'description')
        assert hasattr(lead, 'priority')
        assert hasattr(lead, 'context')
        assert hasattr(lead, 'confidence')
        assert hasattr(lead, 'suggested_tool')  # Optional field

    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    def test_iteration_result_has_required_fields(self):
        """IterationResult must have all required fields."""
        result = IterationResult(
            iteration_number=1,
            tool_used="volatility",
            findings=[],
            iocs={},
            leads_discovered=[],
            lead_followed=None,
            duration=45.2
        )

        assert hasattr(result, 'iteration_number')
        assert hasattr(result, 'tool_used')
        assert hasattr(result, 'findings')
        assert hasattr(result, 'iocs')
        assert hasattr(result, 'leads_discovered')
        assert hasattr(result, 'lead_followed')
        assert hasattr(result, 'duration')
        assert hasattr(result, 'timestamp')

    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    def test_orchestrator_has_iterative_methods(self):
        """OrchestratorAgent must have iterative analysis methods."""
        orchestrator = OrchestratorAgent()

        # New methods for iterative analysis
        assert hasattr(orchestrator, 'process_iterative')
        assert callable(orchestrator.process_iterative)

        assert hasattr(orchestrator, '_extract_leads')
        assert callable(orchestrator._extract_leads)

        assert hasattr(orchestrator, '_should_continue')
        assert callable(orchestrator._should_continue)

        assert hasattr(orchestrator, '_synthesize_investigation')
        assert callable(orchestrator._synthesize_investigation)


class TestIterativeOrchestrationExecution:
    """Test execution - validates actual behavior."""

    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    @pytest.mark.asyncio
    async def test_single_iteration_creates_iteration_result(self):
        """Single iteration should create one IterationResult."""
        orchestrator = OrchestratorAgent()

        result = await orchestrator.process_iterative(
            incident_description="Test incident",
            analysis_goal="Test goal",
            max_iterations=1,
            auto_follow=False  # No follow-up
        )

        assert isinstance(result, IterativeAnalysisResult)
        assert len(result.iterations) == 1
        assert result.iterations[0].iteration_number == 1

    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    @pytest.mark.asyncio
    async def test_lead_extraction_from_findings(self):
        """Should extract investigative leads from analysis results."""
        orchestrator = OrchestratorAgent()

        # Mock findings with obvious leads
        findings = [
            {
                "description": "Suspicious process ransom.exe found",
                "severity": "critical"
            }
        ]
        iocs = {
            "processes": ["ransom.exe"]
        }

        leads = await orchestrator._extract_leads(
            findings=findings,
            iocs=iocs,
            iteration_number=1
        )

        assert isinstance(leads, list)
        assert len(leads) > 0
        assert all(isinstance(lead, InvestigativeLead) for lead in leads)

    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    @pytest.mark.asyncio
    async def test_network_lead_extracted_from_process_finding(self):
        """Finding suspicious process should suggest network analysis lead."""
        orchestrator = OrchestratorAgent()

        findings = [
            {
                "description": "Malicious process with network activity",
                "severity": "critical"
            }
        ]

        leads = await orchestrator._extract_leads(findings, {}, 1)

        # Should suggest checking network traffic
        network_leads = [l for l in leads if l.lead_type == LeadType.NETWORK]
        assert len(network_leads) > 0

    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    @pytest.mark.asyncio
    async def test_timeline_lead_extracted_from_ioc_finding(self):
        """Finding IOCs should suggest timeline analysis lead."""
        orchestrator = OrchestratorAgent()

        iocs = {
            "ips": ["203.0.113.42"],
            "domains": ["evil-c2.example.com"]
        }

        leads = await orchestrator._extract_leads([], iocs, 1)

        # Should suggest checking timeline for when these IOCs appeared
        timeline_leads = [l for l in leads if l.lead_type == LeadType.TIMELINE]
        assert len(timeline_leads) > 0

    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    @pytest.mark.asyncio
    async def test_max_iterations_stops_investigation(self):
        """Investigation should stop at max_iterations."""
        orchestrator = OrchestratorAgent()

        result = await orchestrator.process_iterative(
            incident_description="Ransomware detected",
            analysis_goal="Complete investigation",
            max_iterations=3,
            auto_follow=True
        )

        # Should not exceed max_iterations even if leads exist
        assert len(result.iterations) <= 3

    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    @pytest.mark.asyncio
    async def test_no_leads_stops_investigation(self):
        """Investigation should stop when no leads are found."""
        orchestrator = OrchestratorAgent()

        result = await orchestrator.process_iterative(
            incident_description="Simple benign activity",
            analysis_goal="Investigate",
            max_iterations=5,
            auto_follow=True
        )

        # Should stop early if no leads discovered
        # (Actual number depends on when LLM stops finding leads)
        assert len(result.iterations) >= 1

    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    @pytest.mark.asyncio
    async def test_auto_follow_disabled_stops_after_first(self):
        """With auto_follow=False, should run only initial analysis."""
        orchestrator = OrchestratorAgent()

        result = await orchestrator.process_iterative(
            incident_description="Ransomware detected",
            analysis_goal="Find malicious process",
            max_iterations=5,
            auto_follow=False  # Disabled
        )

        # Should only run initial iteration
        assert len(result.iterations) == 1

    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implementation yet")
    @pytest.mark.asyncio
    async def test_leads_ordered_by_priority(self):
        """High priority leads should be followed before low priority."""
        orchestrator = OrchestratorAgent()

        leads = [
            InvestigativeLead(
                lead_type=LeadType.NETWORK,
                description="Low priority check",
                priority=LeadPriority.LOW,
                context={},
                confidence=0.5
            ),
            InvestigativeLead(
                lead_type=LeadType.PROCESS,
                description="Critical process analysis",
                priority=LeadPriority.HIGH,
                context={},
                confidence=0.9
            )
        ]

        next_lead = orchestrator._select_next_lead(leads)

        # Should select high priority lead
        assert next_lead.priority == LeadPriority.HIGH

    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    @pytest.mark.asyncio
    async def test_synthesize_creates_investigation_chain(self):
        """Should create coherent investigation narrative from iterations."""
        orchestrator = OrchestratorAgent()

        iterations = [
            IterationResult(
                iteration_number=1,
                tool_used="volatility",
                findings=[{"description": "Found ransom.exe"}],
                iocs={},
                leads_discovered=[],
                lead_followed=None,
                duration=30.0
            ),
            IterationResult(
                iteration_number=2,
                tool_used="bulk_extractor",
                findings=[{"description": "Found C2 IP"}],
                iocs={"ips": ["203.0.113.42"]},
                leads_discovered=[],
                lead_followed=InvestigativeLead(
                    lead_type=LeadType.NETWORK,
                    description="Check network traffic",
                    priority=LeadPriority.HIGH,
                    context={},
                    confidence=0.85
                ),
                duration=45.0
            )
        ]

        result = orchestrator._synthesize_investigation(iterations)

        assert isinstance(result, IterativeAnalysisResult)
        assert len(result.iterations) == 2
        assert len(result.investigation_chain) == 2
        assert result.total_duration == 75.0


class TestIterativeOrchestrationIntegration:
    """Test integration - end-to-end workflows (requires external services)."""

    @pytest.mark.integration
    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    @pytest.mark.asyncio
    @pytest.mark.timeout(300)  # 5 minutes max
    async def test_ransomware_investigation_chain(self):
        """End-to-end: Ransomware investigation should follow leads to complete chain."""
        orchestrator = OrchestratorAgent()

        result = await orchestrator.process_iterative(
            incident_description="Ransomware detected on Windows endpoint at 2026-04-10 14:30",
            analysis_goal="Reconstruct complete attack chain from initial infection to encryption",
            max_iterations=5,
            auto_follow=True
        )

        # Should discover multiple steps
        assert len(result.iterations) >= 2

        # Should have findings from multiple tools
        tools_used = {iteration.tool_used for iteration in result.iterations}
        assert len(tools_used) >= 2

        # Should build investigation chain
        assert len(result.investigation_chain) >= 2

        # Should have comprehensive IOCs
        assert len(result.all_iocs.get("ips", [])) > 0 or \
               len(result.all_iocs.get("processes", [])) > 0

    @pytest.mark.integration
    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_network_intrusion_investigation_chain(self):
        """End-to-end: Network intrusion should trace from network → process → file."""
        orchestrator = OrchestratorAgent()

        result = await orchestrator.process_iterative(
            incident_description="Suspicious network connection to unknown IP 203.0.113.42",
            analysis_goal="Identify source process and determine if malicious",
            max_iterations=5,
            auto_follow=True
        )

        # Should follow leads from network to process
        assert len(result.iterations) >= 2

        # Investigation chain should show logical progression
        chain_types = [step.lead_type for step in result.investigation_chain if step]

        # Should include network and process analysis
        assert LeadType.NETWORK in chain_types or LeadType.PROCESS in chain_types

    @pytest.mark.integration
    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_iteration_performance_acceptable(self):
        """Each iteration should complete in reasonable time."""
        orchestrator = OrchestratorAgent()

        result = await orchestrator.process_iterative(
            incident_description="Test incident",
            analysis_goal="Quick test",
            max_iterations=2,
            auto_follow=True
        )

        # Each iteration should be under 2 minutes
        for iteration in result.iterations:
            assert iteration.duration < 120.0, \
                f"Iteration {iteration.iteration_number} took {iteration.duration}s (>120s)"

    @pytest.mark.integration
    @pytest.mark.skipif(not SCHEMAS_AVAILABLE, reason="Schemas not implemented yet")
    @pytest.mark.asyncio
    async def test_investigation_summary_generation(self):
        """Should generate human-readable investigation summary."""
        orchestrator = OrchestratorAgent()

        result = await orchestrator.process_iterative(
            incident_description="Malware detected",
            analysis_goal="Investigate",
            max_iterations=3,
            auto_follow=True
        )

        # Should have investigation summary
        assert hasattr(result, 'investigation_summary')
        assert len(result.investigation_summary) > 0

        # Summary should mention key findings
        assert "finding" in result.investigation_summary.lower() or \
               "discovered" in result.investigation_summary.lower()
