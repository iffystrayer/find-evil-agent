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
from .schemas import AgentState, ToolSelection, ExecutionResult, AnalysisResult
from .tool_selector import ToolSelectorAgent
from .tool_executor import ToolExecutorAgent
from .analyzer import AnalyzerAgent
from find_evil_agent.telemetry import log_agent_error

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
