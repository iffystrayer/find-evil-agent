"""
Security validators for path and command validation.

Prevents:
- Path traversal attacks (../, ~/, /etc/, /root/)
- Command injection (;, |, &, $(), ``, >, <, \n)
- Unauthorized path access
"""

import re
from pathlib import Path


class SecurityValidationError(Exception):
    """Raised when security validation fails."""

    pass


class PathValidator:
    """
    Validates file paths to prevent traversal attacks and unauthorized access.

    Features:
    - Blocks parent directory traversal (../)
    - Blocks home directory access (~/)
    - Blocks system directories (/etc/, /root/)
    - Allows forensic logs (/var/log/)
    - Enforces whitelist if provided
    - Normalizes paths before validation
    """

    def __init__(self, whitelist: list[str] | None = None):
        """
        Initialize path validator.

        Args:
            whitelist: Optional list of allowed path prefixes.
                      If provided, only paths under these prefixes are allowed.
        """
        self.whitelist = whitelist or []
        # Normalize whitelist paths
        self.whitelist = [str(Path(p).resolve()) for p in self.whitelist]

    def validate_path(self, path: str) -> None:
        """
        Validate a file path for security.

        Args:
            path: Path to validate

        Raises:
            SecurityValidationError: If path fails validation
        """
        # Check for empty/whitespace
        if not path or not path.strip():
            raise SecurityValidationError("empty path not allowed")

        path = path.strip()

        # Check for unicode characters (potential evasion)
        try:
            path.encode("ascii")
        except UnicodeEncodeError:
            raise SecurityValidationError(f"non-ASCII characters not allowed in path: {path}")

        # Normalize path to resolve .. and other sequences
        try:
            normalized = str(Path(path).resolve())
        except (ValueError, OSError) as e:
            raise SecurityValidationError(f"Invalid path: {e}")

        # Check for path traversal patterns (before and after normalization)
        if ".." in path:
            raise SecurityValidationError(f"path traversal detected in: {path}")

        # Block home directory access
        if path.startswith("~/") or path.startswith("~"):
            raise SecurityValidationError(f"home directory access not allowed: {path}")

        # Block system directories
        dangerous_prefixes = {
            "/etc/": "system directory",
            "/root/": "root directory",
            "/var/www/": "web directory",
            "/var/lib/": "system directory",
            "/var/cache/": "cache directory",
            "/sys/": "system directory",
            "/proc/": "system directory",
            "/dev/": "device directory",
        }

        # Check both original and normalized paths
        for prefix, desc in dangerous_prefixes.items():
            if normalized.startswith(prefix) or path.startswith(prefix):
                raise SecurityValidationError(f"{desc} access not allowed: {normalized}")

        # Also handle /private/var on macOS (symlink resolution)
        private_dangerous_prefixes = {
            "/private/var/www/": "web directory",
            "/private/var/lib/": "system directory",
            "/private/var/cache/": "cache directory",
        }

        for prefix, desc in private_dangerous_prefixes.items():
            if normalized.startswith(prefix):
                raise SecurityValidationError(f"{desc} access not allowed: {normalized}")

        # Allow /var/log for forensic analysis, block other /var subdirs
        if normalized.startswith("/var/") and not normalized.startswith("/var/log/"):
            # Check if it's already been caught by dangerous_prefixes
            caught = any(normalized.startswith(prefix) for prefix in dangerous_prefixes)
            if not caught:
                raise SecurityValidationError(f"/var directory access restricted: {normalized}")

        # Check against root directory evasion
        if normalized in ["/", "/root", "/etc", "/sys", "/proc", "/dev"]:
            raise SecurityValidationError(f"Root directory access not allowed: {normalized}")

        # Enforce whitelist if provided
        if self.whitelist:
            allowed = False
            for allowed_prefix in self.whitelist:
                if normalized.startswith(allowed_prefix):
                    allowed = True
                    break

            if not allowed:
                raise SecurityValidationError(
                    f"Path not in whitelist: {normalized}. "
                    f"Allowed prefixes: {', '.join(self.whitelist)}"
                )


class CommandValidator:
    """
    Validates shell commands to prevent injection attacks.

    Features:
    - Blocks command chaining (;, |, &)
    - Blocks command substitution ($(), ``)
    - Blocks redirection (>, <)
    - Blocks newline injection
    - Allows safe commands with standard arguments
    """

    # Dangerous patterns that indicate injection attempts
    INJECTION_PATTERNS = [
        r";",  # Command chaining
        r"\|",  # Pipe to another command
        r"&",  # Background execution / chaining
        r"\$\(",  # Command substitution $(...)
        r"`",  # Backtick command substitution
        r"\n",  # Newline injection
        r"\r",  # Carriage return
    ]

    REDIRECTION_PATTERNS = [
        r">",  # Output redirection
        r"<",  # Input redirection
        r">>",  # Append redirection
    ]

    def __init__(self):
        """Initialize command validator."""
        # Compile patterns for efficiency
        self.injection_regex = re.compile("|".join(self.INJECTION_PATTERNS))
        self.redirection_regex = re.compile("|".join(self.REDIRECTION_PATTERNS))

    def validate_command(self, command: str) -> None:
        """
        Validate a shell command for security.

        Args:
            command: Command to validate

        Raises:
            SecurityValidationError: If command fails validation
        """
        # Check for empty/whitespace
        if not command or not command.strip():
            raise SecurityValidationError("Command cannot be empty")

        command = command.strip()

        # Check for command injection patterns
        if self.injection_regex.search(command):
            raise SecurityValidationError(f"Command injection pattern detected in: {command}")

        # Check for redirection patterns
        if self.redirection_regex.search(command):
            raise SecurityValidationError(f"Command redirection not allowed in: {command}")

        # Additional checks for specific dangerous patterns
        if "&&" in command or "||" in command:
            raise SecurityValidationError(f"Command chaining (&&, ||) not allowed in: {command}")
