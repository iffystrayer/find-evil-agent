"""Helper functions for building report components.

Extracted from agents/reporter.py (C3b split).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

import structlog

if TYPE_CHECKING:
    from ..report_schemas import ExecutiveSummary, IOCTableEntry, TimelineEntry, Recommendation, AttackGraph
    from ..schemas import Finding, FindingSeverity

logger = structlog.get_logger(__name__)


async def create_executive_summary(
    findings: list[Finding],
    incident_description: str,
    analysis_goal: str,
) -> ExecutiveSummary:
    """Create executive summary from findings.

    Generates 3-5 paragraph executive summary suitable for
    management and stakeholders.
    """
    from ..report_schemas import ExecutiveSummary
    from ..schemas import FindingSeverity

    # Count by severity
    severity_counts = defaultdict(int)
    for finding in findings:
        severity_counts[finding.severity] += 1

    critical_count = severity_counts[FindingSeverity.CRITICAL]
    high_count = severity_counts[FindingSeverity.HIGH]

    # Incident overview
    incident_overview = f"""
This report documents the forensic analysis of a security incident: {incident_description}.
The investigation was conducted using the Find Evil Agent autonomous incident response system,
which performed comprehensive analysis across multiple forensic tools. A total of {len(findings)}
findings were identified during the investigation, including {critical_count} critical and {high_count}
high-severity discoveries that require immediate attention.
""".strip()

    # Key findings
    critical_findings = [f for f in findings if f.severity == FindingSeverity.CRITICAL]
    high_findings = [f for f in findings if f.severity == FindingSeverity.HIGH]

    key_findings_list = []
    for f in critical_findings[:3]:  # Top 3 critical
        key_findings_list.append(f"- **CRITICAL**: {f.title}")
    for f in high_findings[:2]:  # Top 2 high
        key_findings_list.append(f"- **HIGH**: {f.title}")

    if key_findings_list:
        key_findings = "\n".join(key_findings_list)
        # Ensure minimum length for validation
        if len(key_findings) < 50:
            key_findings += f" ({len(key_findings_list)} finding(s) requiring immediate attention)"
    else:
        key_findings = "No critical or high-severity findings identified during analysis. All findings are medium severity or lower."

    # Impact assessment
    if critical_count > 0:
        impact_assessment = f"""
The investigation identified {critical_count} critical-severity findings indicating active compromise
of the system. Immediate containment and remediation actions are required to prevent further damage.
The presence of {high_count} high-severity findings suggests the threat actor has established persistence
and may have achieved their objectives. This represents a significant security incident requiring
executive awareness and coordinated response across IT, Security, and Business teams.
""".strip()
    elif high_count > 0:
        impact_assessment = f"""
The investigation identified {high_count} high-severity findings indicating suspicious activity
that requires investigation and remediation. While no critical-severity indicators were found,
the high-severity findings suggest potential compromise or policy violations that could escalate
if not addressed promptly. Immediate action is recommended to contain and investigate these findings.
""".strip()
    else:
        impact_assessment = f"""
The investigation identified {len(findings)} findings of varying severity levels. No critical or
high-severity indicators of compromise were discovered, suggesting the incident may be lower risk
or require additional investigation to confirm the threat level. Continued monitoring and implementation
of recommended security controls are advised to maintain security posture.
""".strip()

    # Recommendations summary
    if critical_count > 0 or high_count > 0:
        recommendations_summary = f"""
Immediate actions are required: (1) Isolate affected systems to prevent lateral movement,
(2) Conduct credential reset for potentially compromised accounts, (3) Review and block
identified command and control infrastructure, (4) Deploy enhanced monitoring for indicators
identified in this report, and (5) Initiate incident response procedures per organizational policy.
Detailed recommendations are provided in the Recommendations section of this report.
""".strip()
    else:
        recommendations_summary = f"""
