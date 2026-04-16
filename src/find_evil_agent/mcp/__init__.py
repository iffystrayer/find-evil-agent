"""Model Context Protocol integration.

Provides MCP server for exposing Find Evil Agent tools to AI clients.

Usage:
    # Run as stdio server
    python -m find_evil_agent.mcp.server

    # Run as HTTP server
    python -m find_evil_agent.mcp.server --http --port 16790
"""

from .server import mcp

__all__ = ["mcp"]
