"""Tests for dynamic command builder.

Following TDD methodology:
1. Specification tests (immediate passing)
2. Structure tests (skipped until implementation)
3. Execution tests (skipped until implementation)
"""

from unittest.mock import AsyncMock, Mock

import pytest

from find_evil_agent.agents.schemas import ToolSelection

# Conditional import for TDD
try:
    from find_evil_agent.agents.command_builder import DynamicCommandBuilder
    from find_evil_agent.security import SecurityValidationError

    BUILDER_AVAILABLE = True
except ImportError:
    BUILDER_AVAILABLE = False

    class DynamicCommandBuilder:
        pass

    class SecurityValidationError(Exception):
        pass


class TestCommandBuilderSpecification:
    """Specification tests - Define requirements and expected behavior."""

    def test_requirements_specification(self):
        """Document command builder requirements."""
        requirements = """
        DynamicCommandBuilder Requirements:

        1. Accept tool selection with rationale
        2. Accept investigation context (incident, goal, evidence paths)
        3. Read tool metadata from YAML
        4. Use LLM to construct proper commands
        5. Validate constructed commands (no injection, valid paths)
        6. Return executable command string

        Key Features:
        - Dynamic parameter filling based on context
        - Evidence path resolution
        - Security validation (whitelist, path normalization)
        - LLM-powered intelligent command construction
        """
        assert requirements is not None

    def test_expected_inputs_specification(self):
        """Document expected input structure."""
        expected_inputs = {
            "tool_selection": "ToolSelection with tool_name, confidence, rationale",
            "context": {
                "incident": "Ransomware detected encrypting files",
                "goal": "Identify malicious processes",
                "evidence_paths": ["/mnt/evidence/disk.dd", "/mnt/evidence/memory.raw"],
            },
            "metadata_path": "Path to tools/metadata.yaml",
        }
        assert expected_inputs["tool_selection"] is not None
        assert "incident" in expected_inputs["context"]

    def test_expected_outputs_specification(self):
        """Document expected output structure."""
        expected_outputs = {
            "success_case": {
                "command": "volatility -f /mnt/evidence/memory.raw --profile=Win10x64 pslist",
                "validated": True,
            },
            "failure_case": {"command": None, "error": "Invalid path or injection detected"},
        }
        assert expected_outputs["success_case"]["validated"] is True


@pytest.fixture
def mock_llm_router():
    """Mock LLM router for testing."""
    router = AsyncMock()
    router.chat.return_value = "volatility -f /mnt/evidence/memory.raw --profile=Win10x64 pslist"
    return router


@pytest.fixture
def tool_selection():
    """Sample tool selection."""
    return ToolSelection(
        tool_name="volatility",
        confidence=0.92,
        reason="Memory dump analysis needed to identify running processes",
    )


@pytest.fixture
def investigation_context():
    """Sample investigation context."""
    return {
        "incident": "Ransomware detected encrypting files on Windows server",
        "goal": "Identify malicious processes and IOCs",
        "evidence_paths": ["/mnt/evidence/memory.raw", "/mnt/evidence/disk.dd"],
    }


class TestCommandBuilderStructure:
    """Structure tests - Interface and method requirements."""

    @pytest.mark.skipif(not BUILDER_AVAILABLE, reason="DynamicCommandBuilder not implemented")
    def test_builder_has_required_methods(self):
        """Verify builder has required interface methods."""
        builder = DynamicCommandBuilder(llm_router=Mock(), metadata_path="tools/metadata.yaml")

        # Required methods
        assert hasattr(builder, "build_command")
        assert callable(builder.build_command)

    @pytest.mark.skipif(not BUILDER_AVAILABLE, reason="DynamicCommandBuilder not implemented")
    def test_builder_accepts_llm_router(self, mock_llm_router):
        """Verify builder accepts LLM router dependency."""
        builder = DynamicCommandBuilder(
            llm_router=mock_llm_router, metadata_path="tools/metadata.yaml"
        )
        assert builder.llm_router is not None

    @pytest.mark.skipif(not BUILDER_AVAILABLE, reason="DynamicCommandBuilder not implemented")
    def test_builder_accepts_metadata_path(self):
        """Verify builder accepts metadata file path."""
        builder = DynamicCommandBuilder(llm_router=Mock(), metadata_path="tools/metadata.yaml")
        assert builder.metadata_path is not None


