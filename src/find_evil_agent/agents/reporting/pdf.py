"""PDF report generation.

Extracted from agents/reporter.py (C3b split).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import aiofiles
import structlog

if TYPE_CHECKING:
    from ..report_schemas import ReportSchema

logger = structlog.get_logger(__name__)


async def format_pdf(
    report: ReportSchema,
    output_path: Optional[Path],
    format_html_func,
) -> str:
    """Format report as PDF.

    Args:
        report: Report schema
        output_path: Output file path
        format_html_func: HTML formatter function (injected to avoid circular import)

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
    html_content = await format_html_func(report)

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
        async with aiofiles.open(html_path, "w") as f:
            await f.write(html_content)
        raise ImportError(
            "weasyprint not installed. Install with: pip install weasyprint\n"
            f"HTML report saved to: {html_path}"
        )