Recommended actions include: (1) Review and validate findings to rule out false positives,
(2) Implement additional monitoring for suspicious activities identified, (3) Review security
configurations and policies based on findings, and (4) Conduct follow-up investigation if warranted.
Detailed recommendations are provided in the Recommendations section of this report.
""".strip()

    return ExecutiveSummary(
        incident_overview=incident_overview,
        key_findings=key_findings,
        impact_assessment=impact_assessment,
        recommendations_summary=recommendations_summary,
    )


async def aggregate_iocs(iocs: dict[str, list[str]]) -> dict[str, list[dict]]:
    """Aggregate and deduplicate IOCs into structured tables.

    Args:
        iocs: Dict of IOC type to list of IOC values

    Returns:
        Dict of IOC type to list of IOC dicts (serialized IOCTableEntry objects)
    """
    from ..report_schemas import IOCTableEntry

    ioc_tables = {}

    for ioc_type, ioc_list in iocs.items():
        # Deduplicate and count occurrences
        ioc_counts = defaultdict(int)
        for ioc_value in ioc_list:
            ioc_counts[ioc_value] += 1

        # Build table entries
        entries = []
        for ioc_value, count in sorted(ioc_counts.items()):
            entry = IOCTableEntry(
                value=ioc_value,
                ioc_type=ioc_type,
                first_seen=datetime.now(timezone.utc),
                occurrences=count,
                context=f"Found {count} time(s) during analysis",
            )
            entries.append(entry.model_dump())  # Convert Pydantic to dict

        if entries:
            ioc_tables[ioc_type] = entries

    return ioc_tables


async def generate_timeline(findings: list[Finding]) -> list[TimelineEntry]:
    """Generate chronological timeline from findings.

    Args:
        findings: List of findings with timestamps

    Returns:
        Sorted list of timeline entries
    """
    from ..report_schemas import TimelineEntry

    timeline = []

    for finding in findings:
        timeline.append(TimelineEntry(
            timestamp=finding.timestamp,
            event_description=finding.title,
            severity=finding.severity.value,
            source_finding=finding.title,
            details=finding.description,
        ))

    # Sort chronologically
    return sorted(timeline, key=lambda t: t.timestamp)


async def generate_recommendations(findings: list[Finding]) -> list[Recommendation]:
    """Generate prioritized recommendations based on findings.

    Args:
        findings: List of findings

    Returns:
        Prioritized list of recommendations
    """
    from ..report_schemas import Recommendation
    from ..schemas import FindingSeverity

    recommendations = []

    # Group findings by severity
    critical_findings = [f for f in findings if f.severity == FindingSeverity.CRITICAL]
    high_findings = [f for f in findings if f.severity == FindingSeverity.HIGH]
    medium_findings = [f for f in findings if f.severity == FindingSeverity.MEDIUM]

    priority = 1

    # Critical findings - immediate action
    for finding in critical_findings:
        recommendations.append(Recommendation(
            priority=priority,
            title=f"Immediate Response: {finding.title}",
            description=f"CRITICAL: {finding.description}. Immediate containment and investigation required. "
                       f"Isolate affected systems, preserve evidence, and escalate to incident response team.",
            related_findings=[finding.title],
            urgency="immediate",
        ))
        priority += 1

    # High findings - urgent action
    for finding in high_findings[:3]:  # Top 3 high findings
        recommendations.append(Recommendation(
            priority=priority,
            title=f"Urgent Investigation: {finding.title}",
            description=f"HIGH: {finding.description}. Conduct detailed investigation within 24 hours. "
                       f"Review logs, identify affected assets, and implement containment if compromise confirmed.",
            related_findings=[finding.title],
            urgency="urgent",
        ))
        priority += 1

    # Medium findings - scheduled action
    if medium_findings:
        recommendations.append(Recommendation(
            priority=priority,
            title=f"Review Medium-Severity Findings ({len(medium_findings)} total)",
            description=f"Review {len(medium_findings)} medium-severity findings to determine if additional "
                       f"investigation is warranted. Validate against known-good baselines and organizational policies.",
            related_findings=[f.title for f in medium_findings[:5]],
            urgency="scheduled",
        ))
        priority += 1

    # General recommendations (linked to critical/high findings that triggered them)
    if critical_findings or high_findings:
        triggering_findings = [f.title for f in (critical_findings + high_findings)[:3]]

        recommendations.append(Recommendation(
            priority=priority,
            title="Credential Reset and Access Review",
            description="Reset credentials for all accounts with access to affected systems. Review and revoke "
                       "unnecessary access privileges. Enable multi-factor authentication where not already deployed.",
            related_findings=triggering_findings,
            urgency="urgent",
        ))
        priority += 1

        recommendations.append(Recommendation(
            priority=priority,
            title="Enhanced Monitoring and Detection",
            description="Deploy enhanced monitoring for indicators identified in this report. Review SIEM rules "
                       "and detection logic to ensure similar activity would be detected in the future. "
                       "Consider threat hunting exercises for similar indicators across the environment.",
            related_findings=triggering_findings,
            urgency="short-term",
        ))

    return recommendations


async def generate_attack_graph(findings: list[Finding]) -> Optional[AttackGraph]:
    """Generate attack chain graph from findings.

    Args:
        findings: List of findings with entity relationships

    Returns:
        AttackGraph object or None if no relationships found
    """
    from ..graph_builder import GraphBuilder

    try:
        builder = GraphBuilder()
        graph = builder.build_graph(findings)

        # Only return graph if it has nodes
        if graph.nodes:
            logger.info("attack_graph_generated",
                       node_count=len(graph.nodes),
                       edge_count=len(graph.edges))
            return graph
        else:
            logger.debug("attack_graph_empty", message="No relationships extracted")
            return None

    except Exception as e:
        logger.error("attack_graph_generation_failed", error=str(e))
        return None
