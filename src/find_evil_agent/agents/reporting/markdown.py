"""Markdown report formatting.

Extracted from agents/reporter.py (C3b split).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..report_schemas import ReportSchema
    from ..schemas import FindingSeverity, IterativeAnalysisResult


async def format_markdown(
    report: ReportSchema,
    iterative_result: Optional[IterativeAnalysisResult] = None,
) -> str:
    """Format report as Markdown.

    Args:
        report: Report schema
        iterative_result: Optional iterative analysis result (for investigation chain section)

    Returns:
        Markdown-formatted report
    """
    from ..schemas import FindingSeverity

    md = []

    # Header
    md.append("# Find Evil Agent - Incident Response Report\n")
    md.append(f"**Session ID:** {report.session_id}\n")
    md.append(f"**Generated:** {report.metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    md.append(f"**Incident:** {report.incident_description}\n")
    if report.analysis_goal:
        md.append(f"**Analysis Goal:** {report.analysis_goal}\n")
    md.append("\n---\n\n")

    # Executive Summary
    md.append("## Executive Summary\n\n")
    md.append(f"{report.executive_summary.incident_overview}\n\n")
    md.append("### Key Findings\n\n")
    md.append(f"{report.executive_summary.key_findings}\n\n")
    md.append("### Impact Assessment\n\n")
    md.append(f"{report.executive_summary.impact_assessment}\n\n")
    md.append("### Recommendations Summary\n\n")
    md.append(f"{report.executive_summary.recommendations_summary}\n\n")
    md.append("---\n\n")

    # Investigation Chain (for iterative analysis)
    if iterative_result:
        md.append("## Autonomous Investigation Chain\n\n")

        if iterative_result.iterations:
            md.append(f"This investigation utilized autonomous reasoning across **{len(iterative_result.iterations)} iterations**, ")
            md.append(f"following investigative leads and tool outputs to reconstruct the complete attack chain.\n\n")

            for iteration in iterative_result.iterations:
                md.append(f"### Iteration {iteration.iteration_number}: {iteration.tool_used}\n\n")
                if iteration.tool_selection:
                    md.append(f"**Reasoning:** {iteration.tool_selection.reason}\n\n")
                    md.append(f"**Confidence:** {iteration.tool_selection.confidence:.2f}\n\n")
                if iteration.findings:
                    md.append(f"**Findings:** {len(iteration.findings)} new findings discovered\n\n")
                if iteration.leads_discovered:
                    md.append(f"**Leads Discovered:** {len(iteration.leads_discovered)}\n\n")
                    for lead in iteration.leads_discovered[:3]:
                        md.append(f"- {lead}\n")
                    if len(iteration.leads_discovered) > 3:
                        md.append(f"- *(+{len(iteration.leads_discovered) - 3} more leads)*\n")
                    md.append("\n")
                md.append(f"**Duration:** {iteration.duration:.2f}s\n\n")
        else:
            # No iterations but still iterative result - show summary
            md.append(f"Investigation completed using autonomous reasoning (Iteration count: 0).\n\n")
            if hasattr(iterative_result, 'investigation_summary') and iterative_result.investigation_summary:
                md.append(f"**Summary:** {iterative_result.investigation_summary}\n\n")

        md.append(f"**Investigation Outcome:** {iterative_result.stopping_reason}\n\n")
        md.append("---\n\n")

    # MITRE ATT&CK Mapping
    md.append("## MITRE ATT&CK Mapping\n\n")
    if report.mitre_mappings:
        md.append("| Technique ID | Technique Name | Tactic | Related Findings |\n")
        md.append("|--------------|----------------|--------|------------------|\n")
        for mapping in report.mitre_mappings:
            findings_str = ", ".join(mapping.finding_references[:3])
            if len(mapping.finding_references) > 3:
                findings_str += f" (+{len(mapping.finding_references) - 3} more)"
            md.append(f"| {mapping.technique_id} | {mapping.technique_name} | {mapping.tactic} | {findings_str} |\n")
        md.append("\n")
    else:
        md.append("*No MITRE ATT&CK techniques mapped.*\n\n")
    md.append("---\n\n")

    # IOC Tables
    md.append("## Indicators of Compromise (IOCs)\n\n")
    if report.ioc_tables:
        for ioc_type, entries in sorted(report.ioc_tables.items()):
            md.append(f"### {ioc_type.upper()}\n\n")
            md.append("| IOC Value | Occurrences | Context |\n")
            md.append("|-----------|-------------|----------|\n")
            for entry in entries:
                md.append(f"| `{entry.value}` | {entry.occurrences} | {entry.context} |\n")
            md.append("\n")
    else:
        md.append("*No IOCs extracted during analysis.*\n\n")
    md.append("---\n\n")

    # Attack Chain Graph
    if report.attack_graph and report.attack_graph.nodes:
        md.append("## 🕸️ Attack Chain Graph\n\n")
        md.append("```mermaid\n")
        md.append("graph TD\n")
        for node in report.attack_graph.nodes:
            node_label = node.label.replace('"', '\\"').replace("'", "")
            md.append(f'  {node.id}["{node_label}"]\n')
            if node.severity == FindingSeverity.CRITICAL.value:
                md.append(f"  style {node.id} fill:#f8d7da,stroke:#dc3545\n")
            elif node.severity == FindingSeverity.HIGH.value:
                md.append(f"  style {node.id} fill:#fff3cd,stroke:#ffc107\n")
        for edge in report.attack_graph.edges:
            edge_label = edge.label.replace('"', '')
            md.append(f'  {edge.source} -->|"{edge_label}"| {edge.target}\n')
        md.append("```\n\n")
        md.append("---\n\n")

    # Timeline
    md.append("## Timeline\n\n")
    if report.timeline:
        for entry in report.timeline:
            timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            md.append(f"- **{timestamp_str}** [{entry.severity.upper()}] {entry.event_description}\n")
        md.append("\n")
    else:
        md.append("*No timeline events.*\n\n")
    md.append("---\n\n")

    # Findings by Severity
    md.append("## Findings by Severity\n\n")

    if not report.findings:
        md.append("*No suspicious findings detected during analysis.*\n\n")
    else:
        # Always show all severity levels (even if empty) for consistent structure
        for severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH, FindingSeverity.MEDIUM, FindingSeverity.LOW, FindingSeverity.INFO]:
            md.append(f"### {severity.value.upper()}\n\n")
            severity_findings = [f for f in report.findings if f.severity == severity]
            if severity_findings:
                for finding in severity_findings:
                    md.append(f"#### {finding.title}\n\n")
                    md.append(f"{finding.description}\n\n")
                    md.append(f"**Confidence:** {finding.confidence:.2f}\n\n")
                    if finding.evidence:
                        md.append("**Evidence:**\n\n")
                        for evidence in finding.evidence:
                            md.append(f"- {evidence}\n")
                        md.append("\n")
                    if finding.tool_references:
                        md.append(f"**Tools:** {', '.join(finding.tool_references)}\n\n")
                    md.append("---\n\n")
            else:
                md.append("*No findings at this severity level.*\n\n")

    # Recommendations
    md.append("## Recommendations\n\n")
    if report.recommendations:
        for rec in report.recommendations:
            md.append(f"### {rec.priority}. {rec.title}\n\n")
            md.append(f"**Urgency:** {rec.urgency}\n\n")
            md.append(f"{rec.description}\n\n")
            if rec.related_findings:
                md.append(f"**Related Findings:** {', '.join(rec.related_findings[:3])}\n\n")
            md.append("---\n\n")
    else:
        md.append("*No specific recommendations generated.*\n\n")

    # Metadata
    md.append("## Report Metadata\n\n")
    md.append(f"- **Tools Used:** {report.metadata.tool_count}\n")
    md.append(f"- **Total Findings:** {report.metadata.finding_count}\n")
    md.append(f"- **Total IOCs:** {report.metadata.ioc_count}\n")
    md.append(f"- **Analysis Duration:** {report.metadata.analysis_duration:.1f} seconds\n")
    md.append(f"- **Find Evil Agent Version:** {report.metadata.version}\n\n")

    return "".join(md)
