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

After C3b split, formatting logic is in agents/reporting/*.py modules.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
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
        # Import formatting functions
        from .reporting import format_markdown, format_html, format_pdf

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
            content = await format_markdown(report_schema, iterative_result=iterative_result)
        elif format == ReportFormat.HTML:
            content = await format_html(report_schema)
        elif format == ReportFormat.PDF:
            try:
                return await format_pdf(report_schema, output_path, format_html)
            except ValueError as e:
                # Re-raise validation errors about invalid paths (parent doesn't exist)
                if "Invalid output path" in str(e):
                    raise
                # For missing output_path, use fallback if enabled
                logger.warning("pdf_generation_failed", error=str(e), fallback=fallback_to_html)
                if fallback_to_html:
                    return await format_html(report_schema)
                raise
            except Exception as e:
                logger.warning("pdf_generation_failed", error=str(e), fallback=fallback_to_html)
                if fallback_to_html:
                    return await format_html(report_schema)
                raise

        # Write to output_path if provided for non-PDF formats
        if output_path and content:
            output_path = Path(output_path)
            if not output_path.parent.exists():
                raise ValueError(f"Invalid output path: {output_path.parent} does not exist")
            # Use aiofiles for async file I/O
            import aiofiles
            async with aiofiles.open(output_path, "w") as f:
                await f.write(content)
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
        from .reporting import map_mitre_attacks
        from .reporting.helpers import (
            create_executive_summary,
            aggregate_iocs,
            generate_timeline,
            generate_recommendations,
            generate_attack_graph,
        )

        # Generate all report components
        executive_summary = await create_executive_summary(
            findings=findings,
            incident_description=incident_description,
            analysis_goal=analysis_goal,
        )

        mitre_mappings = await map_mitre_attacks(findings=findings)
        ioc_tables = await aggregate_iocs(iocs=iocs)
        timeline = await generate_timeline(findings=findings)
        recommendations = await generate_recommendations(findings=findings)
        attack_graph = await generate_attack_graph(findings=findings)

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

    # ========================================================================
    # Backwards compatibility wrappers (delegate to helpers in reporting/)
    # ========================================================================

    async def create_executive_summary(
        self, findings: list[Finding], incident_description: str, analysis_goal: str
    ) -> ExecutiveSummary:
        """Wrapper for backwards compatibility - delegates to helpers.create_executive_summary."""
        from .reporting.helpers import create_executive_summary
        return await create_executive_summary(findings, incident_description, analysis_goal)

    async def aggregate_iocs(self, iocs: dict[str, list[str]]) -> dict[str, list[dict]]:
        """Wrapper for backwards compatibility - delegates to helpers.aggregate_iocs."""
        from .reporting.helpers import aggregate_iocs
        return await aggregate_iocs(iocs)

    async def generate_timeline(self, findings: list[Finding]) -> list[TimelineEntry]:
        """Wrapper for backwards compatibility - delegates to helpers.generate_timeline."""
        from .reporting.helpers import generate_timeline
        return await generate_timeline(findings)

    async def generate_recommendations(self, findings: list[Finding]) -> list[Recommendation]:
        """Wrapper for backwards compatibility - delegates to helpers.generate_recommendations."""
        from .reporting.helpers import generate_recommendations
        return await generate_recommendations(findings)

    async def generate_attack_graph(self, findings: list[Finding]) -> Optional[AttackGraph]:
        """Wrapper for backwards compatibility - delegates to helpers.generate_attack_graph."""
        from .reporting.helpers import generate_attack_graph
        return await generate_attack_graph(findings)

    async def map_mitre_attacks(self, findings: list[Finding]) -> list[MITREMapping]:
        """Wrapper for backwards compatibility - delegates to mitre.map_mitre_attacks."""
        from .reporting import map_mitre_attacks
        return await map_mitre_attacks(findings)

    async def format_markdown(
        self, report: ReportSchema, iterative_result: Optional[IterativeAnalysisResult] = None
    ) -> str:
        """Wrapper for backwards compatibility - delegates to markdown.format_markdown."""
        from .reporting import format_markdown
        return await format_markdown(report, iterative_result)

    async def format_html(self, report: ReportSchema) -> str:
        """Wrapper for backwards compatibility - delegates to html.format_html."""
        from .reporting import format_html
        return await format_html(report)

    async def format_pdf(self, report: ReportSchema, output_path: Optional[Path]) -> str:
        """Wrapper for backwards compatibility - delegates to pdf.format_pdf."""
        from .reporting import format_html, format_pdf
        return await format_pdf(report, output_path, format_html)

    async def _generate_graph_html(self, attack_graph: AttackGraph) -> str:
        """Wrapper for backwards compatibility - delegates to html._generate_graph_html."""
        from .reporting.html import _generate_graph_html
        return await _generate_graph_html(attack_graph)


# ============================================================================
# Backwards compatibility exports
# ============================================================================
# Import split modules to register and re-export for backwards compatibility.
# After C3b split, formatting logic moved to agents/reporting/*.py.
# Existing `from find_evil_agent.agents.reporter import format_html` paths
# continue to work via these re-exports.

from .reporting import (
    format_html,
    format_markdown,
    format_pdf,
    map_mitre_attacks,
    MITRE_PATTERNS,
)

__all__ = [
    "ReporterAgent",
    "format_html",
    "format_markdown",
    "format_pdf",
    "map_mitre_attacks",
    "MITRE_PATTERNS",
]
