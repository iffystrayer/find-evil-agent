"""C4: magic numbers → settings.

Verifies that previously-hardcoded numeric defaults now flow through
``config.settings.Settings`` so operators can tune them without editing
source code.
"""

from __future__ import annotations

import pytest

from find_evil_agent.agents.analyzer import AnalyzerAgent
from find_evil_agent.agents.tool_executor import ToolExecutorAgent
from find_evil_agent.agents.tool_selector import ToolSelectorAgent
from find_evil_agent.config import settings as settings_module


@pytest.fixture(autouse=True)
def _reset_settings_singleton():
    settings_module._settings = None
    yield
    settings_module._settings = None


# ---------------------------------------------------------------------------
# New settings exist with the documented defaults
# ---------------------------------------------------------------------------


class TestSettingsFieldsExist:
    def test_analyzer_min_confidence_default(self):
        assert settings_module.get_settings().analyzer_min_confidence == pytest.approx(0.5)

    def test_orchestrator_max_iterations_default(self):
        assert settings_module.get_settings().orchestrator_max_iterations == 5

    def test_orchestrator_min_lead_confidence_default(self):
        assert settings_module.get_settings().orchestrator_min_lead_confidence == pytest.approx(0.6)

    def test_llm_max_retries_default(self):
        assert settings_module.get_settings().llm_max_retries == 2


# ---------------------------------------------------------------------------
# Agents pick up settings values when constructed without explicit overrides
# ---------------------------------------------------------------------------


class TestSettingsFlowThroughToAgents:
    def test_analyzer_reads_min_confidence_from_settings(self, monkeypatch):
        monkeypatch.setenv("ANALYZER_MIN_CONFIDENCE", "0.42")
        settings_module._settings = None
        agent = AnalyzerAgent()
        assert agent.min_confidence == pytest.approx(0.42)

    def test_analyzer_explicit_arg_still_wins(self, monkeypatch):
        monkeypatch.setenv("ANALYZER_MIN_CONFIDENCE", "0.42")
        settings_module._settings = None
        agent = AnalyzerAgent(min_confidence=0.99)
        assert agent.min_confidence == pytest.approx(0.99)

    def test_tool_selector_reads_threshold_and_top_k_from_settings(self, monkeypatch):
        monkeypatch.setenv("TOOL_CONFIDENCE_THRESHOLD", "0.85")
        monkeypatch.setenv("SEMANTIC_SEARCH_TOP_K", "25")
        settings_module._settings = None
        agent = ToolSelectorAgent()
        assert agent.confidence_threshold == pytest.approx(0.85)
        assert agent.semantic_top_k == 25

    def test_tool_selector_explicit_args_still_win(self, monkeypatch):
        monkeypatch.setenv("TOOL_CONFIDENCE_THRESHOLD", "0.85")
        settings_module._settings = None
        agent = ToolSelectorAgent(confidence_threshold=0.50)
        assert agent.confidence_threshold == pytest.approx(0.50)

    def test_tool_executor_reads_timeouts_from_settings(self, monkeypatch):
        monkeypatch.setenv("DEFAULT_TOOL_TIMEOUT", "120")
        monkeypatch.setenv("MAX_TOOL_TIMEOUT", "1800")
        settings_module._settings = None
        agent = ToolExecutorAgent()
        assert agent.default_timeout == 120
        assert agent.max_timeout == 1800

    def test_tool_executor_explicit_args_still_win(self, monkeypatch):
        monkeypatch.setenv("DEFAULT_TOOL_TIMEOUT", "120")
        settings_module._settings = None
        agent = ToolExecutorAgent(default_timeout=30)
        assert agent.default_timeout == 30


# ---------------------------------------------------------------------------
# Static guard: literal "max_retries = 2" no longer in LLM provider sources
# ---------------------------------------------------------------------------


class TestNoHardcodedMaxRetries:
    @pytest.mark.parametrize(
        "module_name",
        [
            "find_evil_agent.llm.providers.openai",
            "find_evil_agent.llm.providers.ollama",
            "find_evil_agent.llm.providers.anthropic",
        ],
    )
    def test_provider_does_not_hardcode_max_retries(self, module_name):
        import importlib
        from pathlib import Path

        mod = importlib.import_module(module_name)
        src_path = Path(mod.__file__)  # type: ignore[arg-type]
        text = src_path.read_text()
        assert "max_retries = 2" not in text, (
            f"{module_name} still has the literal `max_retries = 2`. "
            "Source it from settings.llm_max_retries instead."
        )
        assert "settings.llm_max_retries" in text or "settings().llm_max_retries" in text
