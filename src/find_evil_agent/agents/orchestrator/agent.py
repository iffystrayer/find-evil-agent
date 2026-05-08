"""Orchestrator Agent - LangGraph workflow coordinator.

This agent coordinates the entire DFIR workflow using LangGraph:
1. Tool Selection (ToolSelectorAgent)
2. Tool Execution (ToolExecutorAgent)
3. Analysis (AnalyzerAgent)
4. State aggregation and return

Workflow building extracted to orchestrator/workflows.py (C3c refactor).
Prompting logic extracted to orchestrator/prompting.py (C3c refactor).

Example:
    >>> agent = OrchestratorAgent()
    >>> result = await agent.process({
    ...     "incident_description": "Ransomware detected",
    ...     "analysis_goal": "Identify malicious processes"
    ... })
    >>> state = result.data['state']
    >>> state.selected_tools
    [ToolSelection(tool_name='volatility', ...)]
"""

from typing import Any
from uuid import uuid4
import structlog

from ..base import BaseAgent, AgentResult, AgentStatus
from ..schemas import (
    AgentState,
    ToolSelection,
    InvestigativeLead,
    LeadPriority,
    IterationResult,
    IterativeAnalysisResult,
    Finding,
)
from ..tool_selector import ToolSelectorAgent
from ..tool_executor import ToolExecutorAgent
from ..analyzer import AnalyzerAgent
from ..command_builder import DynamicCommandBuilder
from find_evil_agent.config.settings import get_settings
from find_evil_agent.telemetry import log_agent_error

# Import workflow builders and prompting helpers (C3c refactor)
from .workflows import build_workflow, build_iterative_workflow
from .prompting import (
    build_lead_extraction_prompt,
    parse_leads_from_response,
    extract_leads_fallback
)

agent_logger = structlog.get_logger()


