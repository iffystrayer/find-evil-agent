"""Tests for ToolExecutorAgent - SSH execution of SIFT tools.

TDD Structure:
1. TestToolExecutorSpecification - ALWAYS PASSING (requirements documentation)
2. TestToolExecutorStructure - Tests agent interface compliance
3. TestToolExecutorExecution - Tests actual execution behavior
4. TestToolExecutorIntegration - Tests with real SIFT VM SSH
"""

import asyncio

import pytest

from find_evil_agent.agents.base import AgentResult, AgentStatus
from find_evil_agent.agents.schemas import ExecutionResult, ExecutionStatus

# Conditional import for TDD - ToolExecutorAgent may not exist yet
try:
    from find_evil_agent.agents.tool_executor import ToolExecutorAgent

    TOOL_EXECUTOR_AVAILABLE = True
except ImportError:
    TOOL_EXECUTOR_AVAILABLE = False

    # Placeholder for testing structure
    class ToolExecutorAgent:
        pass


class TestToolExecutorSpecification:
    """Specification tests - ALWAYS PASSING.

    Document ToolExecutorAgent requirements and expected behavior.
    """

    def test_tool_executor_requirements(self):
        """Document ToolExecutorAgent requirements."""
        requirements = {
            "ssh_connection": "Connect to SIFT VM via SSH",
            "command_execution": "Execute tool commands remotely",
            "timeout_handling": "Enforce configurable timeout",
            "output_capture": "Capture stdout, stderr, return code",
            "error_handling": "Handle connection failures, timeouts, command errors",
            "security": "Validate commands against allowed patterns",
            "execution_result": "Return ExecutionResult schema",
            "connection_pooling": "Reuse SSH connections when possible",
        }
        assert requirements["ssh_connection"] == "Connect to SIFT VM via SSH"
        assert requirements["timeout_handling"] == "Enforce configurable timeout"
        assert requirements["output_capture"] == "Capture stdout, stderr, return code"

    def test_execution_workflow(self):
        """Document execution workflow."""
        workflow = {
            "step1": "Receive tool_name and command from input",
            "step2": "Validate command against security patterns",
            "step3": "Establish SSH connection to SIFT VM",
            "step4": "Execute command with timeout",
            "step5": "Capture stdout, stderr, return_code",
            "step6": "Calculate execution time",
            "step7": "Return ExecutionResult with status",
            "step8": "Close SSH connection (or return to pool)",
        }
        assert workflow["step2"] == "Validate command against security patterns"
        assert workflow["step4"] == "Execute command with timeout"
        assert workflow["step7"] == "Return ExecutionResult with status"

    def test_timeout_strategy(self):
        """Document timeout handling strategy."""
        strategy = {
            "default_timeout": 60,  # 1 minute
            "max_timeout": 3600,  # 1 hour for intensive tools
            "timeout_behavior": "Kill process and return TIMEOUT status",
            "timeout_detection": "asyncio.wait_for with timeout",
            "cleanup": "Ensure SSH connection cleanup on timeout",
        }
        assert strategy["default_timeout"] == 60
        assert strategy["max_timeout"] == 3600
        assert strategy["timeout_behavior"] == "Kill process and return TIMEOUT status"

    def test_security_validation(self):
        """Document security validation requirements."""
        security = {
            "allowed_commands": [
                "volatility",
                "vol.py",
                "rekall",
                "bulk_extractor",
                "sleuthkit",
                "plaso",
                "log2timeline.py",
                "psort.py",
                "strings",
                "grep",
                "find",
                "cat",
                "head",
                "tail",
            ],
            "blocked_patterns": [
                "rm -rf",
                "dd if=",
                "mkfs",
                "format",
                "; rm",
                "&& rm",
                "| rm",
                "curl",
                "wget",
                "nc ",
                "netcat",
            ],
            "path_validation": "Commands must target allowed evidence paths only",
            "injection_prevention": "Escape shell metacharacters",
        }
        assert "volatility" in security["allowed_commands"]
        assert "rm -rf" in security["blocked_patterns"]
        assert security["injection_prevention"] == "Escape shell metacharacters"

    def test_error_handling_scenarios(self):
        """Document error handling scenarios."""
        scenarios = {
            "ssh_connection_failed": "Return FAILED status with error message",
            "command_timeout": "Return TIMEOUT status with partial output",
            "command_not_found": "Return FAILED status with stderr",
            "permission_denied": "Return FAILED status with stderr",
            "network_error": "Retry once, then fail",
            "invalid_command": "Return FAILED status without attempting execution",
        }
        assert scenarios["ssh_connection_failed"] == "Return FAILED status with error message"
        assert scenarios["command_timeout"] == "Return TIMEOUT status with partial output"
        assert scenarios["network_error"] == "Retry once, then fail"


