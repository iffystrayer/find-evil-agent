"""SSH host-key verification tests (A2 — TDD).

Verifies that ToolExecutorAgent does NOT silently disable SSH host-key
verification (the prior `known_hosts=None` setting enabled MITM attacks).

Behavior contract:
- Default: strict host-key checking enabled — asyncssh uses `~/.ssh/known_hosts`.
- `settings.ssh_known_hosts_path` set: that file is used as the trust store.
- `settings.ssh_strict_host_key_checking=False`: opt-in insecure mode
  (explicitly passes known_hosts=None). Required for transitional dev
  environments only.

Roadmap reference: Milestone A2 in CODE_REVIEW.md.
"""

from __future__ import annotations

import pytest

from find_evil_agent.agents.tool_executor import ToolExecutorAgent


# ---------------------------------------------------------------------------
# Specification — always pass, document the contract
# ---------------------------------------------------------------------------

class TestSSHHostKeyVerificationSpecification:
    """Document the SSH host-key verification contract."""

    def test_host_key_verification_contract(self):
        """ToolExecutorAgent SSH connection rules:

        1. By default, host-key verification MUST be enabled.
        2. When `settings.ssh_known_hosts_path` is set, that path is used.
        3. When NOT set, asyncssh's default behavior applies (~/.ssh/known_hosts).
        4. Disabling verification requires explicit opt-in via
           `settings.ssh_strict_host_key_checking=False`.
        5. The connect kwargs MUST be inspectable for testing —
           ToolExecutorAgent exposes `_build_ssh_connect_kwargs()`.
        """
        # Method must exist on the class for testability
        assert hasattr(ToolExecutorAgent, "_build_ssh_connect_kwargs")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _agent_with_settings(monkeypatch, **overrides) -> ToolExecutorAgent:
    """Construct a ToolExecutorAgent with overridden settings fields.

    Resets the Settings singleton so per-test env vars are honored.
    """
    from find_evil_agent.config import settings as settings_module

    # Reset cached singleton so a fresh Settings() is built.
    settings_module._settings = None

    # Each override becomes an env var so pydantic-settings picks it up.
    for key, value in overrides.items():
        env_name = key.upper()
        monkeypatch.setenv(env_name, str(value))

    agent = ToolExecutorAgent()
    return agent


# ---------------------------------------------------------------------------
# Execution tests
# ---------------------------------------------------------------------------

class TestSSHConnectKwargs:
    """Verify connect-kwargs construction reflects host-key settings."""

    def test_default_is_strict_host_key_checking(self, monkeypatch):
        """Default Settings → host-key verification is enabled.

        Either `known_hosts` is omitted (asyncssh uses ~/.ssh/known_hosts),
        or it's an explicit path — but it must NOT be None.
        """
        agent = _agent_with_settings(monkeypatch)
        kwargs = agent._build_ssh_connect_kwargs()

        assert kwargs.get("host") == agent.ssh_host
        assert kwargs.get("port") == agent.ssh_port
        assert kwargs.get("username") == agent.ssh_user
        # The cardinal rule:
        if "known_hosts" in kwargs:
            assert kwargs["known_hosts"] is not None, (
                "known_hosts=None disables host-key verification — must require "
                "explicit opt-in via FEA_SSH_STRICT_HOST_KEY_CHECKING=false"
            )

    def test_explicit_known_hosts_path_is_used(self, monkeypatch, tmp_path):
        """When settings.ssh_known_hosts_path points at a file, that file
        is passed to asyncssh."""
        khost_file = tmp_path / "known_hosts"
        khost_file.write_text("# placeholder\n")
        agent = _agent_with_settings(
            monkeypatch,
            ssh_known_hosts_path=str(khost_file),
        )
        kwargs = agent._build_ssh_connect_kwargs()
        assert kwargs.get("known_hosts") == str(khost_file)

    def test_strict_checking_off_opts_into_disabled_verification(self, monkeypatch):
        """Explicit opt-out (FEA_SSH_STRICT_HOST_KEY_CHECKING=false)
        passes known_hosts=None — required for transitional dev only."""
        agent = _agent_with_settings(
            monkeypatch,
            ssh_strict_host_key_checking="false",
        )
        kwargs = agent._build_ssh_connect_kwargs()
        assert kwargs.get("known_hosts") is None

    def test_strict_checking_true_with_no_path_uses_asyncssh_default(self, monkeypatch):
        """Default secure behavior: do NOT pass known_hosts at all so
        asyncssh falls back to ~/.ssh/known_hosts."""
        agent = _agent_with_settings(
            monkeypatch,
            ssh_strict_host_key_checking="true",
        )
        kwargs = agent._build_ssh_connect_kwargs()
        # Either omitted entirely, or set to a non-None value
        assert kwargs.get("known_hosts", "OMITTED") != None  # noqa: E711

    def test_client_keys_passed_when_ssh_key_path_set(self, monkeypatch, tmp_path):
        """The existing `ssh_key_path` flow keeps working — client_keys
        is populated when a key path is configured."""
        key_file = tmp_path / "id_rsa"
        key_file.write_text("# placeholder\n")
        agent = _agent_with_settings(
            monkeypatch,
            sift_ssh_key_path=str(key_file),
        )
        kwargs = agent._build_ssh_connect_kwargs()
        assert kwargs.get("client_keys") == [str(key_file)]
