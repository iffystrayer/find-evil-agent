"""LangGraph State Definitions.

State is passed between agents in the workflow.
"""

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """Shared state for LangGraph workflow.
    
    This state flows through all agents:
    Orchestrator -> Selector -> Executor -> Analyzer -> Reporter
    """
    
    # Workflow metadata
    session_id: str | None
    current_agent: str | None
    step_count: int
    
    # Input
    incident_description: str | None
    evidence_path: str | None
    
    # Agent outputs
    selected_tools: list[dict[str, Any]]
    execution_results: list[dict[str, Any]]
    analysis_findings: list[dict[str, Any]]
    
    # Final output
    report: dict[str, Any] | None
