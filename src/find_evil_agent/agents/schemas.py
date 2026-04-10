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


class LeadType(str, Enum):
    """Types of investigative leads."""
    PROCESS = "process"
    NETWORK = "network"
    FILE = "file"
    TIMELINE = "timeline"
    REGISTRY = "registry"


class LeadPriority(str, Enum):
    """Priority levels for investigative leads."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InvestigativeLead(BaseModel):
    """Schema for investigative leads discovered during analysis.

    Represents a potential next step in the investigation that the
    autonomous agent can follow to build a complete attack chain.

    Attributes:
        lead_type: Type of investigation (process/network/file/timeline/registry)
        description: Human-readable description of what to investigate
        priority: Priority level for this lead
        suggested_tool: Optional specific tool recommendation
        context: Additional context data (IOCs, process IDs, etc.)
        confidence: LLM confidence that this lead is worth following (0.0-1.0)
        reasoning: Explanation of why this lead should be followed
    """

    lead_type: LeadType
    description: str = Field(..., min_length=1)
    priority: LeadPriority = LeadPriority.MEDIUM
    suggested_tool: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    reasoning: str = Field(default="")

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Ensure description is not empty."""
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()


class IterationResult(BaseModel):
    """Schema for results from a single iteration of analysis.

    Captures what happened in one iteration of the autonomous
    investigation workflow.

    Attributes:
        iteration_number: Which iteration this is (1-based)
        tool_used: Tool that was executed this iteration
        tool_selection: Full tool selection details
        execution_result: Full execution details
        findings: Findings discovered this iteration
        iocs: IOCs extracted this iteration
        leads_discovered: New investigative leads found
        lead_followed: The lead that triggered this iteration (None for initial)
        duration: How long this iteration took (seconds)
        timestamp: When iteration completed
    """

    iteration_number: int = Field(..., ge=1)
    tool_used: str
    tool_selection: ToolSelection | None = None
    execution_result: ExecutionResult | None = None
    findings: list[Finding] = Field(default_factory=list)
    iocs: dict[str, list[str]] = Field(default_factory=dict)
    leads_discovered: list[InvestigativeLead] = Field(default_factory=list)
    lead_followed: InvestigativeLead | None = None
    duration: float = Field(default=0.0, ge=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IterativeAnalysisResult(BaseModel):
    """Schema for complete iterative analysis results.

    Contains all iterations and synthesized investigation chain.

    Attributes:
        session_id: Unique session identifier
        incident_description: Original incident description
        analysis_goal: Original analysis goal
        iterations: Results from each iteration
        investigation_chain: Ordered sequence of leads followed
        all_findings: All findings from all iterations
        all_iocs: All IOCs from all iterations
        total_duration: Total time for all iterations
        stopping_reason: Why the investigation stopped
        investigation_summary: Human-readable summary of complete investigation
        timestamp: When investigation completed
    """

    session_id: str
    incident_description: str
    analysis_goal: str
    iterations: list[IterationResult] = Field(default_factory=list)
    investigation_chain: list[InvestigativeLead | None] = Field(default_factory=list)
    all_findings: list[Finding] = Field(default_factory=list)
    all_iocs: dict[str, list[str]] = Field(default_factory=dict)
    total_duration: float = Field(default=0.0, ge=0.0)
    stopping_reason: str = Field(default="")
    investigation_summary: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
