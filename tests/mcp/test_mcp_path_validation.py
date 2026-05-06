"""MCP Server Path Validation Tests (A1 — TDD).

Verifies that user-supplied evidence paths passed to MCP tools are validated
against `Settings.allowed_evidence_paths` BEFORE any command construction or
SSH execution.

Without this guard, the MCP `execute_tool` endpoint concatenates the path
directly into a shell command string and ships it to the SIFT VM — enabling
path traversal (`../../etc/passwd`) and shell-metacharacter injection.

Roadmap reference: Milestone A1 in CODE_REVIEW.md remediation plan.
"""

from __future__ import annotations

import pytest

from find_evil_agent.mcp.server import execute_tool, analyze_evidence


# Sentinel string the MCP layer emits when path validation rejects an input.
# Tests assert on this exact prefix so we know rejection happened at the
# validation gate (not at SSH, not at the registry, not at the LLM).
REJECTION_PREFIX = "❌ Evidence path rejected"


# ---------------------------------------------------------------------------
# Specification — always pass, document the contract
# ---------------------------------------------------------------------------

class TestMCPPathValidationSpecification:
    """Document the security contract for MCP path-accepting tools."""

    def test_evidence_path_validation_contract(self):
        """MCP tools accepting `evidence_path` MUST:

        1. Reject path traversal sequences (..)
        2. Reject home directory access (~)
        3. Reject system directories (/etc/, /root/, /sys/, /proc/, /dev/, /var/lib/)
        4. Reject paths outside settings.allowed_evidence_paths whitelist
        5. Emit a deterministic rejection prefix (REJECTION_PREFIX) so tests
           and operators can distinguish a validation failure from a
           downstream error (SSH timeout, tool not found, etc.).
        6. Reject BEFORE invoking SSH, the orchestrator, or the LLM.
        """
        assert REJECTION_PREFIX.startswith("❌")
        # Path-accepting MCP tools enumerated in the contract:
        path_accepting_tools = ["execute_tool", "analyze_evidence"]
        assert len(path_accepting_tools) == 2


# ---------------------------------------------------------------------------
# execute_tool — direct, fast tests (no LLM, no SSH)
# ---------------------------------------------------------------------------

# Paths that must be rejected. Each represents a distinct attack class.
MALICIOUS_PATHS = [
    "../../etc/passwd",          # parent-directory traversal
    "/etc/shadow",               # system directory
    "/root/.ssh/id_rsa",         # root home
    "~/.aws/credentials",        # home expansion
    "/proc/self/environ",        # /proc
    "/dev/sda1",                 # /dev
    "/var/lib/postgresql/data",  # /var (non-log)
    "/tmp/../etc/passwd",        # nested traversal
    "/home/user/secret",         # outside whitelist
]


class TestExecuteToolPathValidation:
    """`execute_tool` rejects unsafe paths at the MCP boundary."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad_path", MALICIOUS_PATHS)
    async def test_rejects_unsafe_evidence_path(self, bad_path):
        """Each malicious path produces the validation-rejection sentinel
        without any tool execution attempt."""
        result = await execute_tool(tool_name="strings", evidence_path=bad_path)
        assert isinstance(result, str)
        assert result.startswith(REJECTION_PREFIX), (
            f"expected validation rejection for {bad_path!r}, got: {result!r}"
        )
        # The original malicious path should appear in the rejection so the
        # operator can see what was tried.
        assert bad_path in result

    @pytest.mark.asyncio
    async def test_validation_runs_before_tool_lookup(self):
        """Path validation must run BEFORE the registry lookup so even an
        unknown tool name returns the path-rejection error when both are bad."""
        result = await execute_tool(
            tool_name="not_a_real_tool",
            evidence_path="../../etc/passwd",
        )
        assert result.startswith(REJECTION_PREFIX)

    @pytest.mark.asyncio
    async def test_no_evidence_path_skips_validation(self):
        """`evidence_path=None` must not produce a validation rejection
        (many tools run without an explicit path)."""
        result = await execute_tool(
            tool_name="not_a_real_tool",  # avoids any SSH attempt
            evidence_path=None,
        )
        assert not result.startswith(REJECTION_PREFIX)
        # And we should still get the expected "tool not found" response
        assert "Tool not found" in result

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_registry_error_when_path_is_safe(self):
        """When path is safe but tool is unknown, we get the registry error,
        proving validation didn't false-positive."""
        result = await execute_tool(
            tool_name="not_a_real_tool",
            evidence_path="/mnt/evidence/case01/disk.img",
        )
        assert not result.startswith(REJECTION_PREFIX)
        assert "Tool not found" in result


# ---------------------------------------------------------------------------
# analyze_evidence — same gate, lightweight check (no orchestrator run)
# ---------------------------------------------------------------------------

class TestAnalyzeEvidencePathValidation:
    """`analyze_evidence` rejects unsafe paths at the MCP boundary,
    BEFORE invoking the orchestrator (which spins up an LLM call)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad_path", [
        "../../etc/passwd",
        "/etc/shadow",
        "/root/.ssh/id_rsa",
        "~/.aws/credentials",
        "/proc/self/environ",
    ])
    async def test_rejects_unsafe_evidence_path(self, bad_path):
        """Rejection must be fast (sub-second) — proving the gate fires
        before the orchestrator is constructed."""
        import time
        t0 = time.monotonic()
        result = await analyze_evidence(
            incident_description="test",
            analysis_goal="test",
            evidence_path=bad_path,
        )
        elapsed = time.monotonic() - t0

        assert isinstance(result, str)
        assert result.startswith(REJECTION_PREFIX), (
            f"expected validation rejection for {bad_path!r}, got: {result!r}"
        )
        assert bad_path in result
        # Sanity: rejection should be near-instant (no LLM, no SSH).
        assert elapsed < 2.0, f"rejection took {elapsed:.2f}s — gate not firing early"
