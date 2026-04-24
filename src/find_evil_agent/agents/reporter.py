"""Report Agent - Professional incident report generation.

Generates professional IR reports meeting Valhuntir quality standards:
1. Executive summary with incident overview
2. MITRE ATT&CK technique mapping
3. IOC aggregation and structured tables
4. Chronological timeline
5. Findings organized by severity
6. Prioritized recommendations
7. Evidence citations
8. Multiple output formats (Markdown, HTML, PDF)
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from collections import defaultdict
import structlog

from .base import BaseAgent, AgentResult, AgentStatus
from .schemas import Finding, FindingSeverity, AnalysisResult, IterativeAnalysisResult
from .report_schemas import (
    ReportFormat, ReportSchema, ExecutiveSummary, MITREMapping,
    IOCTableEntry, TimelineEntry, Recommendation, ReportMetadata, AttackGraph
)
from .graph_builder import GraphBuilder

logger = structlog.get_logger(__name__)


# MITRE ATT&CK mapping database (simplified - in production use full matrix)
MITRE_PATTERNS = {
    "powershell": [
        ("T1059.001", "PowerShell", "Execution", "Command and Scripting Interpreter: PowerShell"),
    ],
    "cmd.exe": [
        ("T1059.003", "Windows Command Shell", "Execution", "Command and Scripting Interpreter: Windows Command Shell"),
    ],
    "suspicious process": [
        ("T1055", "Process Injection", "Defense Evasion", "Process injection techniques"),
    ],
    "registry": [
        ("T1547.001", "Registry Run Keys / Startup Folder", "Persistence", "Boot or Logon Autostart Execution"),
    ],
    "c2": [
        ("T1071", "Application Layer Protocol", "Command and Control", "Application layer protocols for C2"),
    ],
    "network connection": [
        ("T1071.001", "Web Protocols", "Command and Control", "Web-based C2 communication"),
    ],
    "persistence": [
        ("T1543", "Create or Modify System Process", "Persistence", "System service persistence"),
    ],
    "privilege escalation": [
        ("T1068", "Exploitation for Privilege Escalation", "Privilege Escalation", "Exploit vulnerabilities for privilege escalation"),
    ],
    "credential": [
        ("T1003", "OS Credential Dumping", "Credential Access", "Dump credentials from operating system"),
    ],
    "file modification": [
        ("T1486", "Data Encrypted for Impact", "Impact", "Ransomware and data encryption"),
    ],
    "dll": [
        ("T1574.001", "DLL Search Order Hijacking", "Persistence", "DLL hijacking for persistence"),
    ],
}


class ReporterAgent(BaseAgent):
    """Generates professional incident reports.

    Output Formats:
    - Markdown (human-readable, version-controllable)
    - HTML (professional browser-viewable)
    - PDF (print-ready, shareable)

    Report Components:
    - Executive Summary
    - MITRE ATT&CK Mapping
    - IOC Tables
    - Timeline
    - Findings by Severity
    - Recommendations
    - Evidence Citations
    - Metadata
    """

    def __init__(self, **kwargs):
        super().__init__(name="reporter", **kwargs)

    async def process(self, input_data: dict) -> AgentResult:
        """Generate professional IR report.

        Args:
            input_data: Dict containing:
                - analysis_result: AnalysisResult object OR
                - iterative_result: IterativeAnalysisResult object
                - format: Output format (markdown/html/pdf)
                - session_id: Session identifier
                - incident_description: Incident description
                - analysis_goal: Analysis goal (optional)
                - output_path: File path for output (optional)

        Returns:
            AgentResult with report data
        """
        try:
            logger.info("report_generation_started", session_id=input_data.get("session_id"))

            # Determine input type
            if "iterative_result" in input_data:
                report = await self.generate_report(
                    iterative_result=input_data["iterative_result"],
                    format=ReportFormat(input_data.get("format", "markdown")),
                    output_path=input_data.get("output_path"),
                )
            elif "analysis_result" in input_data:
                report = await self.generate_report(
                    analysis_result=input_data["analysis_result"],
                    format=ReportFormat(input_data.get("format", "markdown")),
                    session_id=input_data.get("session_id", "unknown"),
                    incident_description=input_data.get("incident_description", ""),
                    analysis_goal=input_data.get("analysis_goal", ""),
                    output_path=input_data.get("output_path"),
                )
            else:
                raise ValueError("Must provide either analysis_result or iterative_result")

            logger.info("report_generation_completed", session_id=input_data.get("session_id"))

            return AgentResult(
                status=AgentStatus.SUCCESS,
                success=True,
                data={"report": report},
                metadata={"format": input_data.get("format", "markdown")}
            )

        except Exception as e:
            logger.error("report_generation_failed", error=str(e), session_id=input_data.get("session_id"))
            return AgentResult(
                status=AgentStatus.FAILED,
                success=False,
                error=str(e),
                data={}
            )

    async def generate_report(
        self,
        analysis_result: Optional[AnalysisResult] = None,
        iterative_result: Optional[IterativeAnalysisResult] = None,
        format: ReportFormat = ReportFormat.MARKDOWN,
        session_id: Optional[str] = None,
        incident_description: str = "",
        analysis_goal: str = "",
        output_path: Optional[Path] = None,
        fallback_to_html: bool = True,
    ) -> str:
        """Generate professional IR report.

        Args:
            analysis_result: Single analysis result
            iterative_result: Iterative analysis result
            format: Output format
            session_id: Session ID
            incident_description: Incident description
            analysis_goal: Analysis goal
            output_path: Output file path
            fallback_to_html: Fallback to HTML if PDF fails

        Returns:
            Report content as string (or writes to file for PDF)
        """
        # Extract data from appropriate input
        if iterative_result:
            findings = iterative_result.all_findings
            iocs = iterative_result.all_iocs
            session_id = iterative_result.session_id
            incident_description = iterative_result.incident_description
            analysis_goal = iterative_result.analysis_goal
            duration = iterative_result.total_duration
            tool_count = len(set(iter.tool_used for iter in iterative_result.iterations))
        elif analysis_result:
            findings = analysis_result.findings
            iocs = analysis_result.iocs
            duration = 0.0
            tool_count = 1
        else:
            raise ValueError("Must provide either analysis_result or iterative_result")

        # Build report schema
        report_schema = await self._build_report_schema(
            findings=findings,
            iocs=iocs,
            session_id=session_id or "unknown",
            incident_description=incident_description,
            analysis_goal=analysis_goal,
            format=format,
            duration=duration,
            tool_count=tool_count,
        )

        # Generate output in requested format
        content = None
        if format == ReportFormat.MARKDOWN:
            content = await self.format_markdown(report_schema, iterative_result=iterative_result)
        elif format == ReportFormat.HTML:
            content = await self.format_html(report_schema)
        elif format == ReportFormat.PDF:
            try:
                return await self.format_pdf(report_schema, output_path)
            except ValueError as e:
                # Re-raise validation errors about invalid paths (parent doesn't exist)
                if "Invalid output path" in str(e):
                    raise
                # For missing output_path, use fallback if enabled
                logger.warning("pdf_generation_failed", error=str(e), fallback=fallback_to_html)
                if fallback_to_html:
                    return await self.format_html(report_schema)
                raise
            except Exception as e:
                logger.warning("pdf_generation_failed", error=str(e), fallback=fallback_to_html)
                if fallback_to_html:
                    return await self.format_html(report_schema)
                raise

        # Write to output_path if provided for non-PDF formats
        if output_path and content:
            output_path = Path(output_path)
            if not output_path.parent.exists():
                raise ValueError(f"Invalid output path: {output_path.parent} does not exist")
            with open(output_path, "w") as f:
                f.write(content)
            logger.info("report_written", path=str(output_path), format=format.value)
            return str(output_path)

        return content

    async def _build_report_schema(
        self,
        findings: list[Finding],
        iocs: dict[str, list[str]],
        session_id: str,
        incident_description: str,
        analysis_goal: str,
        format: ReportFormat,
        duration: float,
        tool_count: int,
    ) -> ReportSchema:
        """Build complete report schema from findings and IOCs."""

        # Generate all report components
        executive_summary = await self.create_executive_summary(
            findings=findings,
            incident_description=incident_description,
            analysis_goal=analysis_goal,
        )

        mitre_mappings = await self.map_mitre_attacks(findings=findings)
        ioc_tables = await self.aggregate_iocs(iocs=iocs)
        timeline = await self.generate_timeline(findings=findings)
        recommendations = await self.generate_recommendations(findings=findings)
        attack_graph = await self.generate_attack_graph(findings=findings)

        # Build metadata
        metadata = ReportMetadata(
            session_id=session_id,
            generated_at=datetime.now(timezone.utc),
            tool_count=tool_count,
            finding_count=len(findings),
            ioc_count=sum(len(v) for v in iocs.values()),
            analysis_duration=duration,
            format=format,
            version="0.1.0",
        )

        # Build evidence citations
        evidence_citations = {}
        for finding in findings:
            for tool_ref in finding.tool_references:
                if tool_ref not in evidence_citations:
                    evidence_citations[tool_ref] = finding.title

        return ReportSchema(
            session_id=session_id,
            incident_description=incident_description,
            analysis_goal=analysis_goal,
            executive_summary=executive_summary,
            findings=findings,
            ioc_tables=ioc_tables,
            timeline=timeline,
            mitre_mappings=mitre_mappings,
            recommendations=recommendations,
            attack_graph=attack_graph,
            metadata=metadata,
            evidence_citations=evidence_citations,
        )

    async def create_executive_summary(
        self,
        findings: list[Finding],
        incident_description: str,
        analysis_goal: str,
    ) -> ExecutiveSummary:
        """Create executive summary from findings.

        Generates 3-5 paragraph executive summary suitable for
        management and stakeholders.
        """
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

    async def map_mitre_attacks(self, findings: list[Finding]) -> list[MITREMapping]:
        """Map findings to MITRE ATT&CK techniques.

        Uses pattern matching against finding titles and descriptions
        to identify applicable MITRE techniques.
        """
        mappings = []
        seen_techniques = set()

        for finding in findings:
            # Search for MITRE patterns in finding
            finding_text = f"{finding.title} {finding.description}".lower()

            for pattern, techniques in MITRE_PATTERNS.items():
                if pattern in finding_text:
                    for technique_id, name, tactic, description in techniques:
                        if technique_id not in seen_techniques:
                            mappings.append(MITREMapping(
                                technique_id=technique_id,
                                technique_name=name,
                                tactic=tactic,
                                description=description,
                                finding_references=[finding.title],
                                confidence=0.8,
                            ))
                            seen_techniques.add(technique_id)
                        else:
                            # Add finding reference to existing mapping
                            for mapping in mappings:
                                if mapping.technique_id == technique_id:
                                    if finding.title not in mapping.finding_references:
                                        mapping.finding_references.append(finding.title)

        return sorted(mappings, key=lambda m: m.technique_id)

    async def aggregate_iocs(self, iocs: dict[str, list[str]]) -> dict[str, list[dict]]:
        """Aggregate and deduplicate IOCs into structured tables.

        Args:
            iocs: Dict of IOC type to list of IOC values

        Returns:
            Dict of IOC type to list of IOC dicts (serialized IOCTableEntry objects)
        """
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

    async def generate_timeline(self, findings: list[Finding]) -> list[TimelineEntry]:
        """Generate chronological timeline from findings.

        Args:
            findings: List of findings with timestamps

        Returns:
            Sorted list of timeline entries
        """
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

    async def generate_recommendations(self, findings: list[Finding]) -> list[Recommendation]:
        """Generate prioritized recommendations based on findings.

        Args:
            findings: List of findings

        Returns:
            Prioritized list of recommendations
        """
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

    async def generate_attack_graph(self, findings: list[Finding]) -> Optional[AttackGraph]:
        """Generate attack chain graph from findings.

        Args:
            findings: List of findings with entity relationships

        Returns:
            AttackGraph object or None if no relationships found
        """
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

    async def _generate_graph_html(self, attack_graph: AttackGraph) -> str:
        """Generate inline HTML for attack chain graph visualization.

        Args:
            attack_graph: AttackGraph object with nodes and edges

        Returns:
            HTML string with embedded D3.js graph
        """
        import json

        # Convert graph to JSON for D3.js
        graph_data = {
            "nodes": [
                {
                    "id": node.id,
                    "label": node.label,
                    "node_type": node.node_type,
                    "severity": node.severity,
                    "occurrences": node.occurrences,
                    "properties": node.properties,
                }
                for node in attack_graph.nodes
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "edge_type": edge.edge_type,
                    "label": edge.label,
                    "properties": edge.properties,
                }
                for edge in attack_graph.edges
            ],
            "entry_points": attack_graph.entry_points,
            "critical_path": attack_graph.critical_path,
        }

        # Read template and inject data
        template_path = Path(__file__).parent.parent.parent.parent / "templates" / "report_graph_template.html"

        try:
            with open(template_path, 'r') as f:
                template_html = f.read()

            # Inject graph data into template
            graph_html = template_html.replace(
                "{{ GRAPH_DATA }}",
                json.dumps(graph_data)
            )

            # Wrap in section for embedding
            return f"""
    <div class="section" style="padding: 0; height: 800px; position: relative;">
        <iframe
            srcdoc="{graph_html.replace('"', '&quot;')}"
            style="width: 100%; height: 100%; border: none; border-radius: 8px;"
            sandbox="allow-scripts"
        ></iframe>
    </div>
