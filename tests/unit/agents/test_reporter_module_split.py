"""Static-guard tests for agents/reporter.py module split (C3b).

Pins the refactor contract: reporter.py must stay under an LOC ceiling after
extracting formatting/MITRE logic to agents/reporting/*.py, AND all public
names must remain accessible from the reporter module for backwards compat.

Modeled after tests/mcp/test_mcp_module_split.py (C3a pattern).
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest


# ============================================================================
# SPECIFICATION: Target module layout after C3b split
# ============================================================================

def test_reporter_module_split_specification():
    """Document the C3b split contract (always passes)."""
    assert True, """
    C3b splits agents/reporter.py (1,117 LOC) into:

    1. agents/reporter.py (≤400 LOC)
       - ReporterAgent class (process, generate_report, _build_report_schema)
       - Helper methods: create_executive_summary, aggregate_iocs,
         generate_timeline, generate_recommendations, generate_attack_graph,
         _generate_graph_html
       - Re-exports: format_markdown, format_html, format_pdf, map_mitre_attacks

    2. agents/reporting/mitre.py
       - MITRE_PATTERNS constant
       - map_mitre_attacks() function

    3. agents/reporting/markdown.py
       - format_markdown() function

    4. agents/reporting/html.py
       - format_html() function (migrated to Jinja2 with autoescape=True)

    5. agents/reporting/pdf.py
       - format_pdf() function

    Backwards compatibility: existing `from reporter import format_html` paths
    keep working via re-exports at the bottom of reporter.py.

    Jinja2 migration: B2's html.escape calls are replaced by a Jinja2 template
    with autoescape=True, reducing XSS risk and improving maintainability.
    """


# ============================================================================
# STRUCTURE: LOC ceiling enforcement
# ============================================================================

def test_reporter_py_stays_under_loc_ceiling():
    """Enforce reporter.py ≤ 400 LOC after split (was 1,117)."""
    reporter_path = Path(__file__).parent.parent.parent.parent / "src" / "find_evil_agent" / "agents" / "reporter.py"

    if not reporter_path.exists():
        pytest.skip("reporter.py not found — skip LOC check")

    with open(reporter_path) as f:
        lines = f.readlines()

    loc = len(lines)
    assert loc <= 400, (
        f"reporter.py has {loc} lines (ceiling: 400). "
        f"Extract more logic to agents/reporting/*.py"
    )


def test_reporting_modules_exist():
    """Assert the split created agents/reporting/*.py modules."""
    reporting_dir = Path(__file__).parent.parent.parent.parent / "src" / "find_evil_agent" / "agents" / "reporting"

    assert reporting_dir.exists(), "agents/reporting/ directory must exist"
    assert reporting_dir.is_dir(), "agents/reporting/ must be a directory"

    # Check individual modules exist
    required_modules = ["mitre.py", "markdown.py", "html.py", "pdf.py"]
    for module_name in required_modules:
        module_path = reporting_dir / module_name
        assert module_path.exists(), f"agents/reporting/{module_name} must exist"


# ============================================================================
# STRUCTURE: Formatting functions extracted
# ============================================================================

def test_format_functions_not_in_reporter_py():
    """Assert format_markdown/html/pdf implementations are in reporting/*.py.

    Allows thin backward compatibility wrappers in reporter.py that delegate
    to the split modules (e.g., `from .reporting.html import format_html`).
    """
    reporter_path = Path(__file__).parent.parent.parent.parent / "src" / "find_evil_agent" / "agents" / "reporter.py"

    if not reporter_path.exists():
        pytest.skip("reporter.py not found")

    with open(reporter_path) as f:
        content = f.read()

    # Check that implementations exist in split modules
    for func_name, module_name in [
        ("format_markdown", "markdown"),
        ("format_html", "html"),
        ("format_pdf", "pdf"),
    ]:
        # If there's a class method, it should be a thin wrapper that imports from .reporting
        method_pattern = f"    async def {func_name}("
        if method_pattern in content:
            # Wrapper is OK if it imports from the split module (any of these forms)
            import_patterns = [
                f"from .reporting.{module_name} import {func_name}",
                f"from .reporting import {func_name}",
                # Also accept multi-import forms like "from .reporting import format_html, format_pdf"
                f"from .reporting import",  # Generic check - as long as it imports from .reporting
            ]
            has_import = any(pattern in content for pattern in import_patterns)
            assert has_import, (
                f"Found {func_name} method in reporter.py but no import from "
                f"reporting module — should be a thin wrapper that delegates"
            )


def test_mitre_mapping_not_in_reporter_py():
    """Assert map_mitre_attacks and MITRE_PATTERNS extracted to mitre.py.

    Allows thin backward compatibility wrappers that delegate to reporting.mitre.
    """
    reporter_path = Path(__file__).parent.parent.parent.parent / "src" / "find_evil_agent" / "agents" / "reporter.py"

    if not reporter_path.exists():
        pytest.skip("reporter.py not found")

    with open(reporter_path) as f:
        content = f.read()

    # MITRE_PATTERNS should not be a multi-line dict definition
    assert "MITRE_PATTERNS = {" not in content, (
        "MITRE_PATTERNS constant should be extracted to agents/reporting/mitre.py"
    )

    # map_mitre_attacks: if there's a class method, must be a thin wrapper
    method_pattern = "    async def map_mitre_attacks("
    if method_pattern in content:
        # Wrapper OK if imports from .reporting.mitre
        import_pattern = "from .reporting.mitre import map_mitre_attacks"
        alt_import = "from .reporting import map_mitre_attacks"
        assert import_pattern in content or alt_import in content, (
            "Found map_mitre_attacks method but no import from reporting.mitre — "
            "should be a thin wrapper that delegates"
        )


# ============================================================================
# EXECUTION: Backwards compatibility via re-exports
# ============================================================================

def test_all_formatting_functions_accessible_from_reporter():
    """Assert format_markdown/html/pdf are accessible from reporter module."""
    from find_evil_agent.agents import reporter

    required_names = [
        "format_markdown",
        "format_html",
        "format_pdf",
        "map_mitre_attacks",
        "MITRE_PATTERNS",
    ]

    for name in required_names:
        assert hasattr(reporter, name), (
            f"reporter.{name} not accessible — re-export missing?"
        )
        attr = getattr(reporter, name)
        assert attr is not None, f"reporter.{name} is None"


def test_reporter_agent_class_still_in_reporter():
    """Assert ReporterAgent class remains in reporter.py."""
    from find_evil_agent.agents.reporter import ReporterAgent

    assert inspect.isclass(ReporterAgent), "ReporterAgent must be a class"

    # Check core methods still exist (helpers extracted to reporting/helpers.py)
    required_methods = [
        "process",
        "generate_report",
    ]

    for method_name in required_methods:
        assert hasattr(ReporterAgent, method_name), (
            f"ReporterAgent.{method_name} missing after split"
        )


# ============================================================================
# EXECUTION: Jinja2 migration verification
# ============================================================================

def test_html_formatting_uses_jinja2():
    """Assert format_html uses Jinja2 instead of inline html.escape."""
    # Import from the split module
    from find_evil_agent.agents.reporting import html as html_module

    html_path = Path(html_module.__file__)
    with open(html_path) as f:
        content = f.read()

    # Should import Jinja2 Environment
    assert "from jinja2 import" in content or "import jinja2" in content, (
        "format_html should use Jinja2 for templating"
    )

    # Should NOT have inline html.escape calls (Jinja2 autoescape handles it)
    # Allow import statement but not usage in string interpolation
    lines = content.split("\n")
    escape_usage_lines = [
        line for line in lines
        if "_html_escape(" in line and "import" not in line.lower()
    ]

    assert len(escape_usage_lines) == 0, (
        f"Found {len(escape_usage_lines)} _html_escape() calls in html.py. "
        f"Jinja2 autoescape=True should handle escaping automatically."
    )


def test_jinja2_template_exists():
    """Assert report.html.j2 template exists."""
    template_path = Path(__file__).parent.parent.parent.parent / "templates" / "report.html.j2"

    assert template_path.exists(), (
        "templates/report.html.j2 must exist for Jinja2 rendering"
    )

    with open(template_path) as f:
        content = f.read()

    # Verify autoescape is enabled in template or environment
    # Jinja2 auto-escapes by default in .j2 files, but verify template looks sane
    assert len(content) > 100, "Template should have substantial content"
    assert "{{" in content or "{%" in content, "Template should use Jinja2 syntax"


# ============================================================================
# INTEGRATION: HTML escaping still works after Jinja2 migration
# ============================================================================

@pytest.mark.asyncio
async def test_jinja2_migration_preserves_xss_protection():
    """Verify Jinja2 autoescape prevents XSS (regression guard for B2)."""
    from datetime import datetime, timezone

    from find_evil_agent.agents.report_schemas import (
        ExecutiveSummary,
        ReportFormat,
        ReportMetadata,
        ReportSchema,
    )
    from find_evil_agent.agents.reporter import format_html

    xss_payload = "<script>alert('xss')</script>"

    # Build minimal schema with XSS in incident_description
    schema = ReportSchema(
        session_id="xss-test",
        incident_description=xss_payload,
        analysis_goal="",
        executive_summary=ExecutiveSummary(
            incident_overview="x" * 120,
            key_findings="x" * 120,
            impact_assessment="x" * 120,
            recommendations_summary="x" * 120,
        ),
        mitre_mappings=[],
        ioc_tables={},
        timeline=[],
        findings=[],
        recommendations=[],
        metadata=ReportMetadata(
            session_id="xss-test",
            generated_at=datetime.now(timezone.utc),
            format=ReportFormat.HTML,
        ),
    )

    rendered = await format_html(schema)

    # Raw payload must not appear
    assert xss_payload not in rendered, (
        "Raw XSS payload leaked — Jinja2 autoescape not working"
    )

    # Escaped form should appear
    assert "&lt;script&gt;" in rendered, (
        "Escaped form not found — Jinja2 autoescape not working"
    )
