"""Live SIFT VM integration smoke (P0.2 — regression locks).

Exercises the full SSH chain end-to-end against the real SIFT VM and
proves that Milestone A's protections hold against a live target:

- A1 — MCP path validation rejects bad paths *before* SSH is dialed
- A2 — host-key verification is enabled and accepts the seeded VM
- A3 — allowlist accepts a registered tool (`file`) and rejects bare
       commands (`hostname`)
- A5 — agent-forwarded auth still works (no client_keys override)

These tests only run when:
- The `requires_sift_vm` marker is selected, AND
- `FEA_SIFT_VM_AVAILABLE=1` is set in the environment

Operator workflow:
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/sift_vm_key
    ssh-keyscan -p $SIFT_VM_PORT $SIFT_VM_HOST >> ~/.ssh/known_hosts  # one-time
    FEA_SIFT_VM_AVAILABLE=1 uv run pytest -m requires_sift_vm

Roadmap: P0.2 in regression-tests.md.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest


# Run-time gate: skip the entire module unless explicitly opted in.
pytestmark = [
    pytest.mark.requires_sift_vm,
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("FEA_SIFT_VM_AVAILABLE"),
        reason="Set FEA_SIFT_VM_AVAILABLE=1 to enable live SIFT VM tests",
    ),
]


@pytest.fixture
def reset_settings(monkeypatch):
    """Each test gets a fresh Settings load so per-test env vars apply."""
    from find_evil_agent.config import settings as settings_module
    settings_module._settings = None
    yield monkeypatch
    settings_module._settings = None


# ---------------------------------------------------------------------------
# A2 — host-key verification
# ---------------------------------------------------------------------------

class TestSSHHostKeyVerification:
    """A2: connection succeeds when the VM's public key is in known_hosts,
    fails with HostKeyNotVerifiable when it isn't."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(20)
    async def test_strict_checking_succeeds_with_seeded_known_hosts(self, reset_settings):
        """Default strict-checking mode connects when ~/.ssh/known_hosts
        already trusts the VM. Operator seeded via `ssh-keyscan`."""
        from find_evil_agent.agents.tool_executor import ToolExecutorAgent

        agent = ToolExecutorAgent()
        # `file` is in the registry (A3 allowlist). Sanity: a successful
        # connect + run + clean exit code is the green signal.
        result = await agent.process({
            "tool_name": "file",
            "command": "file /tmp/sift-workspace/regression_smoke.txt",
            "timeout": 10,
        })
        assert result.success, f"connect failed: {result.error!r}"
        exec_result = result.data["execution_result"]
        assert exec_result.return_code == 0
        assert "/tmp/sift-workspace/regression_smoke.txt" in (exec_result.stdout or "")

    @pytest.mark.asyncio
    @pytest.mark.timeout(20)
    async def test_strict_checking_rejects_unknown_host(
        self, reset_settings, tmp_path
    ):
        """Point known_hosts at an empty file → asyncssh must refuse the
        unverified host (proves we are not silently trusting any key)."""
        empty_kh = tmp_path / "known_hosts"
        empty_kh.write_text("")
        reset_settings.setenv("SSH_KNOWN_HOSTS_PATH", str(empty_kh))

        from find_evil_agent.agents.tool_executor import ToolExecutorAgent

        agent = ToolExecutorAgent()
        result = await agent.process({
            "tool_name": "file",
            "command": "file /tmp/sift-workspace/regression_smoke.txt",
            "timeout": 10,
        })
        assert not result.success, (
            "connection should have been refused — empty known_hosts means "
            "the VM's key cannot be verified"
        )
        # The failure should reference host-key verification, not a network
        # or auth error. Accept either asyncssh's message or our own wrap.
        err_lower = (result.error or "").lower()
        exec_stderr = (result.data or {}).get("execution_result", None)
        stderr_text = (exec_stderr.stderr.lower() if exec_stderr and exec_stderr.stderr else "")
        combined = err_lower + " " + stderr_text
        assert any(token in combined for token in (
            "host key", "hostkey", "not verifiable", "unknown server",
        )), f"expected host-key error, got: {result.error!r}"


# ---------------------------------------------------------------------------
# A3 — allowlist enforced even on the real executor
# ---------------------------------------------------------------------------

class TestAllowlistOnLiveExecutor:
    """A3: the live executor must still enforce allowlist & blocklist
    before SSH dial."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_unregistered_binary_rejected_before_ssh(self, reset_settings):
        """`hostname` is not in `tools/metadata.yaml`. Even on a real VM
        where it would otherwise succeed, our gate must reject it with
        a security failure that never opens a socket."""
        from find_evil_agent.agents.tool_executor import ToolExecutorAgent

        agent = ToolExecutorAgent()
        t0 = time.monotonic()
        result = await agent.process({
            "tool_name": "hostname",
            "command": "hostname",
            "timeout": 10,
        })
        elapsed = time.monotonic() - t0

        assert not result.success
        assert "security" in (result.error or "").lower()
        # If we'd dialed SSH, this would take >100ms even on LAN. The gate
        # should fire instantly.
        assert elapsed < 1.0, f"validation should be near-instant, took {elapsed:.2f}s"

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_chained_command_rejected_before_ssh(self, reset_settings):
        """Defense-in-depth: a command that opens with an allowlisted
        binary but chains into `; rm` is blocked."""
        from find_evil_agent.agents.tool_executor import ToolExecutorAgent

        agent = ToolExecutorAgent()
        result = await agent.process({
            "tool_name": "file",
            "command": "file /etc/issue; rm /tmp/x",
            "timeout": 10,
        })
        assert not result.success
        assert "security" in (result.error or "").lower()


# ---------------------------------------------------------------------------
# A1 — MCP path validation gates the full chain
# ---------------------------------------------------------------------------

class TestMCPPathValidationOnLiveStack:
    """A1: bad paths submitted to the MCP entrypoint never reach SSH."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_traversal_rejected_at_mcp_boundary(self, reset_settings):
        from find_evil_agent.mcp.server import execute_tool

        t0 = time.monotonic()
        result = await execute_tool(
            tool_name="file",
            evidence_path="../../etc/passwd",
        )
        elapsed = time.monotonic() - t0

        assert result.startswith("❌ Evidence path rejected")
        assert "../../etc/passwd" in result
        assert elapsed < 1.0, f"gate should fire instantly, took {elapsed:.2f}s"

    @pytest.mark.asyncio
    @pytest.mark.timeout(20)
    async def test_allowed_path_reaches_executor(self, reset_settings):
        """A whitelisted path makes it through the MCP gate AND past the
        allowlist AND past host-key verification AND runs on the VM.
        This is the green-path proof for the entire Milestone A chain."""
        from find_evil_agent.mcp.server import execute_tool

        result = await execute_tool(
            tool_name="file",
            evidence_path="/tmp/sift-workspace/regression_smoke.txt",
        )
        # Either tool ran (status SUCCESS) or it ran with non-zero exit
        # but we still got past every gate. We allow either.
        assert "Evidence path rejected" not in result
        assert (
            "Tool Executed Successfully" in result
            or "exit_code" in result.lower()
            or "/tmp/sift-workspace/regression_smoke.txt" in result
        ), f"unexpected response: {result[:200]}"
