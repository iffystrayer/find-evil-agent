"""Test suite for ReporterAgent - Professional incident report generation.

This test suite follows the project's TDD methodology:
1. TestSpecification - Requirements and capabilities (ALWAYS PASSING)
2. TestStructure - Interface compliance (SKIPPED until implementation)
3. TestExecution - Core functionality (SKIPPED until implementation)
4. TestIntegration - System integration (SKIPPED until implementation)
5. TestErrorHandling - Error scenarios (SKIPPED until implementation)

The ReporterAgent must generate professional IR reports meeting Valhuntir quality standards:
- Executive summary with incident overview
- MITRE ATT&CK technique mapping
- IOC aggregation and tables (IPs, domains, hashes, files, emails, URLs)
- Timeline of events
- Findings organized by severity
- Recommendations based on findings
- Evidence citations linking to tool outputs
- Multiple output formats: Markdown, HTML, PDF
"""

import pytest
from datetime import datetime
from uuid import uuid4

# Conditional import for TDD - Component may not exist yet
try:
    from find_evil_agent.agents.reporter import ReporterAgent
    from find_evil_agent.agents.report_schemas import (
        ReportSchema, ReportFormat, ExecutiveSummary, MITREMapping,
        IOCTableEntry, TimelineEntry, Recommendation
    )
    REPORTER_AVAILABLE = True
except ImportError:
    REPORTER_AVAILABLE = False
    # Placeholder classes for testing structure
    class ReporterAgent:
        pass
    class ReportSchema:
        pass
    class ReportFormat:
        MARKDOWN = "markdown"
        HTML = "html"
        PDF = "pdf"
    class ExecutiveSummary:
        pass
    class MITREMapping:
        pass
    class IOCTableEntry:
        pass
    class TimelineEntry:
        pass
    class Recommendation:
        pass

from find_evil_agent.agents.base import BaseAgent
from find_evil_agent.agents.schemas import (
    Finding, FindingSeverity, AnalysisResult, IterativeAnalysisResult
)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_findings():
    """Sample findings for testing."""
    return [
        Finding(
            title="Suspicious Process Execution",
            description="Powershell.exe spawned from unusual parent process",
            severity=FindingSeverity.HIGH,
            confidence=0.85,
            evidence=["Process: powershell.exe", "Parent: winword.exe"],
            tool_references=["volatility", "pslist"],
            timestamp=datetime(2026, 4, 17, 10, 30, 0)
        ),
        Finding(
            title="Outbound Connection to Suspicious IP",
            description="Connection to known C2 server 192.168.100.50",
            severity=FindingSeverity.CRITICAL,
            confidence=0.95,
            evidence=["IP: 192.168.100.50", "Port: 443", "Process: powershell.exe"],
            tool_references=["volatility", "netscan"],
            timestamp=datetime(2026, 4, 17, 10, 31, 0)
        ),
        Finding(
            title="File Modification in System32",
            description="Suspicious DLL written to System32 directory",
            severity=FindingSeverity.HIGH,
            confidence=0.80,
            evidence=["Path: C:\\Windows\\System32\\evil.dll", "Hash: a1b2c3d4e5..."],
            tool_references=["fls"],
            timestamp=datetime(2026, 4, 17, 10, 32, 0)
        ),
        Finding(
            title="Registry Persistence Mechanism",
            description="New Run key added for persistence",
            severity=FindingSeverity.MEDIUM,
            confidence=0.75,
            evidence=["Key: HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"],
            tool_references=["volatility"],
            timestamp=datetime(2026, 4, 17, 10, 33, 0)
        ),
        Finding(
            title="Normal System Activity",
            description="Standard Windows service activity observed",
            severity=FindingSeverity.INFO,
            confidence=0.60,
            evidence=["Service: svchost.exe"],
            tool_references=["pslist"],
            timestamp=datetime(2026, 4, 17, 10, 34, 0)
        ),
    ]


