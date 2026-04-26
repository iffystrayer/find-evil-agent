"""MCP Client - Connects to SIFT MCP server.

STUB: Implementation pending April 15 starter code.

The MCP Client:
1. Connects to running MCP server
2. Discovers available tools
3. Invokes tools via MCP protocol
4. Handles responses
"""

from typing import Any


class MCPClient:
    """Client for MCP-enabled SIFT server.

    Connects to the SIFT workstation MCP server
    to execute forensic tools remotely.
    """

    def __init__(self, server_url: str | None = None):
        """Initialize client.

        Args:
            server_url: MCP server endpoint (uses settings if None)
        """
        if server_url is None:
            from find_evil_agent.config.settings import get_settings

            settings = get_settings()
            server_url = f"http://{settings.mcp_server_host}:{settings.mcp_server_port}"
        self.server_url = server_url
        self.connected = False

    async def connect(self) -> bool:
        """Stub: Connect to MCP server."""
        raise NotImplementedError("MCP Client implementation pending starter code")

    async def list_tools(self) -> list[dict[str, Any]]:
        """Stub: List available tools."""
        raise NotImplementedError("Tool listing pending starter code")

    async def call_tool(self, tool_name: str, args: dict) -> dict[str, Any]:
        """Stub: Execute tool via MCP."""
        raise NotImplementedError("Tool execution pending starter code")