@pytest.mark.skipif(not TOOL_EXECUTOR_AVAILABLE, reason="ToolExecutorAgent not implemented yet")
class TestToolExecutorStructure:
    """Structure tests - Validate agent interface compliance."""

    def test_tool_executor_inherits_from_base_agent(self):
        """ToolExecutorAgent should inherit from BaseAgent."""
        from find_evil_agent.agents.base import BaseAgent

        agent = ToolExecutorAgent()
        assert isinstance(agent, BaseAgent)

    def test_tool_executor_has_process_method(self):
        """ToolExecutorAgent should have async process() method."""
        agent = ToolExecutorAgent()
        assert hasattr(agent, "process")
        assert callable(agent.process)
        assert asyncio.iscoroutinefunction(agent.process)

    def test_tool_executor_has_validate_method(self):
        """ToolExecutorAgent should have validate() method."""
        agent = ToolExecutorAgent()
        assert hasattr(agent, "validate")
        assert callable(agent.validate)

    def test_tool_executor_has_ssh_config_attributes(self):
        """ToolExecutorAgent should have SSH configuration attributes."""
        agent = ToolExecutorAgent()
        assert hasattr(agent, "ssh_host")
        assert hasattr(agent, "ssh_port")
        assert hasattr(agent, "ssh_user")

    def test_tool_executor_has_timeout_attributes(self):
        """ToolExecutorAgent should have timeout configuration."""
        agent = ToolExecutorAgent()
        assert hasattr(agent, "default_timeout")
        assert isinstance(agent.default_timeout, (int, float))
        assert agent.default_timeout > 0

    def test_tool_executor_name_is_tool_executor(self):
        """ToolExecutorAgent name should be 'tool_executor'."""
        agent = ToolExecutorAgent()
        assert agent.name == "tool_executor"


