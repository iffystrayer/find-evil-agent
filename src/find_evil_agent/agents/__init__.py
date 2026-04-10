"""Agent Intelligence Module.

This module contains the core agent implementations for the DFIR workflow.

Agents:
    OrchestratorAgent: Entry point and task dispatch
    ToolSelectorAgent: Intelligent tool selection with confidence scoring
    ExecutionAgent: Safe SIFT tool execution
    AnalysisAgent: Result analysis and IOC detection
    ReporterAgent: Structured report generation
    MemoryAgent: Cross-agent context management

Note:
    Implementations are stubs pending April 15 starter code.
"""

from .base import BaseAgent
from .schemas import ToolSelection, AgentState, ExecutionResult, AnalysisResult, Finding
from .tool_selector import ToolSelectorAgent
from .tool_executor import ToolExecutorAgent
from .analyzer import AnalyzerAgent

__all__ = [
    "BaseAgent",
    "ToolSelection",
    "AgentState",
    "ExecutionResult",
    "AnalysisResult",
    "Finding",
    "ToolSelectorAgent",
    "ToolExecutorAgent",
    "AnalyzerAgent",
]