class OrchestratorAgent(BaseAgent):
    """Coordinates DFIR workflow using LangGraph.

    Workflow:
        START
          ↓
        Tool Selection (ToolSelectorAgent)
          ↓
        Tool Execution (ToolExecutorAgent)
          ↓
        Analysis (AnalyzerAgent)
          ↓
        END (Return AgentState)

    Key Features:
    - LangGraph state machine for workflow control
    - Automatic state management
    - Graceful error handling
    - Step tracking and logging
    - Session ID for tracing

    Attributes:
        tool_selector: ToolSelectorAgent instance
        tool_executor: ToolExecutorAgent instance
        analyzer: AnalyzerAgent instance
        workflow: Compiled LangGraph workflow
    """

    def __init__(self, **kwargs):
        """Initialize Orchestrator Agent.

        Args:
            **kwargs: Passed to BaseAgent
        """
        super().__init__(name="orchestrator", **kwargs)

        # Initialize LLM provider before creating sub-agents
        llm = self.llm  # Trigger lazy initialization

        # Initialize sub-agents with LLM provider
        self.tool_selector = ToolSelectorAgent(llm_provider=llm)
        self.tool_executor = ToolExecutorAgent(llm_provider=llm)
        self.analyzer = AnalyzerAgent(llm_provider=llm)

        # Initialize command builder with LLM provider
        self.command_builder = DynamicCommandBuilder(
            llm_router=llm,
            metadata_path="tools/metadata.yaml"
        )

        # Build workflows using extracted builders (C3c refactor)
        self.workflow = build_workflow(
            tool_selector=self.tool_selector,
            tool_executor=self.tool_executor,
            analyzer=self.analyzer,
            command_builder=self.command_builder
        )
        self.iterative_workflow = build_iterative_workflow(
            orchestrator_process_method=self.process,
            extract_leads_method=self._extract_leads,
            select_next_lead_method=self._select_next_lead,
            create_follow_up_goal_method=self._create_follow_up_goal,
            merge_iocs_method=self._merge_iocs
        )

        agent_logger.info("orchestrator_initialized")

    async def process(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute DFIR workflow.

        Args:
            input_data: Dict with keys:
                - incident_description: str (description of incident)
                - analysis_goal: str (what to analyze)

        Returns:
            AgentResult with:
                - success: True if workflow completed
                - data: {"state": AgentState, "summary": str}
                - status: SUCCESS or FAILED

        Example:
            >>> result = await agent.process({
            ...     "incident_description": "Ransomware detected",
            ...     "analysis_goal": "Find malicious processes"
            ... })
            >>> result.success
            True
        """
        try:
            # Validate input
            if not await self.validate(input_data):
                return AgentResult(
                    success=False,
                    data={},
                    status=AgentStatus.FAILED,
                    error="Invalid input: incident_description and analysis_goal required"
                )

            # Initialize state
            state = AgentState(
                session_id=str(uuid4()),
                incident_description=input_data["incident_description"],
                selected_tools=[],
                execution_results=[],
                findings=[],
                timeline=[],
                iocs=[],
                current_agent=None,
                step_count=0
            )

            agent_logger.info(
                "workflow_started",
                session_id=state.session_id,
                incident=input_data["incident_description"][:50],
                goal=input_data["analysis_goal"][:50]
            )

            # Execute workflow
            final_state = await self.workflow.ainvoke({
                "state": state,
                "incident_description": input_data["incident_description"],
                "analysis_goal": input_data["analysis_goal"]
            })

            # Extract final state
            result_state = final_state.get("state", state)

            # Generate summary
            summary = self._generate_summary(result_state)

            agent_logger.info(
                "workflow_completed",
                session_id=result_state.session_id,
                steps=result_state.step_count,
                findings=len(result_state.findings),
                tools_used=len(result_state.selected_tools)
            )

            return AgentResult(
                success=True,
                data={
                    "state": result_state,
                    "summary": summary
                },
                status=AgentStatus.SUCCESS,
                confidence=self._calculate_confidence(result_state)
            )

        except Exception as e:
            log_agent_error(
                agent_name=self.name,
                error_type="workflow_error",
                error_message=str(e)
            )

            return AgentResult(
                success=False,
                data={},
                status=AgentStatus.FAILED,
                error=f"Workflow failed: {e}"
            )

    async def validate(self, input_data: dict[str, Any]) -> bool:
        """Validate input data.

        Args:
            input_data: Input dict to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["incident_description", "analysis_goal"]
        for field in required_fields:
            if field not in input_data or not input_data[field]:
                return False
        return True

    def _build_tool_command(self, tool_selection: ToolSelection) -> str:
        """DEPRECATED: Build command from tool selection.

        This method has been replaced by DynamicCommandBuilder which uses
        LLM and tool metadata to construct proper commands.

        Args:
            tool_selection: Selected tool

        Returns:
            Command string

        Note:
            This method is kept for backward compatibility only.
            Use self.command_builder.build_command() instead.
        """
        # DEPRECATED: Replaced by DynamicCommandBuilder
        agent_logger.warning(
            "deprecated_method",
            method="_build_tool_command",
            replacement="DynamicCommandBuilder.build_command"
        )

        tool_name = tool_selection.tool_name
        # Fallback hardcoded commands (should not be used)
        if tool_name == "strings":
            return "strings /etc/hostname"
        elif tool_name == "grep":
            return "grep -i error /var/log/syslog 2>/dev/null || echo 'No errors found'"
        else:
            return f"which {tool_name} || echo '{tool_name} not found'"

    def _generate_summary(self, state: AgentState) -> str:
        """Generate workflow summary.

        Args:
            state: Final workflow state

        Returns:
            Summary string
        """
        parts = []

        parts.append(f"Session: {state.session_id}")
        parts.append(f"Steps: {state.step_count}")

        if state.selected_tools:
            tools = ", ".join([t.tool_name for t in state.selected_tools])
            parts.append(f"Tools: {tools}")

        if state.findings:
            parts.append(f"Findings: {len(state.findings)}")

        if state.iocs:
            parts.append(f"IOC types: {len(state.iocs)}")

        return " | ".join(parts)

    def _calculate_confidence(self, state: AgentState) -> float:
        """Calculate overall workflow confidence.

        Args:
            state: Final workflow state

        Returns:
            Confidence score
        """
        if not state.selected_tools:
            return 0.3

        # Average tool selection confidence
        tool_confidence = sum(t.confidence for t in state.selected_tools) / len(state.selected_tools)

        # Adjust based on findings
        if state.findings:
            return min(tool_confidence + 0.1, 1.0)

        return tool_confidence

    # ============================================================================
    # Iterative Analysis Methods (Autonomous Investigation)
    # ============================================================================

    async def process_iterative(
        self,
        incident_description: str,
        analysis_goal: str,
        max_iterations: int | None = None,
        auto_follow: bool = True,
        min_lead_confidence: float | None = None,
        session_id: str | None = None
    ) -> IterativeAnalysisResult:

        settings = get_settings()
        if max_iterations is None:
            max_iterations = settings.orchestrator_max_iterations
        if min_lead_confidence is None:
            min_lead_confidence = settings.orchestrator_min_lead_confidence

        config = {}
        if not session_id:
            session_id = str(uuid4())
            state = AgentState(
                session_id=session_id,
                incident_description=incident_description,
                analysis_goal=analysis_goal,
                max_iterations=max_iterations,
                current_goal=analysis_goal
            )
            state_dict = {"state": state}
        else:
            state_dict = None
            
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            # Step the graph
            final_state = await self.iterative_workflow.ainvoke(state_dict, config)
            
            # Check if interrupted
            state_info = self.iterative_workflow.get_state(config)
            is_interrupted = len(state_info.next) > 0 and "human_approval_gateway" in state_info.next
            
            result_state = final_state.get("state") if final_state else state_info.values.get("state")
            if isinstance(result_state, dict):
                result_state = AgentState(**result_state)
            
            all_findings = [Finding(**f) for f in result_state.findings]
            
            # Reconstruct IOCs
            all_iocs = {}
            for ioc_entry in result_state.iocs:
                typ = ioc_entry["type"]
                all_iocs.setdefault(typ, []).extend(ioc_entry["values"])
                
            iterations = [IterationResult(**i) for i in result_state.iterations]
            chain = [InvestigativeLead(**l) for l in result_state.investigation_chain]
            
            # If interrupted, set stopping_reason to indicate
            stopping_reason = "Waiting for Human Approval" if is_interrupted else result_state.stopping_reason
            
            return IterativeAnalysisResult(
                session_id=session_id,
                incident_description=result_state.incident_description or incident_description,
                analysis_goal=result_state.analysis_goal or analysis_goal,
                iterations=iterations,
                investigation_chain=chain,
                all_findings=all_findings,
                all_iocs=all_iocs,
                total_duration=result_state.total_duration,
                stopping_reason=stopping_reason,
                investigation_summary="Pending..." if is_interrupted else "Investigation complete"
            )
            
        except Exception as e:
            agent_logger.error("iterative_analysis_error", error=str(e))
            return IterativeAnalysisResult(
                session_id=session_id,
                incident_description=incident_description,
                analysis_goal=analysis_goal,
                stopping_reason=f"Error: {e}"
            )

    async def _extract_leads(
        self,
        findings: list[dict[str, Any]],
        iocs: dict[str, list[str]],
        iteration_number: int
    ) -> list[InvestigativeLead]:
        """Extract investigative leads from findings and IOCs.

        Uses LLM to identify potential next steps in the investigation.
        Delegates to prompting helpers extracted in C3c refactor.

        Args:
            findings: List of findings from current iteration
            iocs: IOCs extracted from current iteration
            iteration_number: Current iteration number

        Returns:
            List of investigative leads ordered by priority

        Example:
            >>> leads = await agent._extract_leads(
            ...     findings=[{"description": "Malicious process found"}],
            ...     iocs={"processes": ["ransom.exe"]},
            ...     iteration_number=1
            ... )
            >>> leads[0].lead_type
            LeadType.NETWORK
        """
        if not findings and not iocs:
            return []

        # Build prompt using extracted helper (C3c refactor)
        prompt = build_lead_extraction_prompt(findings, iocs, iteration_number)

        try:
            # Use LLM to extract leads
            response = await self.llm.generate(prompt)

            # Parse LLM response using extracted helper (C3c refactor)
            leads = parse_leads_from_response(response, findings, iocs)

            agent_logger.debug(
                "leads_extracted",
                iteration=iteration_number,
                num_leads=len(leads)
            )

            return leads

        except Exception as e:
            agent_logger.warning(
                "lead_extraction_failed",
                iteration=iteration_number,
                error=str(e)
            )
            # Fallback using extracted helper (C3c refactor)
            return extract_leads_fallback(findings, iocs)

    def _select_next_lead(self, leads: list[InvestigativeLead]) -> InvestigativeLead | None:
        """Select the next lead to follow.

        Selects the lead with highest priority, then highest confidence.

        Args:
            leads: List of available leads (will be sorted)

        Returns:
            Lead to follow, or None if no suitable lead
        """
        if not leads:
            return None

        # Sort by priority (high first) then by confidence (high first)
        sorted_leads = sorted(leads, key=lambda l: (
            0 if l.priority == LeadPriority.HIGH else 1 if l.priority == LeadPriority.MEDIUM else 2,
            -l.confidence  # Negative for descending order
        ))

        # Return the first (highest priority, highest confidence)
        return sorted_leads[0]

    def _should_continue(
        self,
        iteration_num: int,
        max_iterations: int,
        auto_follow: bool,
        leads: list[InvestigativeLead],
        min_confidence: float
    ) -> bool:
        """Determine if investigation should continue.

        Args:
            iteration_num: Current iteration number
            max_iterations: Maximum allowed iterations
            auto_follow: Whether auto-follow is enabled
            leads: Available leads
            min_confidence: Minimum confidence threshold

        Returns:
            True if should continue, False otherwise
        """
        # Check max iterations
        if iteration_num >= max_iterations:
            return False

        # Check auto-follow disabled
        if not auto_follow:
            return False

        # Check no leads available
        if not leads:
            return False

        # Check all leads below confidence threshold
        if all(lead.confidence < min_confidence for lead in leads):
            return False

        return True

    def _get_stopping_reason(
        self,
        iteration_num: int,
        max_iterations: int,
        leads: list[InvestigativeLead],
        auto_follow: bool
    ) -> str:
        """Get human-readable stopping reason."""
        if iteration_num >= max_iterations:
            return f"Maximum iterations reached ({max_iterations})"
        elif not auto_follow:
            return "Auto-follow disabled (manual mode)"
        elif not leads:
            return "No investigative leads discovered"
        else:
            return "All leads below confidence threshold"

    def _create_follow_up_goal(
        self,
        lead: InvestigativeLead,
        previous_findings: list[Finding]
    ) -> str:
        """Create analysis goal for following a lead.

        Args:
            lead: Lead to follow
            previous_findings: Findings from previous iteration

        Returns:
            Analysis goal string for next iteration
        """
        # Combine lead description with context from previous findings
        goal = lead.description

        # Add context if critical findings exist
        critical_findings = [f for f in previous_findings if f.severity.value == "critical"]
        if critical_findings:
            context = f" Focus on: {critical_findings[0].description[:100]}"
            goal = goal + "." + context

        return goal

    def _synthesize_investigation(
        self,
        session_id: str,
        incident_description: str,
        analysis_goal: str,
        iterations: list[IterationResult],
        investigation_chain: list[InvestigativeLead],
        all_findings: list[Finding],
        all_iocs: dict[str, list[str]],
        total_duration: float
    ) -> IterativeAnalysisResult:
        """Synthesize complete investigation results.

        Args:
            session_id: Session identifier
            incident_description: Original incident
            analysis_goal: Original goal
            iterations: All iteration results
            investigation_chain: Chain of leads followed
            all_findings: All findings from all iterations
            all_iocs: All IOCs from all iterations
            total_duration: Total time spent

        Returns:
            Complete iterative analysis result
        """
        # Generate investigation summary
        summary_parts = []
        summary_parts.append(f"Completed {len(iterations)} iteration(s) of autonomous analysis.")

        tools_used = list({it.tool_used for it in iterations if it.tool_used != "none"})
        if tools_used:
            summary_parts.append(f"Tools used: {', '.join(tools_used)}.")

        summary_parts.append(f"Discovered {len(all_findings)} finding(s) across all iterations.")

        if investigation_chain:
            summary_parts.append(
                f"Investigation chain: {' → '.join([lead.lead_type.value for lead in investigation_chain])}."
            )

        investigation_summary = " ".join(summary_parts)

        # Determine stopping reason
        last_iteration = iterations[-1] if iterations else None
        if last_iteration and not last_iteration.leads_discovered:
            stopping_reason = "No further investigative leads discovered"
        elif len(iterations) >= 5:
            stopping_reason = "Maximum iterations reached"
        else:
            stopping_reason = "Investigation complete"

        return IterativeAnalysisResult(
            session_id=session_id,
            incident_description=incident_description,
            analysis_goal=analysis_goal,
            iterations=iterations,
            investigation_chain=investigation_chain,
            all_findings=all_findings,
            all_iocs=all_iocs,
            total_duration=total_duration,
            stopping_reason=stopping_reason,
            investigation_summary=investigation_summary
        )

    def _merge_iocs(self, ioc_list: list[dict[str, Any]]) -> dict[str, list[str]]:
        """Merge IOC list from state into dict format.

        Args:
            ioc_list: List of IOC dicts from state

        Returns:
            Merged IOC dict
        """
        merged = {}
        for ioc_entry in ioc_list:
            ioc_type = ioc_entry.get("type", "unknown")
            values = ioc_entry.get("values", [])
            if ioc_type not in merged:
                merged[ioc_type] = []
            merged[ioc_type].extend(values)

        # Deduplicate
        for ioc_type in merged:
            merged[ioc_type] = list(set(merged[ioc_type]))

        return merged

    def _merge_iocs_dict(
        self,
        dict1: dict[str, list[str]],
        dict2: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        """Merge two IOC dictionaries.

        Args:
            dict1: First IOC dict
            dict2: Second IOC dict

        Returns:
            Merged IOC dict with deduplicated values
        """
        merged = dict1.copy()
        for ioc_type, values in dict2.items():
            if ioc_type not in merged:
                merged[ioc_type] = []
            merged[ioc_type].extend(values)
            # Deduplicate
            merged[ioc_type] = list(set(merged[ioc_type]))

        return merged
