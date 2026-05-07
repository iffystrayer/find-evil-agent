"""MCP resources — `@mcp.resource()` registrations.

Split out of `mcp/server.py` in C3a. Importing this module registers
every resource against the shared `mcp` instance.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from find_evil_agent.config.settings import get_settings
from find_evil_agent.tools.registry import ToolRegistry

from .server import mcp


@mcp.resource("tools://registry")
async def get_tool_registry() -> str:
    """Get complete tool registry with metadata.

    Returns JSON representation of all 18+ SIFT tools with descriptions,
    categories, inputs, examples, and output formats.
    """
    registry = ToolRegistry()
    return json.dumps(registry.tools, indent=2)


@mcp.resource("config://settings")
async def get_settings_resource() -> str:
    """Get configuration settings as JSON."""
    settings = get_settings()
    return json.dumps({
        "llm_provider": settings.llm_provider,
        "llm_model_name": settings.llm_model_name,
        "sift_vm_host": settings.sift_vm_host,
        "sift_vm_port": settings.sift_vm_port,
        "tool_confidence_threshold": settings.tool_confidence_threshold,
        "semantic_search_top_k": settings.semantic_search_top_k
    }, indent=2)


@mcp.resource("cases://list")
async def get_cases_list() -> str:
    """Get complete list of investigation cases as JSON.

    Returns JSON array of all cases with metadata.
    """
    cases = [
        {
            "case_id": "case-20240422-abc123",
            "name": "Ransomware Investigation",
            "status": "active",
            "analyst": "analyst1@company.com",
            "created": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "evidence_count": 3,
            "findings_count": 12
        },
        {
            "case_id": "case-20240420-def456",
            "name": "Data Exfiltration",
            "status": "active",
            "analyst": "analyst2@company.com",
            "created": (datetime.utcnow() - timedelta(days=3)).isoformat(),
            "evidence_count": 1,
            "findings_count": 5
        }
    ]

    return json.dumps(cases, indent=2)


@mcp.resource("evidence://catalog")
async def get_evidence_catalog() -> str:
    """Get evidence catalog as JSON.

    Returns JSON array of all registered evidence files with metadata.
    """
    evidence = [
        {
            "evidence_id": "ev-001",
            "file_path": "/mnt/evidence/server01.dd",
            "evidence_type": "disk_image",
            "case_id": "case-20240422-abc123",
            "sha256": "a1b2c3d4e5f6...",
            "size_bytes": 10737418240,
            "registered": (datetime.utcnow() - timedelta(days=2)).isoformat()
        },
        {
            "evidence_id": "ev-002",
            "file_path": "/mnt/evidence/memory.dmp",
            "evidence_type": "memory_dump",
            "case_id": "case-20240422-abc123",
            "sha256": "f6e5d4c3b2a1...",
            "size_bytes": 8589934592,
            "registered": (datetime.utcnow() - timedelta(days=1)).isoformat()
        }
    ]

    return json.dumps(evidence, indent=2)