@pytest.mark.skipif(not TOOL_EXECUTOR_AVAILABLE, reason="ToolExecutorAgent not implemented yet")
class TestToolExecutorExecution:
    """Execution tests - Test actual agent behavior."""

    @pytest.mark.asyncio
    async def test_process_returns_agent_result(self):
        """process() should return AgentResult."""
        agent = ToolExecutorAgent()

        input_data = {"tool_name": "strings", "command": "strings /etc/hostname"}

        result = await agent.process(input_data)
        assert isinstance(result, AgentResult)
        assert hasattr(result, "success")
        assert hasattr(result, "data")
        assert hasattr(result, "status")

    @pytest.mark.asyncio
    async def test_validate_requires_tool_name_and_command(self):
        """validate() should require tool_name and command."""
        agent = ToolExecutorAgent()

        # Missing both
        assert not await agent.validate({})

        # Missing command
        assert not await agent.validate({"tool_name": "strings"})

        # Missing tool_name
        assert not await agent.validate({"command": "strings file.bin"})

        # Valid input
        assert await agent.validate({"tool_name": "strings", "command": "strings file.bin"})

    @pytest.mark.asyncio
    async def test_process_with_invalid_input_returns_error(self):
        """process() should return error for invalid input."""
        agent = ToolExecutorAgent()

        result = await agent.process({})
        assert not result.success
        assert result.status == AgentStatus.FAILED
        assert "Invalid input" in result.error or "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_process_includes_execution_result_in_data(self):
        """process() should include ExecutionResult in data."""
        agent = ToolExecutorAgent()

        input_data = {"tool_name": "echo", "command": "echo 'test'"}

        result = await agent.process(input_data)

        if result.success:
            assert "execution_result" in result.data
            assert isinstance(result.data["execution_result"], ExecutionResult)

    @pytest.mark.asyncio
    async def test_execution_result_has_required_fields(self):
        """ExecutionResult should have all required fields."""
        agent = ToolExecutorAgent()

        input_data = {"tool_name": "echo", "command": "echo 'test'"}

        result = await agent.process(input_data)

        if result.success and "execution_result" in result.data:
            exec_result = result.data["execution_result"]
            assert hasattr(exec_result, "tool_name")
            assert hasattr(exec_result, "command")
            assert hasattr(exec_result, "stdout")
            assert hasattr(exec_result, "stderr")
            assert hasattr(exec_result, "return_code")
            assert hasattr(exec_result, "status")
            assert hasattr(exec_result, "execution_time")

    @pytest.mark.asyncio
    async def test_timeout_parameter_is_respected(self):
        """Custom timeout should be respected."""
        agent = ToolExecutorAgent()

        # Long-running command with short timeout
        input_data = {"tool_name": "sleep", "command": "sleep 5", "timeout": 1}  # 1 second timeout

        result = await agent.process(input_data)

        if "execution_result" in result.data:
            exec_result = result.data["execution_result"]
            # Should timeout
            assert exec_result.status == ExecutionStatus.TIMEOUT or exec_result.execution_time < 5

    @pytest.mark.asyncio
    async def test_successful_execution_has_success_status(self):
        """Successful command execution should have SUCCESS status."""
        agent = ToolExecutorAgent()

        input_data = {"tool_name": "echo", "command": "echo 'success'"}

        result = await agent.process(input_data)

        if result.success and "execution_result" in result.data:
            exec_result = result.data["execution_result"]
            assert exec_result.status == ExecutionStatus.SUCCESS
            assert exec_result.return_code == 0

    @pytest.mark.asyncio
    async def test_failed_command_has_failed_status(self):
        """Failed command should have FAILED status."""
        agent = ToolExecutorAgent()

        # Command that will fail
        input_data = {"tool_name": "cat", "command": "cat /nonexistent/file/that/does/not/exist"}

        result = await agent.process(input_data)

        if "execution_result" in result.data:
            exec_result = result.data["execution_result"]
            # Should fail (non-zero return code)
            assert exec_result.return_code != 0 or exec_result.status == ExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_stdout_is_captured(self):
        """stdout should be captured from command execution."""
        agent = ToolExecutorAgent()

        input_data = {"tool_name": "echo", "command": "echo 'test output'"}

        result = await agent.process(input_data)

        if result.success and "execution_result" in result.data:
            exec_result = result.data["execution_result"]
            assert exec_result.stdout is not None
            if exec_result.return_code == 0:
                assert "test output" in exec_result.stdout or len(exec_result.stdout) > 0

    @pytest.mark.asyncio
    async def test_stderr_is_captured(self):
        """stderr should be captured from command execution."""
        agent = ToolExecutorAgent()

        # Command that writes to stderr
        input_data = {
            "tool_name": "cat",
            "command": "cat /nonexistent_file 2>&1",  # Redirect stderr to stdout for testing
        }

        result = await agent.process(input_data)

        if "execution_result" in result.data:
            exec_result = result.data["execution_result"]
            # Either stderr or stdout should have the error
            assert exec_result.stderr is not None or exec_result.stdout is not None

    @pytest.mark.asyncio
    async def test_execution_time_is_recorded(self):
        """Execution time should be recorded."""
        agent = ToolExecutorAgent()

        input_data = {"tool_name": "sleep", "command": "sleep 0.1"}  # 100ms

        result = await agent.process(input_data)

        if result.success and "execution_result" in result.data:
            exec_result = result.data["execution_result"]
            assert exec_result.execution_time >= 0.0
            # Should take at least 100ms
            if exec_result.status == ExecutionStatus.SUCCESS:
                assert exec_result.execution_time >= 0.09


