"""Workflow builders for orchestrator LangGraph workflows.

Extracted from orchestrator.py (C3c refactor).

Functions:
- build_workflow: Build standard 3-step workflow (select → execute → analyze)
- build_iterative_workflow: Build iterative investigation workflow with HITL
"""

from typing import Any
import time
import structlog
from langgraph.graph import StateGraph, END

from ..checkpointer import get_checkpointer
from ..schemas import (
    AgentState,
    ToolSelection,
    ExecutionResult,
    AnalysisResult,
    InvestigativeLead,
    IterationResult,
    Finding,
)
from ..tool_selector import ToolSelectorAgent
from ..tool_executor import ToolExecutorAgent
from ..analyzer import AnalyzerAgent
from ..command_builder import DynamicCommandBuilder

logger = structlog.get_logger()


def build_workflow(
    tool_selector: ToolSelectorAgent,
    tool_executor: ToolExecutorAgent,
    analyzer: AnalyzerAgent,
    command_builder: DynamicCommandBuilder
) -> Any:
    """Build LangGraph workflow for standard 3-step analysis.

    Creates workflow: select_tool → execute_tool → analyze_output → END

    Args:
        tool_selector: ToolSelectorAgent instance
        tool_executor: ToolExecutorAgent instance
        analyzer: AnalyzerAgent instance
        command_builder: DynamicCommandBuilder instance

    Returns:
        Compiled LangGraph workflow
    """
    # Create state graph
    workflow = StateGraph(dict)

    # Define node closures that capture dependencies
    async def select_tool_node(state_dict: dict[str, Any]) -> dict[str, Any]:
        """Tool selection node."""
        state = state_dict["state"]
        if isinstance(state, dict):
            state = AgentState(**state)
        state.current_agent = "tool_selector"
        state.step_count += 1

        logger.debug(
            "workflow_step",
            session_id=state.session_id,
            step=state.step_count,
            agent=state.current_agent
        )

        try:
            # Call ToolSelectorAgent
            result = await tool_selector.process({
                "incident_description": state_dict["incident_description"],
                "analysis_goal": state_dict["analysis_goal"]
            })

            if result.success:
                tool_selection = result.data["tool_selection"]
                state.selected_tools.append(tool_selection)

                logger.info(
                    "tool_selected",
                    session_id=state.session_id,
                    tool=tool_selection.tool_name,
                    confidence=tool_selection.confidence
                )
            else:
                logger.warning(
                    "tool_selection_failed",
                    session_id=state.session_id,
                    error=result.error
                )

        except Exception as e:
            logger.error(
                "tool_selection_error",
                session_id=state.session_id,
                error=str(e)
            )

        state_dict["state"] = state
        return state_dict

    async def execute_tool_node(state_dict: dict[str, Any]) -> dict[str, Any]:
        """Tool execution node."""
        state = state_dict["state"]
        if isinstance(state, dict):
            state = AgentState(**state)
        state.current_agent = "tool_executor"
        state.step_count += 1

        logger.debug(
            "workflow_step",
            session_id=state.session_id,
            step=state.step_count,
            agent=state.current_agent
        )

        # Check if we have a selected tool
        if not state.selected_tools:
            logger.warning(
                "no_tools_selected",
                session_id=state.session_id
            )
            state_dict["state"] = state
            return state_dict

        try:
            # Execute the selected tool
            tool_selection = state.selected_tools[0]  # Use first selected tool

            # Build command dynamically using LLM and metadata
            context = {
                "incident": state.incident_description,
                "goal": state.analysis_goal,
                "evidence_paths": getattr(state, "evidence_paths", [])
            }
            command = await command_builder.build_command(tool_selection, context)

            result = await tool_executor.process({
                "tool_name": tool_selection.tool_name,
                "command": command
            })

            if result.success or "execution_result" in result.data:
                exec_result = result.data["execution_result"]
                state.execution_results.append(exec_result)

                logger.info(
                    "tool_executed",
                    session_id=state.session_id,
                    tool=exec_result.tool_name,
                    status=exec_result.status.value,
                    duration=exec_result.execution_time
                )
            else:
                logger.warning(
                    "tool_execution_failed",
                    session_id=state.session_id,
                    error=result.error
                )

        except Exception as e:
            logger.error(
                "tool_execution_error",
                session_id=state.session_id,
                error=str(e)
            )

        state_dict["state"] = state
        return state_dict

    async def analyze_output_node(state_dict: dict[str, Any]) -> dict[str, Any]:
        """Analysis node."""
        state = state_dict["state"]
        if isinstance(state, dict):
            state = AgentState(**state)
        state.current_agent = "analyzer"
        state.step_count += 1

        logger.debug(
            "workflow_step",
            session_id=state.session_id,
            step=state.step_count,
            agent=state.current_agent
        )

        # Check if we have execution results
        if not state.execution_results:
            logger.warning(
                "no_execution_results",
                session_id=state.session_id
            )
            state_dict["state"] = state
            return state_dict

        try:
            # Analyze each execution result
            for exec_result in state.execution_results:
                result = await analyzer.process({
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

                    logger.info(
                        "analysis_completed",
                        session_id=state.session_id,
                        tool=exec_result.tool_name,
                        findings=len(analysis.findings),
                        ioc_types=len(analysis.iocs)
                    )
                else:
                    logger.warning(
                        "analysis_failed",
                        session_id=state.session_id,
                        error=result.error
                    )

        except Exception as e:
            logger.error(
                "analysis_error",
                session_id=state.session_id,
                error=str(e)
            )

        state_dict["state"] = state
        return state_dict

    # Add nodes
    workflow.add_node("select_tool", select_tool_node)
    workflow.add_node("execute_tool", execute_tool_node)
    workflow.add_node("analyze_output", analyze_output_node)

    # Define edges
    workflow.set_entry_point("select_tool")
    workflow.add_edge("select_tool", "execute_tool")
    workflow.add_edge("execute_tool", "analyze_output")
    workflow.add_edge("analyze_output", END)

    # Compile workflow
    return workflow.compile()


def build_iterative_workflow(
    orchestrator_process_method: Any,  # Callable for single-iteration process
    extract_leads_method: Any,  # Callable for lead extraction
    select_next_lead_method: Any,  # Callable for lead selection
    create_follow_up_goal_method: Any,  # Callable for goal creation
    merge_iocs_method: Any  # Callable for IOC merging
) -> Any:
    """Build LangGraph workflow for iterative autonomous investigation.

    Creates workflow with: process_iteration → extract_leads → [human_approval_gateway] → loop

    Args:
        orchestrator_process_method: Method to run single iteration (self.process)
        extract_leads_method: Method to extract leads (self._extract_leads)
        select_next_lead_method: Method to select next lead (self._select_next_lead)
        create_follow_up_goal_method: Method to create follow-up goal (self._create_follow_up_goal)
        merge_iocs_method: Method to merge IOCs (self._merge_iocs)

    Returns:
        Compiled LangGraph workflow with checkpointer and HITL interrupt
    """
    workflow = StateGraph(dict)

    async def process_iteration_node(state_dict: dict[str, Any]) -> dict[str, Any]:
        """Process one iteration of investigation."""
        state = state_dict["state"]
        if isinstance(state, dict):
            state = AgentState(**state)

        # Determine the goal for this iteration
        current_goal = state.current_goal or state.analysis_goal

        logger.info("iteration_started", session_id=state.session_id, iteration=state.step_count+1)
        start_t = time.time()

        # Run standard process (tool selection -> execution -> analysis) as a sub-call
        result = await orchestrator_process_method({
            "incident_description": state.incident_description,
            "analysis_goal": current_goal
        })

        if not result.success:
            state.stopping_reason = f"Iteration error: {result.error}"
            state_dict["state"] = state
            return state_dict

        inner_state = result.data["state"]
        iteration_findings = [Finding(**f) for f in inner_state.findings]
        iteration_iocs = merge_iocs_method(inner_state.iocs)

        duration = time.time() - start_t
        state.total_duration += duration
        state.step_count += 1

        it_res = IterationResult(
            iteration_number=state.step_count,
            tool_used=inner_state.selected_tools[0].tool_name if inner_state.selected_tools else "none",
            tool_selection=inner_state.selected_tools[0] if inner_state.selected_tools else None,
            execution_result=inner_state.execution_results[0] if inner_state.execution_results else None,
            findings=iteration_findings,
            iocs=iteration_iocs,
            duration=duration
        )

        state.iterations.append(it_res.model_dump())
        state.findings.extend(inner_state.findings)

        # Merge IOC dicts
        merged_iocs = {}
        # Load existing
        for ioc_entry in state.iocs:
            typ = ioc_entry["type"]
            vals = ioc_entry["values"]
            merged_iocs.setdefault(typ, []).extend(vals)

        for k, v in iteration_iocs.items():
            merged_iocs.setdefault(k, []).extend(v)

        # Push back into State IOCs format
        state.iocs = [{"type": k, "values": list(set(v)), "source_tool": "iterative"} for k, v in merged_iocs.items()]

        state_dict["state"] = state
        return state_dict

    async def extract_leads_node(state_dict: dict[str, Any]) -> dict[str, Any]:
        """Extract investigative leads from iteration results."""
        state = state_dict["state"]
        if isinstance(state, dict):
            state = AgentState(**state)
        if state.stopping_reason:
            return state_dict

        # Get latest iteration
        if not state.iterations:
            return state_dict

        last_it = IterationResult(**state.iterations[-1])

        leads = await extract_leads_method(
            findings=[f.model_dump() for f in last_it.findings],
            iocs=last_it.iocs,
            iteration_number=state.step_count
        )
        last_it.leads_discovered = leads
        state.iterations[-1] = last_it.model_dump()

        # Check stopping criteria
        if state.step_count >= state.max_iterations:
            state.stopping_reason = "Maximum iterations reached"
        elif not leads:
            state.stopping_reason = "No investigative leads discovered"
        else:
            # We have leads! We must follow the top one.
            next_lead = select_next_lead_method(leads)
            state.current_lead = next_lead.model_dump() if next_lead else None

            if state.current_lead:
                # Setup HITL required flag
                state.awaiting_human_approval = True
                state.human_approved = None

        state_dict["state"] = state
        return state_dict

    async def approval_node(state_dict: dict[str, Any]) -> dict[str, Any]:
        """Human approval gateway for following investigative leads."""
        state = state_dict["state"]
        if isinstance(state, dict):
            state = AgentState(**state)

        # We only hit this node if execution unpaused and state.human_approved is no longer None
        state.awaiting_human_approval = False

        if state.human_approved is False:
            state.stopping_reason = "Overridden by Human Analyst"
        else:
            # Proceed
            lead = InvestigativeLead(**state.current_lead)
            state.investigation_chain.append(lead.model_dump())
            prev_findings = [Finding(**f) for f in state.findings]  # all findings
            state.current_goal = create_follow_up_goal_method(lead, prev_findings)

        state_dict["state"] = state
        return state_dict

    # Add nodes
    workflow.add_node("process_iteration", process_iteration_node)
    workflow.add_node("extract_leads", extract_leads_node)
    workflow.add_node("human_approval_gateway", approval_node)

    # Set entry point
    workflow.set_entry_point("process_iteration")
    workflow.add_edge("process_iteration", "extract_leads")

    # Conditional edge from extract_leads
    def check_leads(state_dict: dict[str, Any]) -> str:
        state = state_dict["state"]
        if isinstance(state, dict):
            state = AgentState(**state)
        if state.stopping_reason:
            return END
        if state.awaiting_human_approval and state.human_approved is None:
            return "human_approval_gateway"
        return "process_iteration"

    workflow.add_conditional_edges(
        "extract_leads",
        check_leads,
        {END: END, "human_approval_gateway": "human_approval_gateway", "process_iteration": "process_iteration"}
    )

    workflow.add_edge("human_approval_gateway", "process_iteration")

    return workflow.compile(checkpointer=get_checkpointer(), interrupt_before=["human_approval_gateway"])
