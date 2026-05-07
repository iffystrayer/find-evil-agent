"""C3a — MCP server split structure tests.

Verifies the post-split layout of `find_evil_agent.mcp`:

- `mcp/server.py` now holds only the FastMCP instance + validation helper +
  `main()` entrypoint (under a tight LOC ceiling).
- `mcp/tools.py` holds the 12 `@mcp.tool()` functions.
- `mcp/resources.py` holds the 4 `@mcp.resource()` functions.
- `mcp/prompts.py` holds the 4 `@mcp.prompt()` functions.

Hackathon-compliance counts (12 tools / 4 resources / 4 prompts) are
re-asserted at the FastMCP-server level so we can't accidentally drop a
registration during the split.

These tests are *static guards* per project convention: if a future
change re-fattens `server.py` or moves a tool back into it, the LOC
ceiling fails fast.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import find_evil_agent.mcp as mcp_pkg
from find_evil_agent.mcp.server import mcp as mcp_app


SERVER_LOC_CEILING = 250  # server.py must stay slim post-split

REQUIRED_TOOL_NAMES = {
    "analyze_evidence",
    "investigate",
    "list_tools",
    "select_tool",
    "get_config",
    "execute_tool",
    "register_evidence",
    "generate_report",
    "extract_iocs",
    "create_case",
    "list_cases",
    "get_case",
}

REQUIRED_RESOURCE_URIS = {
    "tools://registry",
    "config://settings",
    "cases://list",
    "evidence://catalog",
}

REQUIRED_PROMPT_NAMES = {
    "memory_analysis",
    "disk_triage",
    "network_analysis",
    "timeline_analysis",
}


def _pkg_path(modname: str) -> Path:
    """Resolve a submodule of find_evil_agent.mcp to its source file."""
    pkg_dir = Path(mcp_pkg.__file__).parent
    return pkg_dir / f"{modname}.py"


class TestMCPModuleSplit:
    """Static guards on the post-split file layout."""

    @pytest.mark.parametrize("modname", ["tools", "resources", "prompts"])
    def test_split_module_exists(self, modname):
        """Each split module must exist as its own file."""
        path = _pkg_path(modname)
        assert path.exists(), (
            f"expected mcp/{modname}.py to exist after the C3a split; "
            f"got missing file at {path}"
        )

    @pytest.mark.parametrize("modname", ["tools", "resources", "prompts"])
    def test_split_module_imports_cleanly(self, modname):
        """Each split module must be importable and register against `mcp`."""
        mod = importlib.import_module(f"find_evil_agent.mcp.{modname}")
        assert mod is not None

    def test_server_py_is_slim_after_split(self):
        """`server.py` must shrink below the ceiling once tools/resources/prompts
        move out. Catches regressions where someone re-fattens it."""
        server_path = _pkg_path("server")
        loc = sum(1 for _ in server_path.read_text().splitlines())
        assert loc <= SERVER_LOC_CEILING, (
            f"mcp/server.py grew to {loc} LOC (ceiling {SERVER_LOC_CEILING}). "
            "If you intentionally added code, move tool/resource/prompt definitions "
            "into the split modules; the ceiling exists to prevent re-fattening."
        )

    @pytest.mark.parametrize(
        "decorator,target",
        [
            ("@mcp.tool", "mcp/tools.py"),
            ("@mcp.resource", "mcp/resources.py"),
            ("@mcp.prompt", "mcp/prompts.py"),
        ],
    )
    def test_no_decorator_registration_in_server_py(self, decorator, target):
        """Decorator registrations must live in their split module, not server.

        Looks for `@mcp.<kind>(` at the start of a line (after optional
        whitespace). Substring mentions inside docstrings or comments are
        ignored — only real decorator usage counts.
        """
        server_src = _pkg_path("server").read_text()
        offending = [
            line for line in server_src.splitlines()
            if line.lstrip().startswith(decorator + "(")
        ]
        assert not offending, (
            f"Found {decorator}() decorator usage in server.py "
            f"(must live in {target}):\n  " + "\n  ".join(offending)
        )


class TestMCPRegistrationCounts:
    """Hackathon-compliance counts must survive the split."""

    @pytest.mark.asyncio
    async def test_all_tools_registered(self):
        tool_names = {t.name for t in await mcp_app.list_tools()}
        missing = REQUIRED_TOOL_NAMES - tool_names
        assert not missing, f"missing MCP tools after split: {missing}"
        assert len(tool_names) >= 12

    @pytest.mark.asyncio
    async def test_all_resources_registered(self):
        resource_uris = {str(r.uri) for r in await mcp_app.list_resources()}
        missing = REQUIRED_RESOURCE_URIS - resource_uris
        assert not missing, f"missing MCP resources after split: {missing}"
        assert len(resource_uris) >= 4

    @pytest.mark.asyncio
    async def test_all_prompts_registered(self):
        prompt_names = {p.name for p in await mcp_app.list_prompts()}
        missing = REQUIRED_PROMPT_NAMES - prompt_names
        assert not missing, f"missing MCP prompts after split: {missing}"
        assert len(prompt_names) >= 4


class TestBackwardCompatReexports:
    """Existing call sites do `from find_evil_agent.mcp.server import <name>`.
    Those imports must still work after the split (functions live in tools.py
    / resources.py / prompts.py but are re-exported from server.py).
    """

    @pytest.mark.parametrize(
        "name",
        sorted(REQUIRED_TOOL_NAMES) + [
            "get_cases_list",
            "get_evidence_catalog",
            "get_tool_registry",
            "get_settings_resource",
        ] + sorted(REQUIRED_PROMPT_NAMES),
    )
    def test_reexport_from_server(self, name):
        from find_evil_agent.mcp import server as server_mod
        assert hasattr(server_mod, name), (
            f"`from find_evil_agent.mcp.server import {name}` must keep working "
            "after the C3a split — re-export it from server.py"
        )
