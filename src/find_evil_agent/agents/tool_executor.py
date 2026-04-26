"""Tool Executor Agent - SSH execution of SIFT tools.

This agent executes forensic tools on the SIFT VM via SSH:
1. Validates command against security patterns
2. Establishes SSH connection to SIFT VM
3. Executes command with timeout
4. Captures stdout, stderr, return code
5. Returns ExecutionResult with metrics

Example:
    >>> agent = ToolExecutorAgent()
    >>> result = await agent.process({
    ...     "tool_name": "volatility",
    ...     "command": "vol.py -f memory.dmp pslist"
    ... })
    >>> exec_result = result.data['execution_result']
    >>> exec_result.return_code
    0
    >>> exec_result.stdout
    'Volatility Foundation Volatility Framework...'
"""

import asyncio
import time
from typing import Any

import asyncssh
import structlog

from find_evil_agent.config.settings import get_settings
from find_evil_agent.parsers.factory import get_parser_factory
from find_evil_agent.telemetry import log_agent_error

from .base import AgentResult, AgentStatus, BaseAgent
from .schemas import ExecutionResult, ExecutionStatus

agent_logger = structlog.get_logger()


# Security: Blocked command patterns
BLOCKED_PATTERNS = [
    "rm -rf",
    "dd if=",
    "mkfs",
    "format",
    "; rm",
    "&& rm",
    "| rm",
    "curl http",
    "wget ",
    "nc ",
    "netcat",
    "> /dev/",
]


