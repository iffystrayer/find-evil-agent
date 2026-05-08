"""HTML report formatting using Jinja2 templates.

Extracted from agents/reporter.py (C3b split).
Migrated from inline html.escape calls to Jinja2 with autoescape=True (B2 → C3b).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import aiofiles
import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

if TYPE_CHECKING:
    from ..report_schemas import AttackGraph, ReportSchema
    from ..schemas import FindingSeverity

logger = structlog.get_logger(__name__)

# Initialize Jinja2 environment with autoescape enabled
_template_dir = Path(__file__).parent.parent.parent.parent.parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_template_dir)),
    autoescape=select_autoescape(['html', 'xml', 'j2']),
    trim_blocks=True,
    lstrip_blocks=True,
)


async def format_html(report: ReportSchema) -> str:
    """Format report as HTML with professional styling using Jinja2.

    Args:
        report: Report schema

    Returns:
        HTML-formatted report
    """
    from html import escape as html_escape
    from markupsafe import Markup
    from ..schemas import FindingSeverity

    # Generate attack graph HTML if present
    attack_graph_html = None
    if report.attack_graph and report.attack_graph.nodes:
        attack_graph_html = await _generate_graph_html(report.attack_graph)

    # Pre-process key_findings: escape first, THEN apply bullet replacement
    # This ensures user input is escaped but our intentional <br>• markup works
    key_findings_escaped = html_escape(report.executive_summary.key_findings)
    key_findings_with_bullets = Markup(key_findings_escaped.replace('- ', '<br>• '))

    # Prepare template context
    context = {
        "report": report,
        "key_findings_processed": key_findings_with_bullets,
        "severity_order": [
            FindingSeverity.CRITICAL,
            FindingSeverity.HIGH,
            FindingSeverity.MEDIUM,
            FindingSeverity.LOW,
            FindingSeverity.INFO,
        ],
        "attack_graph_html": attack_graph_html,
    }

    # Render template
    template = _jinja_env.get_template("report.html.j2")
    return template.render(**context)


async def _generate_graph_html(attack_graph: AttackGraph) -> str:
    """Generate inline HTML for attack chain graph visualization.

    Args:
        attack_graph: AttackGraph object with nodes and edges

    Returns:
        HTML string with embedded D3.js graph
    """
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
    template_path = Path(__file__).parent.parent.parent.parent.parent / "templates" / "report_graph_template.html"

    try:
        async with aiofiles.open(template_path, "r") as f:
            template_html = await f.read()

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
        # Return error message (will be auto-escaped by Jinja2 when included in template)
        return f"""
    <div class="section">
        <h2>🕸️ Attack Chain Graph</h2>
        <p style="color: #dc3545;">Graph visualization unavailable: {str(e)}</p>
        <p>Nodes: {len(attack_graph.nodes)}, Edges: {len(attack_graph.edges)}</p>
    </div>
"""
