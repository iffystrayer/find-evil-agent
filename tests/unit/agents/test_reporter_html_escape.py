"""HTML escape tests for ReporterAgent.format_html.

Covers B2 of the May 2026 remediation cycle: every user-controlled value
interpolated into the HTML report MUST be html-escaped to prevent XSS via
incident description, IOC values, finding titles/descriptions, recommendation
text, MITRE technique names, etc.

Tests use real ReporterAgent + real ReportSchema models — no mocks. Each
test seeds a malicious payload into a different field and asserts:
  1. The raw payload does NOT appear verbatim in the rendered HTML.
  2. The escaped form (e.g. ``&lt;script&gt;``) DOES appear.
"""

from __future__ import annotations

import html as html_lib
from datetime import datetime, timezone

import pytest

from find_evil_agent.agents.report_schemas import (
    ExecutiveSummary,
    IOCTableEntry,
    MITREMapping,
    Recommendation,
    ReportFormat,
    ReportMetadata,
    ReportSchema,
)
from find_evil_agent.agents.reporter import ReporterAgent
from find_evil_agent.agents.schemas import Finding, FindingSeverity

XSS_PAYLOAD = "<script>alert('xss')</script>"
XSS_IMG = '<img src=x onerror="alert(1)">'


def _baseline_summary(text_prefix: str = "") -> ExecutiveSummary:
    """Build a valid ExecutiveSummary with min_length-satisfying text."""
    pad = "x" * 120
    return ExecutiveSummary(
        incident_overview=f"{text_prefix}{pad}",
        key_findings=f"{text_prefix}{pad}",
        impact_assessment=f"{text_prefix}{pad}",
        recommendations_summary=f"{text_prefix}{pad}",
    )


def _baseline_metadata() -> ReportMetadata:
    return ReportMetadata(
        session_id="sess-xss-test",
        generated_at=datetime(2026, 5, 6, 12, 0, 0, tzinfo=timezone.utc),
        format=ReportFormat.HTML,
    )


def _build_schema(**overrides) -> ReportSchema:
    """Construct a minimal valid ReportSchema with override-friendly fields."""
    defaults = dict(
        session_id="sess-xss-test",
        incident_description="Routine incident.",
        analysis_goal="",
        executive_summary=_baseline_summary(),
        mitre_mappings=[],
        ioc_tables={},
        timeline=[],
        findings=[],
        recommendations=[],
        metadata=_baseline_metadata(),
    )
    defaults.update(overrides)
    return ReportSchema(**defaults)


def _assert_payload_escaped(rendered: str, payload: str) -> None:
    """Assert the raw payload is gone and dangerous characters are escaped.

    Note: We check that dangerous characters (&lt; &gt; &quot; &#39; or &#x27;)
    are escaped, not the exact encoding format. Jinja2 autoescape produces
    decimal entities (&#39;, &#34;) while Python's html.escape() produces
    mixed hex/decimal (&#x27;, &quot;). Both are valid and safe.
    """
    assert payload not in rendered, (
        f"Raw XSS payload leaked into rendered HTML: {payload!r}"
    )

    # Check that dangerous characters are escaped (accept either format)
    # < → &lt;  > → &gt;  " → &quot; or &#34;  ' → &#39; or &#x27;
    for char in payload:
        if char == '<':
            assert '&lt;' in rendered, "< character not escaped"
        elif char == '>':
            assert '&gt;' in rendered, "> character not escaped"
        elif char == '"':
            assert ('&quot;' in rendered or '&#34;' in rendered), '" character not escaped'
        elif char == "'":
            assert ('&#39;' in rendered or '&#x27;' in rendered), "' character not escaped"


@pytest.mark.asyncio
async def test_incident_description_is_escaped():
    schema = _build_schema(incident_description=XSS_PAYLOAD)
    rendered = await ReporterAgent().format_html(schema)
    _assert_payload_escaped(rendered, XSS_PAYLOAD)


@pytest.mark.asyncio
async def test_executive_summary_overview_is_escaped():
    summary = _baseline_summary()
    summary.incident_overview = XSS_IMG + ("y" * 100)
    schema = _build_schema(executive_summary=summary)
    rendered = await ReporterAgent().format_html(schema)
    _assert_payload_escaped(rendered, XSS_IMG)


