"""Run Find Evil Agent MCP Server.

Usage:
    # Run as stdio server (for Claude Code, Claude Desktop)
    python -m find_evil_agent.mcp.server

    # Run as HTTP server (for remote clients)
    python -m find_evil_agent.mcp.server --http --port 16790
"""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())
