import sys

with open("src/find_evil_agent/agents/orchestrator.py", "r") as f:
    code = f.read()

# 1. Add MemorySaver import
code = code.replace(
    "from langgraph.graph import StateGraph, END",
    "from langgraph.graph import StateGraph, END\nfrom langgraph.checkpoint.memory import MemorySaver"
)

# 2. Add build_iterative_workflow and specific nodes
iterative_methods = """
    def _build_iterative_workflow(self) -> Any:
        workflow = StateGraph(dict)

        workflow.add_node("process_iteration", self._iterative_process_node)
        workflow.add_node("extract_leads", self._iterative_extract_leads_node)
        workflow.add_node("human_approval_gateway", self._iterative_approval_node)

        workflow.set_entry_point("process_iteration")
        workflow.add_edge("process_iteration", "extract_leads")

        def check_leads(state_dict: dict[str, Any]) -> str:
            state: AgentState = state_dict["state"]
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

        memory = MemorySaver()
        return workflow.compile(checkpointer=memory, interrupt_before=["human_approval_gateway"])

    async def _iterative_process_node(self, state_dict: dict[str, Any]) -> dict[str, Any]:
        state: AgentState = state_dict["state"]
        
        # Determine the goal for this iteration
        current_goal = state.current_goal or state.analysis_goal
        
        agent_logger.info("iteration_started", session_id=state.session_id, iteration=state.step_count+1)
        start_t = time.time()
        
        # Run standard process (tool selection -> execution -> analysis) as a sub-call
        # This is safe because self.process does its own self.workflow.ainvoke without memory checkpointer conflicts
        result = await self.process({
            "incident_description": state.incident_description,
            "analysis_goal": current_goal
        })
        
        if not result.success:
            state.stopping_reason = f"Iteration error: {result.error}"
            state_dict["state"] = state
            return state_dict
            
        inner_state = result.data["state"]
        iteration_findings = [Finding(**f) for f in inner_state.findings]
        iteration_iocs = self._merge_iocs(inner_state.iocs)
        
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
        
        # Merge dicts
        merged_iocs = {}
        # load existing
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

    async def _iterative_extract_leads_node(self, state_dict: dict[str, Any]) -> dict[str, Any]:
        state: AgentState = state_dict["state"]
        if state.stopping_reason:
            return state_dict
            
        # Get latest iteration
        if not state.iterations:
            return state_dict
            
        last_it = IterationResult(**state.iterations[-1])
        
        leads = await self._extract_leads(
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
            next_lead = self._select_next_lead(leads)
            state.current_lead = next_lead.model_dump() if next_lead else None
            
            if state.current_lead:
                # Setup HITL required flag
                state.awaiting_human_approval = True
                state.human_approved = None
        
        state_dict["state"] = state
        return state_dict

    async def _iterative_approval_node(self, state_dict: dict[str, Any]) -> dict[str, Any]:
        state: AgentState = state_dict["state"]
        
        # We only hit this node if execution unpaused and state.human_approved is no longer None
        state.awaiting_human_approval = False
        
        if state.human_approved is False:
            state.stopping_reason = "Overridden by Human Analyst"
        else:
            # Proceed
            lead = InvestigativeLead(**state.current_lead)
            state.investigation_chain.append(lead.model_dump())
            prev_findings = [Finding(**f) for f in state.findings] # all findings
            state.current_goal = self._create_follow_up_goal(lead, prev_findings)
            
        state_dict["state"] = state
        return state_dict
"""

# Replace __init__ to also compile iterative workflow
code = code.replace(
    "self.workflow = self._build_workflow()",
    "self.workflow = self._build_workflow()\n        self.iterative_workflow = self._build_iterative_workflow()"
)

# Insert the new iterative methods right after _build_workflow
import re
code = code.replace(
    "    def _build_workflow(self) -> Any:",
    iterative_methods + "\n    def _build_workflow(self) -> Any:"
)

# Replace process_iterative completely
process_iterative_code = """    async def process_iterative(
        self,
        incident_description: str,
        analysis_goal: str,
        max_iterations: int = 5,
        auto_follow: bool = True,
        min_lead_confidence: float = 0.6,
        session_id: str | None = None
    ) -> IterativeAnalysisResult:
        
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
                incident_description=result_state.incident_description,
                analysis_goal=result_state.analysis_goal,
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
            )"""

# Regex to replace process_iterative completely until _extract_leads
code = re.sub(
    r"    async def process_iterative\([^)]+\)\s*->\s*IterativeAnalysisResult:.*?    async def _extract_leads",
    process_iterative_code + "\n\n    async def _extract_leads",
    code,
    flags=re.DOTALL
)

with open("src/find_evil_agent/agents/orchestrator.py", "w") as f:
    f.write(code)

print("Patching complete.")