@pytest.fixture
def sample_iocs():
    """Sample IOCs for testing."""
    return {
        "ipv4": ["192.168.100.50", "10.0.0.5", "172.16.1.100"],
        "domain": ["evil.com", "malware-c2.net"],
        "md5": ["5d41402abc4b2a76b9719d911017c592"],
        "sha256": ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
        "file_path_windows": ["C:\\Windows\\System32\\evil.dll", "C:\\Users\\victim\\malware.exe"],
        "email": ["attacker@evil.com"],
        "url": ["https://evil.com/payload", "http://malware-c2.net/beacon"],
    }


@pytest.fixture
def sample_analysis_result(sample_findings, sample_iocs):
    """Sample analysis result for testing."""
    return AnalysisResult(
        tool_name="volatility",
        findings=sample_findings,
        iocs=sample_iocs,
        raw_output="[Volatility output truncated]",
        parsed_output={"processes": 42, "connections": 8},
        analysis_summary="Analysis completed successfully"
    )


@pytest.fixture
def sample_iterative_result(sample_findings, sample_iocs):
    """Sample iterative analysis result for testing."""
    return IterativeAnalysisResult(
        session_id=str(uuid4()),
        incident_description="Ransomware detected on Windows endpoint",
        analysis_goal="Reconstruct complete attack chain",
        iterations=[],  # Simplified for testing
        investigation_chain=[],
        all_findings=sample_findings,
        all_iocs=sample_iocs,
        total_duration=45.6,
        stopping_reason="Max iterations reached",
        investigation_summary="Complete attack chain reconstructed",
        timestamp=datetime(2026, 4, 17, 10, 35, 0)
    )


# ============================================================================
# SPECIFICATION TESTS (Always Pass - Document Requirements)
# ============================================================================

class TestSpecification:
    """Test specification and requirements documentation.

    These tests ALWAYS PASS and serve as living documentation
    of the ReporterAgent's requirements and capabilities.
    """

    def test_reporter_requirements_specification(self):
        """Document ReporterAgent requirements and capabilities."""
        requirements = {
            "core_functionality": [
                "Generate professional incident response reports",
                "Support multiple output formats (Markdown, HTML, PDF)",
                "Create executive summary with incident overview",
                "Map findings to MITRE ATT&CK techniques",
                "Aggregate and present IOCs in structured tables",
                "Generate timeline of events from findings",
                "Organize findings by severity level",
                "Provide actionable recommendations",
                "Include evidence citations with tool references",
            ],
            "report_components": [
                "Executive Summary - High-level incident overview",
                "MITRE ATT&CK Mapping - Techniques and tactics identified",
                "IOC Tables - Structured tables of all IOC types",
                "Timeline - Chronological event sequence",
                "Findings by Severity - CRITICAL → HIGH → MEDIUM → LOW → INFO",
                "Evidence Citations - Links to source tool outputs",
                "Recommendations - Prioritized action items",
                "Metadata - Session ID, timestamps, tool usage stats",
            ],
            "output_formats": [
                "Markdown - Human-readable, version-controllable",
                "HTML - Professional browser-viewable report",
                "PDF - Print-ready, shareable document",
            ],
            "quality_standards": {
                "benchmark": "Valhuntir by AppliedIR (SANS Author Steve Anson)",
                "executive_summary": "3-5 paragraphs covering incident, impact, findings",
                "mitre_coverage": "Map all findings to ATT&CK techniques where applicable",
                "ioc_presentation": "Separate tables per IOC type with deduplication",
                "timeline_accuracy": "Chronological ordering with timestamps",
                "recommendations": "Prioritized, actionable, severity-based",
                "evidence_traceability": "Each finding links to source tools",
                "professional_formatting": "Structured sections, clear hierarchy",
            },
            "input_data": [
                "AnalysisResult - Single analysis findings and IOCs",
                "IterativeAnalysisResult - Multi-iteration investigation results",
                "Agent execution metadata - Tools used, timing, session info",
            ],
            "integration_points": [
                "CLI - Called from analyze and investigate commands",
                "API - Exposed via REST endpoints",
                "Orchestrator - Integrated into LangGraph workflow",
                "Storage - Save reports to filesystem or serve via HTTP",
            ],
        }

        # This test always passes - it documents requirements
        assert requirements["core_functionality"]
        assert requirements["report_components"]
        assert requirements["output_formats"]
        assert requirements["quality_standards"]
        assert requirements["input_data"]
        assert requirements["integration_points"]

    def test_reporter_workflow_position(self):
        """Document ReporterAgent position in workflow."""
        workflow = {
            "position": "Final stage - after all analysis complete",
            "inputs": [
                "All findings from AnalyzerAgent",
                "All IOCs extracted across all iterations",
                "Tool selection and execution history",
                "Session metadata and timing information",
            ],
            "outputs": [
                "Professional IR report in requested format(s)",
                "Report saved to filesystem or returned for serving",
                "Report metadata for audit trail",
            ],
            "dependencies": {
                "upstream": ["ToolSelectorAgent", "ToolExecutorAgent", "AnalyzerAgent"],
                "downstream": ["CLI output handlers", "API response formatters"],
            },
            "error_handling": [
                "Graceful degradation if PDF generation fails (fallback to HTML)",
                "Generate partial report if some components fail",
                "Include generation errors in report metadata",
            ],
        }

        assert workflow["position"]
        assert workflow["inputs"]
        assert workflow["outputs"]