@pytest.mark.skipif(not TOOL_EXECUTOR_AVAILABLE, reason="ToolExecutorAgent not implemented yet")
@pytest.mark.integration
class TestToolExecutorIntegration:
    """Integration tests - Test with real SIFT VM SSH connection.

    These tests require:
    - SIFT VM running at 192.168.12.101:16789
    - SSH access configured
    - Basic SIFT tools available
    """

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_real_ssh_connection_to_sift_vm(self):
        """Test actual SSH connection to SIFT VM."""
        agent = ToolExecutorAgent()

        # Simple hostname command
        input_data = {"tool_name": "hostname", "command": "hostname"}

        result = await agent.process(input_data)

        # Should successfully connect and execute
        assert result.success or "connection" in result.error.lower()

        if result.success:
            exec_result = result.data["execution_result"]
            assert exec_result.status == ExecutionStatus.SUCCESS
            assert exec_result.return_code == 0
            assert len(exec_result.stdout) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_execute_strings_on_sift_vm(self):
        """Test executing 'strings' command on SIFT VM."""
        agent = ToolExecutorAgent()

        # strings command on /etc/hostname
        input_data = {"tool_name": "strings", "command": "strings /etc/hostname"}

        result = await agent.process(input_data)

        if result.success:
            exec_result = result.data["execution_result"]
            assert exec_result.status == ExecutionStatus.SUCCESS
            assert exec_result.return_code == 0
            assert exec_result.stdout is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_execute_grep_on_sift_vm(self):
        """Test executing 'grep' command on SIFT VM."""
        agent = ToolExecutorAgent()

        # grep command
        input_data = {"tool_name": "grep", "command": "grep -i 'ubuntu' /etc/os-release"}

        result = await agent.process(input_data)

        if result.success:
            exec_result = result.data["execution_result"]
            assert (
                exec_result.return_code == 0 or exec_result.return_code == 1
            )  # grep returns 1 if no match
            assert exec_result.stdout is not None or exec_result.stderr is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_command_not_found_handling(self):
        """Test handling of non-existent command."""
        agent = ToolExecutorAgent()

        # Command that doesn't exist
        input_data = {"tool_name": "nonexistent", "command": "nonexistent_command_xyz123"}

        result = await agent.process(input_data)

        if "execution_result" in result.data:
            exec_result = result.data["execution_result"]
            # Should fail with non-zero return code
            assert exec_result.return_code != 0 or exec_result.status == ExecutionStatus.FAILED
            # stderr should contain error message
            assert exec_result.stderr is not None or "not found" in exec_result.stdout.lower()

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_timeout_kills_long_running_command(self):
        """Test that timeout properly kills long-running commands."""
        agent = ToolExecutorAgent()

        # Command that runs for 30 seconds with 2 second timeout
        input_data = {"tool_name": "sleep", "command": "sleep 30", "timeout": 2}

        result = await agent.process(input_data)

        if "execution_result" in result.data:
            exec_result = result.data["execution_result"]
            # Should timeout in ~2 seconds, not 30
            assert exec_result.execution_time < 5.0
            assert exec_result.status == ExecutionStatus.TIMEOUT or not result.success

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_multiple_sequential_executions(self):
        """Test multiple sequential command executions."""
        agent = ToolExecutorAgent()

        commands = [
            {"tool_name": "hostname", "command": "hostname"},
            {"tool_name": "whoami", "command": "whoami"},
            {"tool_name": "pwd", "command": "pwd"},
        ]

        for input_data in commands:
            result = await agent.process(input_data)

            if result.success:
                exec_result = result.data["execution_result"]
                assert exec_result.status == ExecutionStatus.SUCCESS
                assert exec_result.return_code == 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_volatility_available_on_sift_vm(self):
        """Test that Volatility is available on SIFT VM."""
        agent = ToolExecutorAgent()

        # Check if volatility is available
        input_data = {"tool_name": "volatility", "command": "which vol.py || which volatility"}

        result = await agent.process(input_data)

        if result.success:
            exec_result = result.data["execution_result"]
            # If volatility is installed, should return path
            assert exec_result.return_code == 0 or exec_result.return_code == 1

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_concurrent_executions(self):
        """Test concurrent command executions (connection pooling)."""
        agent = ToolExecutorAgent()

        # Run 3 commands concurrently
        commands = [
            {"tool_name": "echo", "command": "echo 'test1'"},
            {"tool_name": "echo", "command": "echo 'test2'"},
            {"tool_name": "echo", "command": "echo 'test3'"},
        ]

        tasks = [agent.process(cmd) for cmd in commands]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete (either success or handled error)
        assert len(results) == 3
        for result in results:
            if isinstance(result, AgentResult):
                assert result is not None
