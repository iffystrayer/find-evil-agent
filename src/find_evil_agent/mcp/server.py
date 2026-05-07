"""MCP Server — FastMCP wiring for Find Evil Agent.

Holds only the FastMCP instance, the path-validation helper, the
process entrypoint, and the back-compat re-exports. The actual tool /
resource / prompt definitions live in:

- `find_evil_agent.mcp.tools`     — `@mcp.tool()` registrations
- `find_evil_agent.mcp.resources` — `@mcp.resource()` registrations
- `find_evil_agent.mcp.prompts`   — `@mcp.prompt()` registrations

The C3a refactor split these out so each concern is its own file. The
re-exports at the bottom of this module preserve every existing
`from find_evil_agent.mcp.server import <name>` import path used by
tests and downstream callers.

Example:
    # Run as stdio server
    python -m find_evil_agent.mcp.server

    # Run as HTTP server
    python -m find_evil_agent.mcp.server --http --port 16790
"""

from __future__ import annotations

import asyncio

import structlog
from mcp.server.fastmcp import FastMCP

from find_evil_agent.config.settings import get_settings
from find_evil_agent.security import PathValidator, SecurityValidationError

logger = structlog.get_logger(__name__)


def _validate_evidence_path(evidence_path: str | None) -> str | None:
    """Validate a user-supplied evidence path against the allowlist.

    Returns a formatted MCP error string if validation fails, or None if the
    path is safe (or absent). Callers MUST short-circuit on a non-None return.

    The error is prefixed with "❌ Evidence path rejected" so callers and
    operators can distinguish a validation failure from a downstream error.
    """
    if not evidence_path:
        return None

    settings = get_settings()
    validator = PathValidator(whitelist=settings.allowed_evidence_paths)
    try:
        validator.validate_path(evidence_path)
    except SecurityValidationError as exc:
        logger.warning(
            "evidence_path_rejected",
            path=evidence_path,
            reason=str(exc),
        )
        return (
            f"❌ Evidence path rejected: {evidence_path}\n"
            f"\n**Reason:** {exc}\n"
            f"**Allowed prefixes:** {', '.join(settings.allowed_evidence_paths)}\n"
        )
    return None


# Initialize FastMCP server. The split modules (tools/resources/prompts)
# import this `mcp` instance and register their decorators against it.
mcp = FastMCP(
    name="find-evil-agent",
    instructions="""Find Evil Agent - Autonomous AI Incident Response

This MCP server provides forensic analysis capabilities for SANS SIFT Workstation.

Key Capabilities:
1. Hallucination-Resistant Tool Selection - Two-stage validation prevents LLM from
   inventing non-existent forensic tools
2. Autonomous Iterative Investigation - Automatically follows investigative leads
   across multiple iterations
3. IOC Extraction - Extracts IPs, domains, hashes, file paths from tool output
4. Finding Generation - Structures forensic findings with severity and confidence

Always:
- Provide clear incident descriptions and analysis goals
- Review tool selection confidence scores (≥0.7 required)
- Verify autonomous investigation results
- Approve/reject findings before final reporting

Human-in-the-loop review is critical for forensic integrity.""",
    debug=False,
    log_level="INFO"
)


# Importing the split modules registers their decorators against `mcp`.
# Order: tools → resources → prompts. Each module does
# `from .server import mcp` so the FastMCP instance must already exist
# above this point.
from find_evil_agent.mcp.tools import (  # noqa: E402,F401  (registration side-effect; re-export)
    analyze_evidence,
    create_case,
    execute_tool,
    extract_iocs,
    generate_report,
    get_case,
    get_config,
    investigate,
    list_cases,
    list_tools,
    register_evidence,
    select_tool,
)
from find_evil_agent.mcp.resources import (  # noqa: E402,F401
    get_cases_list,
    get_evidence_catalog,
    get_settings_resource,
    get_tool_registry,
)
from find_evil_agent.mcp.prompts import (  # noqa: E402,F401
    disk_triage,
    memory_analysis,
    network_analysis,
    timeline_analysis,
)


async def main():
    """Main entry point for MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Find Evil Agent MCP Server")
    parser.add_argument("--http", action="store_true", help="Run as HTTP server")
    parser.add_argument("--port", type=int, default=16790, help="HTTP port (default: 16790)")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host (default: 127.0.0.1)")
    args = parser.parse_args()

    if args.http:
        # Run as HTTP server (streamable-http transport)
        logger.info(
            "mcp_server_starting",
            transport="http",
            host=args.host,
            port=args.port
        )

        # Update FastMCP settings
        mcp.settings.host = args.host
        mcp.settings.port = args.port

        # Run server
        await mcp.run_async()
    else:
        # Run as stdio server (default)
        logger.info("mcp_server_starting", transport="stdio")

        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await mcp.server.run(
                read_stream,
                write_stream,
                mcp.server.create_initialization_options()
            )


if __name__ == "__main__":
    asyncio.run(main())
