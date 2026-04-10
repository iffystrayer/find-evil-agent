"""Pydantic schemas for agent data validation.

This module defines the data models used by all agents.
Schemas ensure type safety and validation across the system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator


class ToolSelection(BaseModel):
    """Schema for tool selection by ToolSelectorAgent.
    
    Attributes:
        tool_name: Name of the selected SIFT tool
        reason: Explanation of why this tool was chosen
        confidence: Confidence score (0.0-1.0)
        inputs: Tool arguments
        alternatives: Other tools considered
    """
    
    tool_name: str = Field(..., description="Name of the SIFT tool")
    reason: str = Field(..., min_length=1, description="Explanation for selection")
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence score (reject if < 0.7)"
    )
    inputs: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    alternatives: list[str] = Field(default_factory=list, description="Other tools considered")
    
    @field_validator('tool_name')
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """Ensure tool name is not empty."""
        if not v.strip():
            raise ValueError("Tool name cannot be empty")
        return v.strip()


class ExecutionStatus(Enum):
    """Execution status for tool runs."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    TIMEOUT = "timeout"
    FAILED = "failed"


class ExecutionResult(BaseModel):
    """Schema for tool execution results.
    
    Attributes:
        tool_name: Executed tool name
        command: Actual command run
        stdout: Standard output
        stderr: Standard error
        return_code: Process return code
        status: Execution status
        execution_time: Time taken in seconds
        parsed_output: Structured data extracted
    """
    
    tool_name: str
    command: str | None = None
    stdout: str | None = None
    stderr: str | None = None
    return_code: int | None = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    execution_time: float = Field(default=0.0, ge=0.0)
    parsed_output: dict[str, Any] | None = None
    
    @property
    def success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.SUCCESS and self.return_code == 0


class AgentState(BaseModel):
    """Shared state for LangGraph workflow.
    
    This state is passed between agents in the workflow
    and maintains context across the analysis.
    """
    
    session_id: str | None = None
    incident_description: str | None = None
    selected_tools: list[ToolSelection] = Field(default_factory=list)
    execution_results: list[ExecutionResult] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    iocs: list[dict[str, Any]] = Field(default_factory=list)
    current_agent: str | None = None
    step_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


class FindingSeverity(str, Enum):
    """Severity levels for findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Finding(BaseModel):
    """Schema for incident findings."""

    title: str
    description: str
    severity: FindingSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    tool_references: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnalysisResult(BaseModel):
    """Schema for tool output analysis results.

    Attributes:
        tool_name: Name of the analyzed tool
        findings: List of extracted findings
        iocs: Extracted indicators of compromise (IPs, hashes, domains, etc.)
        raw_output: Original tool output
        parsed_output: Structured parsed data
        analysis_summary: Brief summary of analysis
    """

    tool_name: str
    findings: list[Finding] = Field(default_factory=list)
    iocs: dict[str, list[str]] = Field(default_factory=dict)
    raw_output: str
    parsed_output: dict[str, Any] = Field(default_factory=dict)
    analysis_summary: str = Field(default="")
