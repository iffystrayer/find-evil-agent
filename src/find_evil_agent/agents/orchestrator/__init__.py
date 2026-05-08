"""Orchestrator package - workflow coordination modules.

Split from monolithic orchestrator.py (C3c refactor).

Modules:
- agent: OrchestratorAgent class (main coordinator)
- workflows: LangGraph workflow builders and node implementations
- prompting: LLM prompt building and response parsing for lead extraction
"""

# Re-export OrchestratorAgent for backward compatibility
from .agent import OrchestratorAgent

# Export workflow and prompting helpers
from .workflows import build_workflow, build_iterative_workflow
from .prompting import (
    build_lead_extraction_prompt,
    parse_leads_from_response,
    extract_leads_fallback
)

__all__ = [
    "OrchestratorAgent",
    "build_workflow",
    "build_iterative_workflow",
    "build_lead_extraction_prompt",
    "parse_leads_from_response",
    "extract_leads_fallback"
]