# ============================================================================
# STRUCTURE TESTS (Skipped Until Implementation)
# ============================================================================

class TestStructure:
    """Test ReporterAgent interface compliance and structure.

    These tests verify the agent implements required interfaces
    and has the expected structure. Skipped until implementation.
    """

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    def test_inherits_from_base_agent(self):
        """Verify ReporterAgent inherits from BaseAgent."""
        assert issubclass(ReporterAgent, BaseAgent)

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    def test_has_required_methods(self):
        """Verify ReporterAgent has all required methods."""
        agent = ReporterAgent()
        assert hasattr(agent, "process")
        assert hasattr(agent, "generate_report")
        assert hasattr(agent, "format_markdown")
        assert hasattr(agent, "format_html")
        assert hasattr(agent, "format_pdf")
        assert hasattr(agent, "create_executive_summary")
        assert hasattr(agent, "map_mitre_attacks")
        assert hasattr(agent, "aggregate_iocs")
        assert hasattr(agent, "generate_timeline")
        assert hasattr(agent, "generate_recommendations")

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReportSchema not implemented yet")
    def test_report_schema_structure(self):
        """Verify ReportSchema has required fields."""
        from find_evil_agent.agents.report_schemas import ReportMetadata

        schema = ReportSchema(
            session_id="test-session",
            incident_description="Test incident description for schema validation purposes",
            executive_summary=ExecutiveSummary(
                incident_overview="This is a test incident overview that provides sufficient detail about what happened during the incident and when it occurred for validation purposes.",
                key_findings="These are the test key findings with enough detail to pass validation requirements.",
                impact_assessment="This is the test impact assessment with sufficient information about the impact.",
                recommendations_summary="These are the test recommendations summary with adequate detail for validation."
            ),
            findings=[],
            ioc_tables={},
            timeline=[],
            mitre_mappings=[],
            recommendations=[],
            metadata=ReportMetadata(
                session_id="test-session",
                format=ReportFormat.MARKDOWN
            )
        )

        assert hasattr(schema, "session_id")
        assert hasattr(schema, "incident_description")
        assert hasattr(schema, "executive_summary")
        assert hasattr(schema, "findings")
        assert hasattr(schema, "ioc_tables")
        assert hasattr(schema, "timeline")
        assert hasattr(schema, "mitre_mappings")
        assert hasattr(schema, "recommendations")
        assert hasattr(schema, "metadata")


# ============================================================================
# EXECUTION TESTS (Skipped Until Implementation)
# ============================================================================