class TestCommandBuilderExecution:
    """Execution tests - Core functionality with real inputs."""

    @pytest.mark.skipif(not BUILDER_AVAILABLE, reason="DynamicCommandBuilder not implemented")
    async def test_build_simple_command(
        self, mock_llm_router, tool_selection, investigation_context
    ):
        """Test building a simple command."""
        builder = DynamicCommandBuilder(
            llm_router=mock_llm_router, metadata_path="tools/metadata.yaml"
        )

        result = await builder.build_command(
            tool_selection=tool_selection, context=investigation_context
        )

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.skipif(not BUILDER_AVAILABLE, reason="DynamicCommandBuilder not implemented")
    async def test_command_includes_evidence_path(
        self, mock_llm_router, tool_selection, investigation_context
    ):
        """Test that command includes evidence file path."""
        builder = DynamicCommandBuilder(
            llm_router=mock_llm_router, metadata_path="tools/metadata.yaml"
        )

        result = await builder.build_command(
            tool_selection=tool_selection, context=investigation_context
        )

        # Should contain evidence path
        assert "/mnt/evidence/memory.raw" in result or "memory.raw" in result

    @pytest.mark.skipif(not BUILDER_AVAILABLE, reason="DynamicCommandBuilder not implemented")
    async def test_command_respects_tool_metadata(self, mock_llm_router, investigation_context):
        """Test that different tools produce different commands."""
        builder = DynamicCommandBuilder(
            llm_router=mock_llm_router, metadata_path="tools/metadata.yaml"
        )

        # Volatility selection
        vol_selection = ToolSelection(
            tool_name="volatility", confidence=0.9, reason="Memory analysis needed"
        )
        vol_cmd = await builder.build_command(vol_selection, investigation_context)

        # Strings selection (different tool)
        mock_llm_router.chat.return_value = "strings /mnt/evidence/disk.dd"
        strings_selection = ToolSelection(
            tool_name="strings", confidence=0.85, reason="String extraction needed"
        )
        strings_cmd = await builder.build_command(strings_selection, investigation_context)

        # Commands should be different
        assert vol_cmd != strings_cmd


class TestCommandBuilderValidation:
    """Validation tests - Security and safety checks."""

    @pytest.mark.skipif(not BUILDER_AVAILABLE, reason="DynamicCommandBuilder not implemented")
    async def test_rejects_path_traversal(self, mock_llm_router):
        """Test that path traversal attempts are rejected."""
        # Mock LLM returns malicious command
        mock_llm_router.chat.return_value = "strings ../../etc/shadow"

        builder = DynamicCommandBuilder(
            llm_router=mock_llm_router, metadata_path="tools/metadata.yaml"
        )

        tool_selection = ToolSelection(tool_name="strings", confidence=0.9, reason="Test")
        context = {"incident": "Test", "goal": "Test", "evidence_paths": ["/mnt/evidence/file.txt"]}

        with pytest.raises(SecurityValidationError, match="path traversal"):
            await builder.build_command(tool_selection, context)

    @pytest.mark.skipif(not BUILDER_AVAILABLE, reason="DynamicCommandBuilder not implemented")
    async def test_rejects_command_injection(self, mock_llm_router):
        """Test that command injection attempts are rejected."""
        # Mock LLM returns malicious command
        mock_llm_router.chat.return_value = "strings /mnt/evidence/file.txt; rm -rf /"

        builder = DynamicCommandBuilder(
            llm_router=mock_llm_router, metadata_path="tools/metadata.yaml"
        )

        tool_selection = ToolSelection(tool_name="strings", confidence=0.9, reason="Test")
        context = {"incident": "Test", "goal": "Test", "evidence_paths": ["/mnt/evidence/file.txt"]}

        with pytest.raises(SecurityValidationError, match="injection"):
            await builder.build_command(tool_selection, context)

    @pytest.mark.skipif(not BUILDER_AVAILABLE, reason="DynamicCommandBuilder not implemented")
    async def test_validates_evidence_paths_exist(self, mock_llm_router):
        """Test that non-existent evidence paths are flagged."""
        builder = DynamicCommandBuilder(
            llm_router=mock_llm_router, metadata_path="tools/metadata.yaml", validate_paths=True
        )

        tool_selection = ToolSelection(tool_name="strings", confidence=0.9, reason="Test")
        context = {
            "incident": "Test",
            "goal": "Test",
            "evidence_paths": ["/nonexistent/path/file.txt"],
        }

        with pytest.raises(FileNotFoundError):
            await builder.build_command(tool_selection, context)


class TestCommandBuilderIntegration:
    """Integration tests - Real metadata and LLM interaction."""

    @pytest.mark.skipif(not BUILDER_AVAILABLE, reason="DynamicCommandBuilder not implemented")
    async def test_loads_real_metadata(self):
        """Test loading actual tools/metadata.yaml file."""
        builder = DynamicCommandBuilder(llm_router=Mock(), metadata_path="tools/metadata.yaml")

        # Should load metadata successfully
        assert builder.metadata is not None
        assert "tools" in builder.metadata
        assert len(builder.metadata["tools"]) > 0

    @pytest.mark.skipif(not BUILDER_AVAILABLE, reason="DynamicCommandBuilder not implemented")
    async def test_finds_tool_in_metadata(self, mock_llm_router):
        """Test finding specific tool in metadata."""
        builder = DynamicCommandBuilder(
            llm_router=mock_llm_router, metadata_path="tools/metadata.yaml"
        )

        tool_meta = builder._get_tool_metadata("volatility")

        assert tool_meta is not None
        assert tool_meta["name"] == "volatility"
        assert "inputs" in tool_meta
        assert "examples" in tool_meta