@pytest.mark.asyncio
async def test_executive_summary_impact_is_escaped():
    summary = _baseline_summary()
    summary.impact_assessment = XSS_PAYLOAD + ("y" * 100)
    schema = _build_schema(executive_summary=summary)
    rendered = await ReporterAgent().format_html(schema)
    _assert_payload_escaped(rendered, XSS_PAYLOAD)


@pytest.mark.asyncio
async def test_mitre_mapping_fields_are_escaped():
    mapping = MITREMapping(
        technique_id=XSS_PAYLOAD,
        technique_name='"><svg onload=alert(1)>',
        tactic="<b>Initial Access</b>",
        finding_references=["<i>finding-1</i>"],
    )
    schema = _build_schema(mitre_mappings=[mapping])
    rendered = await ReporterAgent().format_html(schema)
    _assert_payload_escaped(rendered, XSS_PAYLOAD)
    _assert_payload_escaped(rendered, '"><svg onload=alert(1)>')
    _assert_payload_escaped(rendered, "<b>Initial Access</b>")
    _assert_payload_escaped(rendered, "<i>finding-1</i>")


@pytest.mark.asyncio
async def test_ioc_value_and_context_are_escaped():
    ioc = IOCTableEntry(
        value=XSS_IMG,
        ioc_type="ip",
        occurrences=1,
        context="<iframe src=javascript:alert(1)>",
    )
    schema = _build_schema(ioc_tables={"ip": [ioc]})
    rendered = await ReporterAgent().format_html(schema)
    _assert_payload_escaped(rendered, XSS_IMG)
    _assert_payload_escaped(rendered, "<iframe src=javascript:alert(1)>")


@pytest.mark.asyncio
async def test_finding_fields_and_evidence_are_escaped():
    finding = Finding(
        title=XSS_PAYLOAD,
        description="<svg/onload=alert(2)>" + ("z" * 50),
        severity=FindingSeverity.CRITICAL,
        confidence=0.9,
        evidence=["<script>steal()</script>", "ok-evidence"],
    )
    schema = _build_schema(findings=[finding])
    rendered = await ReporterAgent().format_html(schema)
    _assert_payload_escaped(rendered, XSS_PAYLOAD)
    _assert_payload_escaped(rendered, "<svg/onload=alert(2)>")
    _assert_payload_escaped(rendered, "<script>steal()</script>")


@pytest.mark.asyncio
async def test_recommendation_fields_are_escaped():
    rec = Recommendation(
        priority=1,
        title=XSS_PAYLOAD,
        description="<img src=x onerror=alert(3)>" + ("z" * 50),
        urgency="<b>immediate</b>",
    )
    schema = _build_schema(recommendations=[rec])
    rendered = await ReporterAgent().format_html(schema)
    _assert_payload_escaped(rendered, XSS_PAYLOAD)
    _assert_payload_escaped(rendered, "<img src=x onerror=alert(3)>")
    _assert_payload_escaped(rendered, "<b>immediate</b>")


@pytest.mark.asyncio
async def test_legitimate_html_chrome_still_present():
    """Escaping must not corrupt structural HTML (style, doctype, sections)."""
    schema = _build_schema(incident_description=XSS_PAYLOAD)
    rendered = await ReporterAgent().format_html(schema)
    assert "<!DOCTYPE html>" in rendered
    assert '<html lang="en">' in rendered
    assert "<style>" in rendered
    assert 'class="section"' in rendered
    assert 'class="header"' in rendered


@pytest.mark.asyncio
async def test_key_findings_bullet_replacement_still_works_after_escape():
    """The reporter intentionally converts '- ' → '<br>• ' for key_findings.
    That conversion must run AFTER escaping so the literal <br> still renders
    while user-supplied HTML stays escaped.
    """
    summary = _baseline_summary()
    summary.key_findings = (
        "- " + XSS_PAYLOAD + " followed by harmless text " + ("k" * 100)
    )
    schema = _build_schema(executive_summary=summary)
    rendered = await ReporterAgent().format_html(schema)
    assert XSS_PAYLOAD not in rendered, "raw payload leaked through bullet path"
    assert html_lib.escape(XSS_PAYLOAD) in rendered
    assert "<br>•" in rendered, "intentional <br>• marker was over-escaped"