class TestExecution:
    """Test ReporterAgent core functionality.

    These tests verify the agent correctly generates professional reports
    with all required components. Skipped until implementation.
    """

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_generate_markdown_report_from_analysis_result(self, sample_analysis_result):
        """Test generating markdown report from AnalysisResult."""
        agent = ReporterAgent()

        report = await agent.generate_report(
            analysis_result=sample_analysis_result,
            format=ReportFormat.MARKDOWN,
            session_id="test-session-001",
            incident_description="Ransomware attack on endpoint"
        )

        assert report is not None
        assert "# Find Evil Agent - Incident Response Report" in report
        assert "## Executive Summary" in report
        assert "## MITRE ATT&CK Mapping" in report
        assert "## Indicators of Compromise (IOCs)" in report
        assert "## Findings by Severity" in report
        assert "## Timeline" in report
        assert "## Recommendations" in report
        assert "192.168.100.50" in report  # Check IOC included
        assert "Suspicious Process Execution" in report  # Check finding included

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_generate_html_report(self, sample_analysis_result):
        """Test generating HTML report with professional styling."""
        agent = ReporterAgent()

        report = await agent.generate_report(
            analysis_result=sample_analysis_result,
            format=ReportFormat.HTML,
            session_id="test-session-002"
        )

        assert report is not None
        assert "<!DOCTYPE html>" in report
        assert "<html" in report
        assert "<head>" in report
        assert "<style>" in report  # Should include CSS
        assert "<body>" in report
        assert "class=\"severity-critical\"" in report  # Check severity styling
        assert "class=\"ioc-table\"" in report  # Check IOC table styling

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_generate_pdf_report(self, sample_analysis_result, tmp_path):
        """Test generating PDF report."""
        agent = ReporterAgent()

        output_path = tmp_path / "report.pdf"

        await agent.generate_report(
            analysis_result=sample_analysis_result,
            format=ReportFormat.PDF,
            output_path=output_path,
            session_id="test-session-003"
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0  # PDF should have content

        # Verify PDF magic bytes
        with open(output_path, "rb") as f:
            magic = f.read(4)
            assert magic == b"%PDF"

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_executive_summary_generation(self, sample_findings):
        """Test executive summary contains key incident information."""
        agent = ReporterAgent()

        summary = await agent.create_executive_summary(
            findings=sample_findings,
            incident_description="Ransomware detected on Windows endpoint",
            analysis_goal="Identify malware and C2 infrastructure"
        )

        assert summary is not None
        assert hasattr(summary, "incident_overview")
        assert hasattr(summary, "key_findings")
        assert hasattr(summary, "impact_assessment")
        assert hasattr(summary, "recommendations_summary")

        # Verify content quality
        assert len(summary.incident_overview) >= 100  # Substantial overview
        assert "ransomware" in summary.incident_overview.lower()
        assert summary.key_findings  # Should list key findings
        assert "critical" in summary.key_findings.lower()  # Should mention critical finding

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_mitre_attack_mapping(self, sample_findings):
        """Test MITRE ATT&CK technique mapping from findings."""
        agent = ReporterAgent()

        mappings = await agent.map_mitre_attacks(findings=sample_findings)

        assert mappings is not None
        assert len(mappings) > 0

        # Check for expected techniques based on findings
        techniques = [m.technique_id for m in mappings]
        assert any("T1059" in t for t in techniques)  # Command and Scripting Interpreter (PowerShell)
        assert any("T1071" in t for t in techniques)  # Application Layer Protocol (C2)

        # Verify mapping structure
        for mapping in mappings:
            assert hasattr(mapping, "technique_id")
            assert hasattr(mapping, "technique_name")
            assert hasattr(mapping, "tactic")
            assert hasattr(mapping, "finding_references")
            assert mapping.finding_references  # Should reference findings

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_ioc_aggregation_and_deduplication(self, sample_iocs):
        """Test IOC aggregation with deduplication and table formatting."""
        agent = ReporterAgent()

        # Add duplicate IOCs
        iocs_with_dupes = {
            "ipv4": sample_iocs["ipv4"] + ["192.168.100.50", "10.0.0.5"],  # Duplicates
            "domain": sample_iocs["domain"] + ["evil.com"],  # Duplicate
            "md5": sample_iocs["md5"],
            "sha256": sample_iocs["sha256"],
            "file_path_windows": sample_iocs["file_path_windows"],
            "email": sample_iocs["email"],
            "url": sample_iocs["url"],
        }

        ioc_tables = await agent.aggregate_iocs(iocs=iocs_with_dupes)

        assert ioc_tables is not None
        assert "ipv4" in ioc_tables
        assert "domain" in ioc_tables

        # Verify deduplication
        assert len(ioc_tables["ipv4"]) == 3  # Original 3, not 5
        assert len(ioc_tables["domain"]) == 2  # Original 2, not 3

        # Verify table structure
        for ioc_type, table in ioc_tables.items():
            assert isinstance(table, list)
            for entry in table:
                assert "value" in entry
                assert "first_seen" in entry or "count" in entry  # Should track occurrences

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_timeline_generation(self, sample_findings):
        """Test timeline generation from findings with chronological ordering."""
        agent = ReporterAgent()

        timeline = await agent.generate_timeline(findings=sample_findings)

        assert timeline is not None
        assert len(timeline) == len(sample_findings)

        # Verify chronological ordering
        timestamps = [entry.timestamp for entry in timeline]
        assert timestamps == sorted(timestamps)

        # Verify timeline entry structure
        for entry in timeline:
            assert hasattr(entry, "timestamp")
            assert hasattr(entry, "event_description")
            assert hasattr(entry, "severity")
            assert hasattr(entry, "source_finding")

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_recommendations_generation(self, sample_findings):
        """Test recommendations based on severity and findings."""
        agent = ReporterAgent()

        recommendations = await agent.generate_recommendations(findings=sample_findings)

        assert recommendations is not None
        assert len(recommendations) > 0

        # Should prioritize based on severity
        critical_high_count = sum(
            1 for f in sample_findings
            if f.severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH]
        )
        assert len(recommendations) >= critical_high_count  # At least one per critical/high finding

        # Verify recommendation structure
        for rec in recommendations:
            assert hasattr(rec, "priority")
            assert hasattr(rec, "title")
            assert hasattr(rec, "description")
            assert hasattr(rec, "related_findings")
            assert rec.related_findings  # Should reference findings

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_findings_organized_by_severity(self, sample_findings):
        """Test findings are organized by severity in report."""
        agent = ReporterAgent()

        report = await agent.generate_report(
            analysis_result=AnalysisResult(
                tool_name="test",
                findings=sample_findings,
                iocs={},
                raw_output="",
            ),
            format=ReportFormat.MARKDOWN,
            session_id="test"
        )

        # Find severity section positions
        critical_pos = report.find("### CRITICAL")
        high_pos = report.find("### HIGH")
        medium_pos = report.find("### MEDIUM")
        low_pos = report.find("### LOW")
        info_pos = report.find("### INFO")

        # Verify correct ordering (CRITICAL → HIGH → MEDIUM → LOW → INFO)
        assert critical_pos < high_pos < medium_pos < low_pos < info_pos

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_evidence_citations_included(self, sample_findings):
        """Test report includes evidence citations linking to tool outputs."""
        agent = ReporterAgent()

        report = await agent.generate_report(
            analysis_result=AnalysisResult(
                tool_name="volatility",
                findings=sample_findings,
                iocs={},
                raw_output="",
            ),
            format=ReportFormat.MARKDOWN,
            session_id="test"
        )

        # Verify evidence citations
        assert "**Evidence:**" in report or "**Source:**" in report
        assert "volatility" in report  # Tool reference
        assert "pslist" in report  # Tool reference
        assert "Process: powershell.exe" in report  # Evidence item

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_report_metadata_included(self, sample_analysis_result):
        """Test report includes comprehensive metadata."""
        agent = ReporterAgent()

        report = await agent.generate_report(
            analysis_result=sample_analysis_result,
            format=ReportFormat.MARKDOWN,
            session_id="test-session-123",
            incident_description="Test incident"
        )

        # Verify metadata sections
        assert "test-session-123" in report
        assert "Test incident" in report
        assert "Generated:" in report or "Report Date:" in report
        assert "Tools Used:" in report or "Analysis Tools:" in report


