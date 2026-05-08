"""Report formatting modules for Find Evil Agent.

Split from agents/reporter.py (C3b) to improve maintainability:
- mitre.py: MITRE ATT&CK mapping logic
- markdown.py: Markdown report formatting
- html.py: HTML report formatting (Jinja2-based)
- pdf.py: PDF report generation
"""

from .html import format_html
from .markdown import format_markdown
from .mitre import MITRE_PATTERNS, map_mitre_attacks
from .pdf import format_pdf

__all__ = [
    "format_html",
    "format_markdown",
    "format_pdf",
    "map_mitre_attacks",
    "MITRE_PATTERNS",
]
