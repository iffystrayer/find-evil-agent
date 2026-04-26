"""Pydantic schemas for professional incident reporting.

This module defines the data models for generating professional
IR reports that meet Valhuntir quality standards.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ReportFormat(str, Enum):
    """Supported report output formats."""

    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"


class ExecutiveSummary(BaseModel):
    """Executive summary section of IR report.

    High-level overview for management and stakeholders.
    Should be 3-5 paragraphs covering incident nature, impact, and key findings.

    Attributes:
        incident_overview: What happened and when
        key_findings: Most critical discoveries
        impact_assessment: Business/system impact
        recommendations_summary: High-level recommended actions
    """

    incident_overview: str = Field(..., min_length=100, description="Incident description")
    key_findings: str = Field(..., min_length=50, description="Critical findings")
    impact_assessment: str = Field(..., min_length=50, description="Impact analysis")
    recommendations_summary: str = Field(..., min_length=50, description="Recommended actions")


class MITREMapping(BaseModel):
    """MITRE ATT&CK technique mapping.

    Maps findings to MITRE ATT&CK framework for standardized
    threat intelligence communication.

    Attributes:
        technique_id: MITRE technique ID (e.g., T1059.001)
        technique_name: Human-readable technique name
        tactic: Associated tactic (e.g., Execution, Persistence)
        description: Brief description of technique
        finding_references: IDs or titles of findings that map to this technique
        confidence: Confidence in this mapping (0.0-1.0)
    """

    technique_id: str = Field(..., description="MITRE ATT&CK technique ID")
    technique_name: str = Field(..., description="Technique name")
    tactic: str = Field(..., description="Associated tactic")
    description: str = Field(default="", description="Technique description")
    finding_references: list[str] = Field(default_factory=list, description="Related findings")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Mapping confidence")


class IOCTableEntry(BaseModel):
    """Single entry in an IOC table.

    Attributes:
        value: The IOC value (IP, hash, domain, etc.)
        ioc_type: Type of IOC (ipv4, md5, domain, etc.)
        first_seen: When first observed
        occurrences: Number of times observed
        context: Additional context (tool that found it, related findings, etc.)
    """

    value: str = Field(..., description="IOC value")
    ioc_type: str = Field(..., description="IOC type")
    first_seen: datetime = Field(default_factory=datetime.utcnow, description="First observation")
    occurrences: int = Field(default=1, ge=1, description="Occurrence count")
    context: str = Field(default="", description="Additional context")


class TimelineEntry(BaseModel):
    """Timeline event entry.

    Chronological event for incident timeline.

    Attributes:
        timestamp: When event occurred
        event_description: What happened
        severity: Event severity level
        source_finding: Finding title or ID that generated this event
        details: Additional event details
    """

    timestamp: datetime = Field(..., description="Event timestamp")
    event_description: str = Field(..., min_length=10, description="Event description")
    severity: str = Field(..., description="Severity level")
    source_finding: str = Field(..., description="Source finding")
    details: str = Field(default="", description="Additional details")


class Recommendation(BaseModel):
    """Actionable recommendation.

    Prioritized action item based on findings.

    Attributes:
        priority: Priority level (1=highest)
        title: Short recommendation title
        description: Detailed recommendation with steps
        related_findings: Findings that drove this recommendation
        urgency: Timeframe for action (immediate, short-term, long-term)
    """

    priority: int = Field(..., ge=1, le=10, description="Priority (1=highest)")
    title: str = Field(..., min_length=10, description="Recommendation title")
    description: str = Field(..., min_length=50, description="Detailed recommendation")
    related_findings: list[str] = Field(default_factory=list, description="Related findings")
    urgency: str = Field(default="medium", description="Urgency level")


class ReportMetadata(BaseModel):
    """Report metadata.

    Attributes:
        session_id: Unique session identifier
        generated_at: When report was generated
        tool_count: Number of tools used
        finding_count: Total findings count
        ioc_count: Total IOC count
        analysis_duration: Total analysis time (seconds)
        format: Report output format
        version: Find Evil Agent version
    """

    session_id: str = Field(..., description="Session ID")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation time")
    tool_count: int = Field(default=0, ge=0, description="Tools used")
    finding_count: int = Field(default=0, ge=0, description="Total findings")
    ioc_count: int = Field(default=0, ge=0, description="Total IOCs")
    analysis_duration: float = Field(default=0.0, ge=0.0, description="Duration in seconds")
    format: ReportFormat = Field(..., description="Output format")
    version: str = Field(default="0.1.0", description="Agent version")


class GraphNode(BaseModel):
    """Node in attack chain graph.

    Represents an entity (process, file, network, etc.) in the attack chain.

    Attributes:
        id: Unique node identifier
        label: Display label (e.g., "malware.exe", "192.168.1.1")
        node_type: Type of entity (process/file/network/registry/ioc)
        severity: Severity level inherited from findings
        properties: Additional metadata
        occurrences: Number of times this entity appeared
    """

    id: str = Field(..., description="Unique node ID")
    label: str = Field(..., description="Display label")
    node_type: str = Field(..., description="Node type")
    severity: str = Field(default="info", description="Severity level")
    properties: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    occurrences: int = Field(default=1, ge=1, description="Occurrence count")


class GraphEdge(BaseModel):
    """Edge in attack chain graph.

    Represents a relationship between entities.

    Attributes:
        source: Source node ID
        target: Target node ID
        edge_type: Type of relationship (spawned/created/connected_to/modified/referenced)
        label: Display label for edge
        properties: Additional metadata
    """

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    edge_type: str = Field(..., description="Edge type")
    label: str = Field(default="", description="Display label")
    properties: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AttackGraph(BaseModel):
    """Complete attack chain graph.

    Graph representation of attack progression showing entities and relationships.

    Attributes:
        nodes: All graph nodes
        edges: All graph edges
        entry_points: Initial attack entry point node IDs
        critical_path: Most critical attack chain node IDs
        metadata: Graph generation metadata
    """

    nodes: list[GraphNode] = Field(default_factory=list, description="Graph nodes")
    edges: list[GraphEdge] = Field(default_factory=list, description="Graph edges")
    entry_points: list[str] = Field(default_factory=list, description="Entry point node IDs")
    critical_path: list[str] = Field(default_factory=list, description="Critical path node IDs")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Graph metadata")


class ReportSchema(BaseModel):
    """Complete IR report schema.

    Professional incident response report structure meeting
    Valhuntir quality standards.

    Attributes:
        session_id: Unique session identifier
        incident_description: Original incident description
        analysis_goal: Original analysis goal
        executive_summary: High-level summary for stakeholders
        findings: All findings organized by severity
        ioc_tables: IOC tables by type (ipv4, domain, hash, etc.)
        timeline: Chronological event timeline
        mitre_mappings: MITRE ATT&CK technique mappings
        recommendations: Prioritized action items
        metadata: Report generation metadata
        evidence_citations: Tool output references
        attack_graph: Attack chain graph visualization data
    """

    session_id: str = Field(..., description="Session ID")
    incident_description: str = Field(..., description="Incident description")
    analysis_goal: str = Field(default="", description="Analysis goal")
    executive_summary: ExecutiveSummary = Field(..., description="Executive summary")
    findings: list[Any] = Field(default_factory=list, description="All findings")
    ioc_tables: dict[str, list[IOCTableEntry]] = Field(
        default_factory=dict, description="IOC tables"
    )
    timeline: list[TimelineEntry] = Field(default_factory=list, description="Event timeline")
    mitre_mappings: list[MITREMapping] = Field(default_factory=list, description="MITRE mappings")
    recommendations: list[Recommendation] = Field(
        default_factory=list, description="Recommendations"
    )
    metadata: ReportMetadata = Field(..., description="Report metadata")
    evidence_citations: dict[str, str] = Field(
        default_factory=dict, description="Evidence references"
    )
    attack_graph: AttackGraph | None = Field(default=None, description="Attack chain graph")

    class Config:
        arbitrary_types_allowed = True
