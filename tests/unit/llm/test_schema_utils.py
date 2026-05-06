"""C2: shared LLM schema-prompt utilities.

OpenAI and Ollama providers used to ship duplicate copies of
``_build_schema_prompt`` / ``_inject_schema_prompt``. Both now delegate
to ``find_evil_agent.llm.schema_utils``. These tests pin the contract.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from find_evil_agent.llm.schema_utils import (
    build_schema_prompt,
    inject_schema_prompt,
)


class _SampleSchema(BaseModel):
    tool_name: str = Field(..., description="Tool to invoke")
    confidence: float = Field(..., ge=0, le=1)


# ---------------------------------------------------------------------------
# build_schema_prompt
# ---------------------------------------------------------------------------


class TestBuildSchemaPrompt:
    def test_includes_field_names(self) -> None:
        prompt = build_schema_prompt(_SampleSchema)
        assert "tool_name" in prompt
        assert "confidence" in prompt

    def test_includes_marker_text(self) -> None:
        prompt = build_schema_prompt(_SampleSchema)
        assert "valid JSON" in prompt
        assert "IMPORTANT" in prompt

    def test_forbids_markdown_fences_in_instructions(self) -> None:
        """The schema prompt must instruct the model NOT to wrap output
        in markdown fences — that's what trips up parsing the response."""
        prompt = build_schema_prompt(_SampleSchema)
        assert "Do NOT include markdown code fences" in prompt


# ---------------------------------------------------------------------------
# inject_schema_prompt
# ---------------------------------------------------------------------------


class TestInjectSchemaPrompt:
    def test_prepends_when_no_system_message(self) -> None:
        messages = [{"role": "user", "content": "hi"}]
        result = inject_schema_prompt(messages, "Schema: X")
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "Schema: X"
        assert result[1]["role"] == "user"

    def test_appends_to_existing_system_message(self) -> None:
        messages = [
            {"role": "system", "content": "You are an analyst."},
            {"role": "user", "content": "go"},
        ]
        result = inject_schema_prompt(messages, "Schema: Y")
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert "You are an analyst." in result[0]["content"]
        assert "Schema: Y" in result[0]["content"]

    def test_does_not_mutate_input(self) -> None:
        original = [{"role": "user", "content": "hi"}]
        snapshot = [m.copy() for m in original]
        inject_schema_prompt(original, "Schema: Z")
        assert original == snapshot, "input messages must not be mutated"

    def test_empty_list_input(self) -> None:
        result = inject_schema_prompt([], "Schema: Q")
        assert result == [{"role": "system", "content": "Schema: Q"}]


# ---------------------------------------------------------------------------
# Static guard: provider sources no longer carry the duplicated logic
# ---------------------------------------------------------------------------


class TestProvidersDelegateToSharedModule:
    @pytest.mark.parametrize(
        "module_name",
        [
            "find_evil_agent.llm.providers.openai",
            "find_evil_agent.llm.providers.ollama",
        ],
    )
    def test_no_inline_schema_prompt_body(self, module_name: str) -> None:
        """The marker f-string from the old inline copy must be gone — it
        now lives only in :mod:`find_evil_agent.llm.schema_utils`."""
        import importlib

        mod = importlib.import_module(module_name)
        text = Path(mod.__file__).read_text()  # type: ignore[arg-type]
        # Inline body fragments that should NOT exist in the providers anymore.
        assert "model_json_schema()" not in text, (
            f"{module_name} still inlines schema-prompt construction; should "
            "delegate to llm.schema_utils.build_schema_prompt"
        )
        assert "schema_utils" in text, (
            f"{module_name} should import from llm.schema_utils after C2"
        )