# ============================================================================
# INTEGRATION TESTS (Skipped Until Implementation)
# ============================================================================

class TestIntegration:
    """Test ReporterAgent integration with system components.

    These tests verify the agent integrates correctly with
    other agents and system infrastructure.
    """

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_integration_with_iterative_analysis(self, sample_iterative_result):
        """Test report generation from IterativeAnalysisResult."""
        agent = ReporterAgent()

        report = await agent.generate_report(
            iterative_result=sample_iterative_result,
            format=ReportFormat.MARKDOWN
        )

        assert report is not None
        assert "Investigation Chain" in report or "Autonomous Investigation" in report
        assert "Iteration" in report  # Should show iteration details
        assert sample_iterative_result.stopping_reason in report

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_process_method_integration(self, sample_analysis_result):
        """Test process() method follows BaseAgent interface."""
        agent = ReporterAgent()

        result = await agent.process({
            "analysis_result": sample_analysis_result,
            "format": "markdown",
            "session_id": "test",
        })

        assert result is not None
        assert hasattr(result, "status")
        assert hasattr(result, "data")
        assert "report" in result.data

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_multiple_format_generation(self, sample_analysis_result, tmp_path):
        """Test generating multiple report formats simultaneously."""
        agent = ReporterAgent()

        formats = [ReportFormat.MARKDOWN, ReportFormat.HTML, ReportFormat.PDF]
        outputs = {
            ReportFormat.MARKDOWN: tmp_path / "report.md",
            ReportFormat.HTML: tmp_path / "report.html",
            ReportFormat.PDF: tmp_path / "report.pdf",
        }

        for format_type, output_path in outputs.items():
            await agent.generate_report(
                analysis_result=sample_analysis_result,
                format=format_type,
                output_path=output_path,
                session_id="test"
            )

            assert output_path.exists()
            assert output_path.stat().st_size > 0


