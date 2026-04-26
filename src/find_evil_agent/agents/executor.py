"""Execution Agent - Safe SIFT tool execution.

STUB: Implementation pending April 15 starter code.

The Execution Agent ensures security by:
1. Path validation (whitelist allowed directories)
2. Subprocess execution without shell=True
3. Timeout handling
4. Output capture and parsing
5. Error handling
"""

from .base import AgentResult, BaseAgent


class ExecutionAgent(BaseAgent):
    """Executes SIFT tools with security validation.

    Security Features:
    - Path sanitization (prevents /etc/shadow access)
    - Subprocess with arg list (not shell)
    - Configurable timeouts
    - Privilege management
    """

    ALLOWED_PATHS = ["/mnt/evidence/", "/workspace/", "/tmp/sift-workspace/"]  # nosec B108
    DEFAULT_TIMEOUT = 60

    def __init__(self):
        super().__init__(name="executor")

    async def process(self, input_data: dict) -> AgentResult:
        """Stub: Implement after April 15 starter code."""
        raise NotImplementedError(
            "ExecutionAgent implementation pending starter code. "
            "Will integrate with SIFT subprocess management."
        )

    def validate_path(self, path: str) -> bool:
        """Validate path is within allowed directories."""
        from pathlib import Path

        resolved = Path(path).resolve()
        return any(str(resolved).startswith(allowed) for allowed in self.ALLOWED_PATHS)