class ToolExecutorAgent(BaseAgent):
    """Executes SIFT tools via SSH with timeout and security validation.

    Key Features:
    - SSH connection to SIFT VM
    - Command timeout enforcement
    - stdout/stderr/return_code capture
    - Execution time tracking
    - Security validation (blocked patterns)
    - Connection cleanup

    Attributes:
        ssh_host: SIFT VM hostname/IP
        ssh_port: SSH port
        ssh_user: SSH username
        ssh_key_path: Path to SSH private key (optional)
        default_timeout: Default command timeout in seconds
        max_timeout: Maximum allowed timeout
    """

    def __init__(
        self,
        ssh_host: str | None = None,
        ssh_port: int | None = None,
        ssh_user: str | None = None,
        ssh_key_path: str | None = None,
        default_timeout: int = 60,
        max_timeout: int = 3600,
        **kwargs,
    ):
        """Initialize Tool Executor Agent.

        Args:
            ssh_host: SIFT VM hostname (defaults to settings)
            ssh_port: SSH port (defaults to settings)
            ssh_user: SSH username (defaults to settings)
            ssh_key_path: Path to SSH private key (optional)
            default_timeout: Default timeout in seconds
            max_timeout: Maximum allowed timeout in seconds
            **kwargs: Passed to BaseAgent
        """
        super().__init__(name="tool_executor", **kwargs)

        settings = get_settings()

        self.ssh_host = ssh_host or settings.sift_vm_host
        self.ssh_port = ssh_port or settings.sift_vm_port
        self.ssh_user = ssh_user or settings.sift_ssh_user
        self.ssh_key_path = ssh_key_path or settings.sift_ssh_key_path
        self.default_timeout = default_timeout
        self.max_timeout = max_timeout

        agent_logger.info(
            "tool_executor_initialized",
            ssh_host=self.ssh_host,
            ssh_port=self.ssh_port,
            ssh_user=self.ssh_user,
            default_timeout=self.default_timeout,
        )

    async def process(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute tool command on SIFT VM.

        Args:
            input_data: Dict with keys:
                - tool_name: str (name of the tool)
                - command: str (command to execute)
                - timeout: int (optional, timeout in seconds)

        Returns:
            AgentResult with:
                - success: True if command executed (even with non-zero exit)
                - data: {"execution_result": ExecutionResult}
                - status: SUCCESS, TIMEOUT, or FAILED

        Example:
            >>> result = await agent.process({
            ...     "tool_name": "strings",
            ...     "command": "strings /evidence/malware.bin",
            ...     "timeout": 30
            ... })
            >>> result.success
            True
            >>> result.data['execution_result'].return_code
            0
        """
        try:
            # Validate input
            if not await self.validate(input_data):
                return AgentResult(
                    success=False,
                    data={},
                    status=AgentStatus.FAILED,
                    error="Invalid input: tool_name and command are required",
                )

            tool_name = input_data["tool_name"]
            command = input_data["command"]
            timeout = input_data.get("timeout", self.default_timeout)

            # Enforce max timeout
            timeout = min(timeout, self.max_timeout)

            agent_logger.info(
                "tool_execution_started",
                agent=self.name,
                tool=tool_name,
                command=command[:100],  # Truncate for logging
                timeout=timeout,
            )

            # Validate command security
            if not self._validate_command_security(command):
                log_agent_error(
                    agent_name=self.name,
                    error_type="security_validation",
                    error_message=f"Command blocked by security rules: {command}",
                    tool=tool_name,
                )

                return AgentResult(
                    success=False,
                    data={},
                    status=AgentStatus.FAILED,
                    error="Command blocked by security validation: contains dangerous patterns",
                )

            # Execute command via SSH
            exec_result = await self._execute_ssh_command(
                tool_name=tool_name, command=command, timeout=timeout
            )

            # Determine overall status
            if exec_result.status == ExecutionStatus.SUCCESS:
                status = AgentStatus.SUCCESS
                success = True
            elif exec_result.status == ExecutionStatus.TIMEOUT:
                status = AgentStatus.FAILED
                success = False
            else:
                # Command failed but execution completed
                status = AgentStatus.FAILED
                success = False

            # Parse output if parser available
            if exec_result.stdout and exec_result.status == ExecutionStatus.SUCCESS:
                exec_result = self._parse_output(exec_result, input_data)

            agent_logger.info(
                "tool_execution_completed",
                tool=tool_name,
                status=exec_result.status.value,
                return_code=exec_result.return_code,
                execution_time=exec_result.execution_time,
                stdout_length=len(exec_result.stdout or ""),
                stderr_length=len(exec_result.stderr or ""),
                parsed=exec_result.parsed_output is not None,
            )

            return AgentResult(
                success=success,
                data={"execution_result": exec_result},
                status=status,
                error=None if success else f"Command failed with code {exec_result.return_code}",
            )

        except Exception as e:
            log_agent_error(
                agent_name=self.name, error_type="execution_error", error_message=str(e)
            )

            return AgentResult(
                success=False,
                data={},
                status=AgentStatus.FAILED,
                error=f"Tool execution failed: {e}",
            )

    async def validate(self, input_data: dict[str, Any]) -> bool:
        """Validate input data.

        Args:
            input_data: Input dict to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["tool_name", "command"]
        for field in required_fields:
            if field not in input_data or not input_data[field]:
                return False
        return True

    def _validate_command_security(self, command: str) -> bool:
        """Validate command against security patterns.

        Args:
            command: Command to validate

        Returns:
            True if safe, False if blocked
        """
        command_lower = command.lower()

        # Check blocked patterns
        for pattern in BLOCKED_PATTERNS:
            if pattern in command_lower:
                agent_logger.warning("command_blocked", pattern=pattern, command=command[:100])
                return False

        return True

    async def _execute_ssh_command(
        self, tool_name: str, command: str, timeout: int
    ) -> ExecutionResult:
        """Execute command via SSH with timeout.

        Args:
            tool_name: Name of the tool
            command: Command to execute
            timeout: Timeout in seconds

        Returns:
            ExecutionResult with execution details
        """
        start_time = time.time()

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._run_ssh_command(tool_name, command), timeout=timeout
            )

            execution_time = time.time() - start_time
            result.execution_time = execution_time

            return result

        except TimeoutError:
            execution_time = time.time() - start_time

            agent_logger.warning(
                "command_timeout", tool=tool_name, timeout=timeout, execution_time=execution_time
            )

            return ExecutionResult(
                tool_name=tool_name,
                command=command,
                stdout=None,
                stderr=f"Command timed out after {timeout} seconds",
                return_code=-1,
                status=ExecutionStatus.TIMEOUT,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time

            agent_logger.error(
                "ssh_execution_error", tool=tool_name, error=str(e), execution_time=execution_time
            )

            return ExecutionResult(
                tool_name=tool_name,
                command=command,
                stdout=None,
                stderr=f"SSH execution error: {e}",
                return_code=-1,
                status=ExecutionStatus.FAILED,
                execution_time=execution_time,
            )

    async def _run_ssh_command(self, tool_name: str, command: str) -> ExecutionResult:
        """Run command via SSH connection.

        Args:
            tool_name: Name of the tool
            command: Command to execute

        Returns:
            ExecutionResult with output
        """
        conn = None

        try:
            # Establish SSH connection
            agent_logger.debug(
                "ssh_connecting", host=self.ssh_host, port=self.ssh_port, user=self.ssh_user
            )

            # Build connection kwargs
            connect_kwargs = {
                "host": self.ssh_host,
                "port": self.ssh_port,
                "username": self.ssh_user,
                "known_hosts": None,  # Disable strict host key checking for now
            }

            # Add SSH key if provided
            if self.ssh_key_path:
                connect_kwargs["client_keys"] = [self.ssh_key_path]

            # Connect
            conn = await asyncssh.connect(**connect_kwargs)

            agent_logger.debug("ssh_connected", host=self.ssh_host)

            # Execute command
            result = await conn.run(command, check=False)

            # Extract output
            stdout = result.stdout if result.stdout else ""
            stderr = result.stderr if result.stderr else ""
            return_code = result.exit_status if result.exit_status is not None else -1

            # Determine status
            if return_code == 0:
                status = ExecutionStatus.SUCCESS
            else:
                status = ExecutionStatus.FAILED

            agent_logger.debug(
                "ssh_command_completed",
                tool=tool_name,
                return_code=return_code,
                stdout_length=len(stdout),
                stderr_length=len(stderr),
            )

            return ExecutionResult(
                tool_name=tool_name,
                command=command,
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                status=status,
                execution_time=0.0,  # Will be set by caller
            )

        except asyncssh.Error as e:
            agent_logger.error(
                "ssh_error", tool=tool_name, error=str(e), error_type=type(e).__name__
            )

            return ExecutionResult(
                tool_name=tool_name,
                command=command,
                stdout=None,
                stderr=f"SSH error: {e}",
                return_code=-1,
                status=ExecutionStatus.FAILED,
                execution_time=0.0,
            )

        finally:
            # Cleanup connection
            if conn:
                conn.close()
                await conn.wait_closed()
                agent_logger.debug("ssh_connection_closed")

    def _parse_output(self, exec_result: ExecutionResult, input_data: dict) -> ExecutionResult:
        """Parse tool output using appropriate parser.

        Args:
            exec_result: Execution result with raw stdout
            input_data: Original input data (may contain parser hints)

        Returns:
            ExecutionResult with parsed_output populated
        """
        try:
            factory = get_parser_factory()
            tool_name = exec_result.tool_name

            # Determine parser kwargs from input data
            parser_kwargs = {}

            # Volatility: extract plugin name
            if "volatility" in tool_name.lower():
                command = exec_result.command or ""
                if "pslist" in command:
                    parser_kwargs["plugin"] = "pslist"
                elif "netscan" in command:
                    parser_kwargs["plugin"] = "netscan"
                elif "malfind" in command:
                    parser_kwargs["plugin"] = "malfind"

            # Timeline: assume CSV format
            elif tool_name.lower() in ["psort", "log2timeline"]:
                parser_kwargs["format"] = "csv"

            # TSK tools: set tool name
            elif tool_name.lower() in ["fls", "mmls", "fsstat"]:
                parser_kwargs["tool"] = tool_name.lower()

            # Strings: enable IOC detection
            elif tool_name.lower() == "strings":
                parser_kwargs["min_length"] = 10
                parser_kwargs["detect_obfuscation"] = True
                parser_kwargs["extract_iocs"] = True

            # Grep: enable IOC extraction
            elif tool_name.lower() in ["grep", "egrep"]:
                parser_kwargs["extract_iocs"] = True

            # Attempt parsing
            parse_result = factory.parse(tool_name, exec_result.stdout, **parser_kwargs)

            if parse_result and parse_result.success:
                # Convert parsed data to dict for ExecutionResult
                if hasattr(parse_result.data, "__dict__"):
                    exec_result.parsed_output = parse_result.data.__dict__
                else:
                    exec_result.parsed_output = {"data": parse_result.data}

                agent_logger.debug("output_parsed", tool=tool_name, parser_kwargs=parser_kwargs)
            else:
                agent_logger.debug(
                    "parsing_failed_or_unavailable",
                    tool=tool_name,
                    has_parser=factory.supports_tool(tool_name),
                )

        except Exception as e:
            agent_logger.warning("parse_error", tool=exec_result.tool_name, error=str(e))
            # Don't fail execution if parsing fails
            pass

        return exec_result