"""
        except Exception as e:
            logger.error("graph_html_generation_failed", error=str(e))
            return f"""
    <div class="section">
        <h2>🕸️ Attack Chain Graph</h2>
        <p style="color: #dc3545;">Graph visualization unavailable: {str(e)}</p>
        <p>Nodes: {len(attack_graph.nodes)}, Edges: {len(attack_graph.edges)}</p>
    </div>
"""

    async def format_markdown(self, report: ReportSchema, iterative_result: Optional[IterativeAnalysisResult] = None) -> str:
        """Format report as Markdown.

        Args:
            report: Report schema
            iterative_result: Optional iterative analysis result (for investigation chain section)

        Returns:
            Markdown-formatted report
        """
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

    async def format_html(self, report: ReportSchema) -> str:
        """Format report as HTML with professional styling.

        Args:
            report: Report schema

        Returns:
            HTML-formatted report
        """
        html = []

        # HTML header with CSS
        html.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Find Evil Agent - Incident Response Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 2em;
        }
        .metadata {
            font-size: 0.9em;
            margin-top: 10px;
        }
        .section {
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section h2 {
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .severity-critical {
            border-left: 5px solid #dc3545;
            padding-left: 15px;
            background-color: #ffe6e6;
            margin: 10px 0;
            padding: 15px;
        }
        .severity-high {
            border-left: 5px solid #fd7e14;
            padding-left: 15px;
            background-color: #fff3e6;
            margin: 10px 0;
            padding: 15px;
        }
        .severity-medium {
            border-left: 5px solid #ffc107;
            padding-left: 15px;
            background-color: #fffbf0;
            margin: 10px 0;
            padding: 15px;
        }
        .severity-low {
            border-left: 5px solid #17a2b8;
            padding-left: 15px;
            background-color: #e6f7f9;
            margin: 10px 0;
            padding: 15px;
        }
        .severity-info {
            border-left: 5px solid #6c757d;
            padding-left: 15px;
            background-color: #f8f9fa;
            margin: 10px 0;
            padding: 15px;
        }
        .ioc-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .ioc-table th {
            background-color: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }
        .ioc-table td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        .ioc-table tr:hover {
            background-color: #f5f5f5;
        }
        .ioc-value {
            font-family: 'Courier New', monospace;
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
        }
        .timeline-entry {
            border-left: 3px solid #667eea;
            padding-left: 15px;
            margin: 15px 0;
        }
        .recommendation {
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
        }
        .recommendation-priority {
            background-color: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
            display: inline-block;
            margin-right: 10px;
        }
    </style>
</head>
<body>
""")

        # Header
        html.append(f"""
    <div class="header">
        <h1>🔍 Find Evil Agent - Incident Response Report</h1>
        <div class="metadata">
            <strong>Session ID:</strong> {report.session_id}<br>
            <strong>Generated:</strong> {report.metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
            <strong>Incident:</strong> {report.incident_description}
        </div>
    </div>
""")

        # Executive Summary
        html.append("""
    <div class="section">
        <h2>📋 Executive Summary</h2>
""")
        html.append(f"<p>{report.executive_summary.incident_overview}</p>")
        html.append("<h3>Key Findings</h3>")
        html.append(f"<p>{report.executive_summary.key_findings.replace('- ', '<br>• ')}</p>")
        html.append("<h3>Impact Assessment</h3>")
        html.append(f"<p>{report.executive_summary.impact_assessment}</p>")
        html.append("<h3>Recommendations Summary</h3>")
        html.append(f"<p>{report.executive_summary.recommendations_summary}</p>")
        html.append("</div>\n")

        # MITRE ATT&CK
        html.append("""
    <div class="section">
        <h2>🎯 MITRE ATT&CK Mapping</h2>
""")
        if report.mitre_mappings:
            html.append('<table class="ioc-table">')
            html.append("<tr><th>Technique ID</th><th>Technique Name</th><th>Tactic</th><th>Related Findings</th></tr>")
            for mapping in report.mitre_mappings:
                findings_str = ", ".join(mapping.finding_references[:3])
                html.append(f"<tr><td><code>{mapping.technique_id}</code></td><td>{mapping.technique_name}</td>")
                html.append(f"<td>{mapping.tactic}</td><td>{findings_str}</td></tr>")
            html.append("</table>")
        else:
            html.append("<p><em>No MITRE ATT&CK techniques mapped.</em></p>")
        html.append("</div>\n")

        # IOC Tables
        html.append("""
    <div class="section">
        <h2>🚨 Indicators of Compromise (IOCs)</h2>
""")
        if report.ioc_tables:
            for ioc_type, entries in sorted(report.ioc_tables.items()):
                html.append(f"<h3>{ioc_type.upper()}</h3>")
                html.append('<table class="ioc-table">')
                html.append("<tr><th>IOC Value</th><th>Occurrences</th><th>Context</th></tr>")
                for entry in entries:
                    html.append(f'<tr><td><span class="ioc-value">{entry.value}</span></td>')
                    html.append(f"<td>{entry.occurrences}</td><td>{entry.context}</td></tr>")
                html.append("</table>")
        else:
            html.append("<p><em>No IOCs extracted during analysis.</em></p>")
        html.append("</div>\n")

        # Findings
        html.append("""
    <div class="section">
        <h2>🔍 Findings by Severity</h2>
""")
        for severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH, FindingSeverity.MEDIUM, FindingSeverity.LOW, FindingSeverity.INFO]:
            severity_findings = [f for f in report.findings if f.severity == severity]
            if severity_findings:
                for finding in severity_findings:
                    html.append(f'<div class="severity-{severity.value}">')
                    html.append(f"<h3>{finding.title}</h3>")
                    html.append(f"<p>{finding.description}</p>")
                    html.append(f"<p><strong>Confidence:</strong> {finding.confidence:.2f}</p>")
                    if finding.evidence:
                        html.append("<p><strong>Evidence:</strong></p><ul>")
                        for evidence in finding.evidence:
                            html.append(f"<li>{evidence}</li>")
                        html.append("</ul>")
                    html.append("</div>")
        html.append("</div>\n")

        # Recommendations
        html.append("""
    <div class="section">
        <h2>💡 Recommendations</h2>
""")
        if report.recommendations:
            for rec in report.recommendations:
                html.append('<div class="recommendation">')
                html.append(f'<span class="recommendation-priority">Priority {rec.priority}</span>')
                html.append(f"<strong>{rec.title}</strong>")
                html.append(f"<p>{rec.description}</p>")
                html.append(f"<p><small><strong>Urgency:</strong> {rec.urgency}</small></p>")
                html.append("</div>")
        html.append("</div>\n")

        # Attack Chain Graph
        if report.attack_graph and report.attack_graph.nodes:
            html.append(await self._generate_graph_html(report.attack_graph))

        # Footer
        html.append("""
</body>
</html>
""")

        return "".join(html)

    async def format_pdf(self, report: ReportSchema, output_path: Optional[Path]) -> str:
        """Format report as PDF.

        Args:
            report: Report schema
            output_path: Output file path

        Returns:
            Path to generated PDF file
        """
        if not output_path:
            raise ValueError("output_path required for PDF generation")

        # Validate output path
        output_path = Path(output_path)
        if not output_path.parent.exists():
            raise ValueError(f"Invalid output path: {output_path.parent} does not exist")

        # Generate HTML first
        html_content = await self.format_html(report)

        # Convert HTML to PDF using weasyprint (if available)
        try:
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(output_path)
            logger.info("pdf_generated", path=str(output_path))
            return str(output_path)
        except ImportError:
            logger.warning("weasyprint_not_available", fallback="html")
            # Fallback: save as HTML with .pdf extension warning
            html_path = output_path.with_suffix(".html")
            with open(html_path, "w") as f:
                f.write(html_content)
            raise ImportError(
                "weasyprint not installed. Install with: pip install weasyprint\n"
                f"HTML report saved to: {html_path}"
            )
