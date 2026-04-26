"""Exception definitions for tool management.

These exceptions provide structured error handling
across the tool execution pipeline.
"""


class ToolError(Exception):
    """Base exception for tool-related errors."""

    pass


class ValidationError(ToolError):
    """Input validation failed."""

    pass


class TimeoutError(ToolError):
    """Tool execution timed out."""

    pass


class ExecutionError(ToolError):
    """Tool execution failed."""

    def __init__(self, message: str, return_code: int = None, stderr: str = None):
        super().__init__(message)
        self.return_code = return_code
        self.stderr = stderr


class PathError(ValidationError):
    """Path validation failed (security)."""

    pass
