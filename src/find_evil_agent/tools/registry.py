"""Tool Registry - Central catalog of SIFT tools.

STUB: Implementation pending April 15 starter code.

The registry maintains:
1. Tool metadata (name, description, args)
2. Tool schemas for MCP
3. Tool availability status
4. Embeddings for semantic search
"""

from typing import Any
from pathlib import Path


class ToolRegistry:
    """Registry of available SIFT tools.
    
    Provides:
    - Tool discovery and registration
    - Semantic search for tool selection
    - Schema management for MCP
    - Tool metadata access
    """
    
    def __init__(self, sift_path: Path | None = None):
        """Initialize registry."""
        self.tools: dict[str, Any] = {}
        self.sift_path = sift_path or Path("/usr/bin")
    
    def discover(self) -> list[str]:
        """Stub: Discover available SIFT tools."""
        raise NotImplementedError(
            "Tool discovery pending starter code integration"
        )
    
    def get_tool(self, name: str) -> dict[str, Any] | None:
        """Get tool metadata by name."""
        return self.tools.get(name)
    
    def search(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Semantic search for tools matching query."""
        raise NotImplementedError(
            "Semantic search pending embedding implementation"
        )