# ============================================================================
# ERROR HANDLING TESTS (Skipped Until Implementation)
# ============================================================================

class TestErrorHandling:
    """Test ReporterAgent error handling and edge cases."""

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_handles_empty_findings_gracefully(self):
        """Test report generation with no findings."""
        agent = ReporterAgent()

        result = AnalysisResult(
            tool_name="test",
            findings=[],
            iocs={},
            raw_output="No suspicious activity detected"
        )

        report = await agent.generate_report(
            analysis_result=result,
            format=ReportFormat.MARKDOWN,
            session_id="test"
        )

        assert report is not None
        assert "No suspicious findings" in report or "No findings detected" in report

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_handles_empty_iocs_gracefully(self, sample_findings):
        """Test report generation with no IOCs."""
        agent = ReporterAgent()

        result = AnalysisResult(
            tool_name="test",
            findings=sample_findings,
            iocs={},  # No IOCs
            raw_output="Test output"
        )

        report = await agent.generate_report(
            analysis_result=result,
            format=ReportFormat.MARKDOWN,
            session_id="test"
        )

        assert report is not None
        assert "No IOCs extracted" in report or "No indicators" in report

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_pdf_generation_fallback_to_html(self, sample_analysis_result):
        """Test PDF generation falls back to HTML if PDF engine unavailable."""
        agent = ReporterAgent()

        # This should not raise even if PDF generation fails
        report = await agent.generate_report(
            analysis_result=sample_analysis_result,
            format=ReportFormat.PDF,
            session_id="test",
            fallback_to_html=True
        )

        # Should get HTML if PDF fails
        assert report is not None
        assert ("<html" in report) or (report.endswith(".pdf"))

    @pytest.mark.skipif(not REPORTER_AVAILABLE, reason="ReporterAgent not implemented yet")
    @pytest.mark.asyncio
    async def test_handles_invalid_output_path(self, sample_analysis_result):
        """Test error handling for invalid output path."""
        agent = ReporterAgent()

        with pytest.raises(ValueError, match="Invalid output path"):
            await agent.generate_report(
                analysis_result=sample_analysis_result,
                format=ReportFormat.PDF,
                output_path="/nonexistent/directory/report.pdf",
                session_id="test"
            )
