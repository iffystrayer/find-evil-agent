"""MCP (Model Context Protocol) Integration Module.

This module provides MCP server and client implementations
for integration with SANS SIFT Workstation.

Note:
    Implementations are stubs pending April 15 starter code.
    MCP spec: https://spec.modelcontextprotocol.io
"""

from .server import MCPServer
from .client import MCPClient

__all__ = ["MCPServer", "MCPClient"]
