"""Orchestrator Agent - LangGraph workflow coordinator.

This agent coordinates the entire DFIR workflow using LangGraph:
1. Tool Selection (ToolSelectorAgent)
2. Tool Execution (ToolExecutorAgent)
3. Analysis (AnalyzerAgent)
4. State aggregation and return

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
from langgraph.graph import StateGraph, END

from .base import BaseAgent, AgentResult, AgentStatus
from .schemas import (
    AgentState,
    ToolSelection,
    ExecutionResult,
    AnalysisResult,
    InvestigativeLead,
    IterationResult,
    IterativeAnalysisResult,
    LeadType,
    LeadPriority,
    Finding,
)
from .tool_selector import ToolSelectorAgent
from .tool_executor import ToolExecutorAgent
from .analyzer import AnalyzerAgent
from find_evil_agent.telemetry import log_agent_error
import time
from datetime import datetime

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

        # Initialize sub-agents
        self.tool_selector = ToolSelectorAgent(llm_provider=self._llm_provider)
        self.tool_executor = ToolExecutorAgent(llm_provider=self._llm_provider)
        self.analyzer = AnalyzerAgent(llm_provider=self._llm_provider)

        # Build workflow
        self.workflow = self._build_workflow()

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

    def _build_workflow(self) -> Any:
        """Build LangGraph workflow.

        Returns:
            Compiled LangGraph workflow
        """
        # Create state graph
        workflow = StateGraph(dict)

        # Add nodes
        workflow.add_node("select_tool", self._select_tool_node)
        workflow.add_node("execute_tool", self._execute_tool_node)
        workflow.add_node("analyze_output", self._analyze_output_node)

        # Define edges
        workflow.set_entry_point("select_tool")
        workflow.add_edge("select_tool", "execute_tool")
        workflow.add_edge("execute_tool", "analyze_output")
        workflow.add_edge("analyze_output", END)

        # Compile workflow
        return workflow.compile()

    async def _select_tool_node(self, state_dict: dict[str, Any]) -> dict[str, Any]:
        """Tool selection node.

        Args:
            state_dict: Workflow state dictionary

        Returns:
            Updated state dictionary
        """
        state: AgentState = state_dict["state"]
        state.current_agent = "tool_selector"
        state.step_count += 1

        agent_logger.debug(
            "workflow_step",
            session_id=state.session_id,
            step=state.step_count,
            agent=state.current_agent
        )

        try:
            # Call ToolSelectorAgent
            result = await self.tool_selector.process({
                "incident_description": state_dict["incident_description"],
                "analysis_goal": state_dict["analysis_goal"]
            })

            if result.success:
                tool_selection = result.data["tool_selection"]
                state.selected_tools.append(tool_selection)

                agent_logger.info(
                    "tool_selected",
                    session_id=state.session_id,
                    tool=tool_selection.tool_name,
                    confidence=tool_selection.confidence
                )
            else:
                agent_logger.warning(
                    "tool_selection_failed",
                    session_id=state.session_id,
                    error=result.error
                )

        except Exception as e:
            agent_logger.error(
                "tool_selection_error",
                session_id=state.session_id,
                error=str(e)
            )

        state_dict["state"] = state
        return state_dict

    async def _execute_tool_node(self, state_dict: dict[str, Any]) -> dict[str, Any]:
        """Tool execution node.

        Args:
            state_dict: Workflow state dictionary

        Returns:
            Updated state dictionary
        """
        state: AgentState = state_dict["state"]
        state.current_agent = "tool_executor"
        state.step_count += 1

        agent_logger.debug(
            "workflow_step",
            session_id=state.session_id,
            step=state.step_count,
            agent=state.current_agent
        )

        # Check if we have a selected tool
        if not state.selected_tools:
            agent_logger.warning(
                "no_tools_selected",
                session_id=state.session_id
            )
            state_dict["state"] = state
            return state_dict

        try:
            # Execute the selected tool
            tool_selection = state.selected_tools[0]  # Use first selected tool

            # Build command from tool selection
            # For now, use a simple command - this would be enhanced based on tool_selection.inputs
            command = self._build_tool_command(tool_selection)

            result = await self.tool_executor.process({
                "tool_name": tool_selection.tool_name,
                "command": command
            })

            if result.success or "execution_result" in result.data:
                exec_result = result.data["execution_result"]
                state.execution_results.append(exec_result)

                agent_logger.info(
                    "tool_executed",
                    session_id=state.session_id,
                    tool=exec_result.tool_name,
                    status=exec_result.status.value,
                    duration=exec_result.execution_time
                )
            else:
                agent_logger.warning(
                    "tool_execution_failed",
                    session_id=state.session_id,
                    error=result.error
                )

        except Exception as e:
            agent_logger.error(
                "tool_execution_error",
                session_id=state.session_id,
                error=str(e)
            )

        state_dict["state"] = state
        return state_dict

    async def _analyze_output_node(self, state_dict: dict[str, Any]) -> dict[str, Any]:
        """Analysis node.

        Args:
            state_dict: Workflow state dictionary

        Returns:
            Updated state dictionary
        """
        state: AgentState = state_dict["state"]
        state.current_agent = "analyzer"
        state.step_count += 1

        agent_logger.debug(
            "workflow_step",
            session_id=state.session_id,
            step=state.step_count,
            agent=state.current_agent
        )

        # Check if we have execution results
        if not state.execution_results:
            agent_logger.warning(
                "no_execution_results",
                session_id=state.session_id
            )
            state_dict["state"] = state
            return state_dict

        try:
            # Analyze each execution result
            for exec_result in state.execution_results:
                result = await self.analyzer.process({
                    "execution_result": exec_result
                })

                if result.success:
                    analysis: AnalysisResult = result.data["analysis_result"]

                    # Add findings to state
                    for finding in analysis.findings:
                        state.findings.append(finding.model_dump())

                    # Add IOCs to state
                    for ioc_type, values in analysis.iocs.items():
                        state.iocs.append({
                            "type": ioc_type,
                            "values": values,
                            "source_tool": exec_result.tool_name
                        })

                    agent_logger.info(
                        "analysis_completed",
                        session_id=state.session_id,
                        tool=exec_result.tool_name,
                        findings=len(analysis.findings),
                        ioc_types=len(analysis.iocs)
                    )
                else:
                    agent_logger.warning(
                        "analysis_failed",
                        session_id=state.session_id,
                        error=result.error
                    )

        except Exception as e:
            agent_logger.error(
                "analysis_error",
                session_id=state.session_id,
                error=str(e)
            )

        state_dict["state"] = state
        return state_dict

    def _build_tool_command(self, tool_selection: ToolSelection) -> str:
        """Build command from tool selection.

        Args:
            tool_selection: Selected tool

        Returns:
            Command string
        """
        # Simple command building - would be enhanced based on tool type
        tool_name = tool_selection.tool_name

        # For demonstration, use basic commands
        if tool_name == "strings":
            return "strings /etc/hostname"
        elif tool_name == "grep":
            return "grep -i error /var/log/syslog 2>/dev/null || echo 'No errors found'"
        elif tool_name in ["volatility", "rekall"]:
            return f"which {tool_name} || echo '{tool_name} not installed'"
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
        max_iterations: int = 5,
        auto_follow: bool = True,
        min_lead_confidence: float = 0.6
    ) -> IterativeAnalysisResult:
        """Execute autonomous iterative analysis workflow.

        Automatically follows investigative leads to build complete attack chain.

        Args:
            incident_description: Description of the incident
            analysis_goal: What to analyze/investigate
            max_iterations: Maximum number of iterations (prevent infinite loops)
            auto_follow: Enable automatic lead following
            min_lead_confidence: Minimum confidence for following leads

        Returns:
            IterativeAnalysisResult with complete investigation chain

        Example:
            >>> result = await agent.process_iterative(
            ...     incident_description="Ransomware detected",
            ...     analysis_goal="Reconstruct complete attack chain",
            ...     max_iterations=5,
            ...     auto_follow=True
            ... )
            >>> len(result.iterations)
            3
            >>> result.investigation_chain
            [InvestigativeLead(...), InvestigativeLead(...)]
        """
        session_id = str(uuid4())
        iterations = []
        investigation_chain = []
        all_findings = []
        all_iocs = {}
        total_start_time = time.time()

        agent_logger.info(
            "iterative_analysis_started",
            session_id=session_id,
            max_iterations=max_iterations,
            auto_follow=auto_follow
        )

        try:
            # Iteration context starts with user's request
            current_goal = analysis_goal
            current_context = {}
            lead_followed = None

            for iteration_num in range(1, max_iterations + 1):
                iteration_start_time = time.time()

                agent_logger.info(
                    "iteration_started",
                    session_id=session_id,
                    iteration=iteration_num,
                    goal=current_goal[:100]
                )

                # Run single analysis iteration
                result = await self.process({
                    "incident_description": incident_description,
                    "analysis_goal": current_goal
                })

                if not result.success:
                    agent_logger.warning(
                        "iteration_failed",
                        session_id=session_id,
                        iteration=iteration_num,
                        error=result.error
                    )
                    break

                # Extract results from iteration
                state = result.data["state"]
                iteration_findings = [Finding(**f) for f in state.findings]
                iteration_iocs = self._merge_iocs(state.iocs)

                # Extract investigative leads
                leads = await self._extract_leads(
                    findings=[f.model_dump() for f in iteration_findings],
                    iocs=iteration_iocs,
                    iteration_number=iteration_num
                )

                iteration_duration = time.time() - iteration_start_time

                # Create iteration result
                iteration_result = IterationResult(
                    iteration_number=iteration_num,
                    tool_used=state.selected_tools[0].tool_name if state.selected_tools else "none",
                    tool_selection=state.selected_tools[0] if state.selected_tools else None,
                    execution_result=state.execution_results[0] if state.execution_results else None,
                    findings=iteration_findings,
                    iocs=iteration_iocs,
                    leads_discovered=leads,
                    lead_followed=lead_followed,
                    duration=iteration_duration
                )

                iterations.append(iteration_result)
                all_findings.extend(iteration_findings)
                all_iocs = self._merge_iocs_dict(all_iocs, iteration_iocs)

                agent_logger.info(
                    "iteration_completed",
                    session_id=session_id,
                    iteration=iteration_num,
                    findings=len(iteration_findings),
                    iocs=len(iteration_iocs),
                    leads=len(leads),
                    duration=iteration_duration
                )

                # Check if we should continue
                if not self._should_continue(
                    iteration_num=iteration_num,
                    max_iterations=max_iterations,
                    auto_follow=auto_follow,
                    leads=leads,
                    min_confidence=min_lead_confidence
                ):
                    stopping_reason = self._get_stopping_reason(
                        iteration_num, max_iterations, leads, auto_follow
                    )
                    agent_logger.info(
                        "iteration_stopped",
                        session_id=session_id,
                        reason=stopping_reason
                    )
                    break

                # Select next lead to follow
                next_lead = self._select_next_lead(leads)
                if not next_lead:
                    break

                # Update context for next iteration
                current_goal = self._create_follow_up_goal(next_lead, iteration_findings)
                current_context = next_lead.context
                lead_followed = next_lead
                investigation_chain.append(next_lead)

                agent_logger.debug(
                    "following_lead",
                    session_id=session_id,
                    lead_type=next_lead.lead_type.value,
                    lead_description=next_lead.description[:100]
                )

            # Synthesize final results
            total_duration = time.time() - total_start_time
            result = self._synthesize_investigation(
                session_id=session_id,
                incident_description=incident_description,
                analysis_goal=analysis_goal,
                iterations=iterations,
                investigation_chain=investigation_chain,
                all_findings=all_findings,
                all_iocs=all_iocs,
                total_duration=total_duration
            )

            agent_logger.info(
                "iterative_analysis_completed",
                session_id=session_id,
                total_iterations=len(iterations),
                total_findings=len(all_findings),
                total_duration=total_duration
            )

            return result

        except Exception as e:
            log_agent_error(
                agent_name=self.name,
                error_type="iterative_analysis_error",
                error_message=str(e)
            )

            # Return partial results if available
            return IterativeAnalysisResult(
                session_id=session_id,
                incident_description=incident_description,
                analysis_goal=analysis_goal,
                iterations=iterations,
                investigation_chain=investigation_chain,
                all_findings=all_findings,
                all_iocs=all_iocs,
                total_duration=time.time() - total_start_time,
                stopping_reason=f"Error: {e}",
                investigation_summary="Investigation interrupted by error"
            )

    async def _extract_leads(
        self,
        findings: list[dict[str, Any]],
        iocs: dict[str, list[str]],
        iteration_number: int
    ) -> list[InvestigativeLead]:
        """Extract investigative leads from findings and IOCs.

        Uses LLM to identify potential next steps in the investigation.

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

        # Build prompt for LLM
        prompt = self._build_lead_extraction_prompt(findings, iocs, iteration_number)

        try:
            # Use LLM to extract leads
            response = await self.llm.generate(prompt)

            # Parse LLM response into leads
            leads = self._parse_leads_from_response(response, findings, iocs)

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
            # Fallback: simple rule-based lead extraction
            return self._extract_leads_fallback(findings, iocs)

    def _build_lead_extraction_prompt(
        self,
        findings: list[dict[str, Any]],
        iocs: dict[str, list[str]],
        iteration_number: int
    ) -> str:
        """Build LLM prompt for lead extraction."""
        findings_text = "\n".join([
            f"- {f.get('description', 'N/A')} (Severity: {f.get('severity', 'unknown')})"
            for f in findings[:5]  # Limit to first 5
        ])

        iocs_text = "\n".join([
            f"- {ioc_type}: {', '.join(values[:3])}"  # First 3 of each type
            for ioc_type, values in iocs.items()
            if values
        ])

        return f"""You are a DFIR expert analyzing investigation findings. Based on the current findings and IOCs, identify the next investigative steps.

Current Findings:
{findings_text or "No findings yet"}

Current IOCs:
{iocs_text or "No IOCs yet"}

Iteration: {iteration_number}

Identify 1-3 investigative leads that would help build a complete attack chain. For each lead, provide:
1. Lead type (process/network/file/timeline/registry)
2. Clear description of what to investigate
3. Priority (high/medium/low)
4. Suggested tool (if applicable)
5. Confidence (0.0-1.0) that this lead is worth following

Focus on leads that would:
- Identify the initial infection vector
- Trace network communication (C2 servers)
- Identify malicious processes or files
- Build a timeline of events
- Uncover persistence mechanisms

Respond in this format (one lead per line):
LEAD: <type> | <priority> | <confidence> | <suggested_tool or none> | <description>

Example:
LEAD: network | high | 0.9 | bulk_extractor | Analyze network traffic to identify C2 server communication from suspicious process
"""

    def _parse_leads_from_response(
        self,
        response: str,
        findings: list[dict[str, Any]],
        iocs: dict[str, list[str]]
    ) -> list[InvestigativeLead]:
        """Parse LLM response into InvestigativeLead objects."""
        leads = []

        for line in response.split('\n'):
            if not line.strip().startswith('LEAD:'):
                continue

            try:
                # Parse: LEAD: <type> | <priority> | <confidence> | <tool> | <description>
                parts = line.replace('LEAD:', '').split('|')
                if len(parts) < 5:
                    continue

                lead_type_str = parts[0].strip().lower()
                priority_str = parts[1].strip().lower()
                confidence = float(parts[2].strip())
                suggested_tool = parts[3].strip() if parts[3].strip() != 'none' else None
                description = parts[4].strip()

                # Map strings to enums
                lead_type = LeadType(lead_type_str) if lead_type_str in [t.value for t in LeadType] else LeadType.PROCESS
                priority = LeadPriority(priority_str) if priority_str in [p.value for p in LeadPriority] else LeadPriority.MEDIUM

                # Build context from IOCs
                context = {
                    "findings_count": len(findings),
                    "ioc_types": list(iocs.keys())
                }

                lead = InvestigativeLead(
                    lead_type=lead_type,
                    description=description,
                    priority=priority,
                    suggested_tool=suggested_tool,
                    context=context,
                    confidence=confidence,
                    reasoning="LLM-generated lead based on current findings"
                )

                leads.append(lead)

            except Exception as e:
                agent_logger.debug("failed_to_parse_lead", line=line, error=str(e))
                continue

        # Sort by priority and confidence
        leads.sort(key=lambda l: (
            0 if l.priority == LeadPriority.HIGH else 1 if l.priority == LeadPriority.MEDIUM else 2,
            -l.confidence
        ))

        return leads

    def _extract_leads_fallback(
        self,
        findings: list[dict[str, Any]],
        iocs: dict[str, list[str]]
    ) -> list[InvestigativeLead]:
        """Fallback rule-based lead extraction when LLM fails."""
        leads = []

        # If we found processes, suggest network analysis
        if iocs.get("processes"):
            leads.append(InvestigativeLead(
                lead_type=LeadType.NETWORK,
                description="Analyze network activity for suspicious processes",
                priority=LeadPriority.HIGH,
                suggested_tool="bulk_extractor",
                context={"processes": iocs["processes"][:3]},
                confidence=0.75,
                reasoning="Processes found, network analysis is logical next step"
            ))

        # If we found IPs/domains, suggest timeline
        if iocs.get("ips") or iocs.get("domains"):
            leads.append(InvestigativeLead(
                lead_type=LeadType.TIMELINE,
                description="Build timeline to identify when IOCs first appeared",
                priority=LeadPriority.MEDIUM,
                suggested_tool="log2timeline",
                context={"iocs": {k: v for k, v in iocs.items() if v}},
                confidence=0.7,
                reasoning="IOCs found, timeline helps establish attack sequence"
            ))

        return leads

    def _select_next_lead(self, leads: list[InvestigativeLead]) -> InvestigativeLead | None:
        """Select the next lead to follow.

        Args:
            leads: List of available leads

        Returns:
            Lead to follow, or None if no suitable lead
        """
        if not leads:
            return None

        # Leads are already sorted by priority and confidence
        # Return the first (highest priority, highest confidence)
        return leads[0]

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
