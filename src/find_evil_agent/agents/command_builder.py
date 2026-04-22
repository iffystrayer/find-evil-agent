"""Dynamic command builder for forensic tools.

Constructs tool commands dynamically using LLM and tool metadata,
replacing hardcoded command strings with context-aware generation.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

from find_evil_agent.agents.schemas import ToolSelection


class DynamicCommandBuilder:
    """Build forensic tool commands dynamically using LLM and metadata.

    Replaces hardcoded command strings with intelligent command construction
    based on tool metadata, investigation context, and evidence paths.
    """

    # Security: Dangerous patterns that indicate command injection
    INJECTION_PATTERNS = [
        r';',           # Command separator
        r'\|',          # Pipe
        r'&',           # Background/AND
        r'\$\(',        # Command substitution
        r'`',           # Backticks
        r'>',           # Redirect
        r'<',           # Redirect
        r'\n',          # Newline
        r'\r',          # Carriage return
    ]

    # Security: Path traversal patterns
    TRAVERSAL_PATTERNS = [
        r'\.\.',        # Parent directory
        r'~/',          # Home directory
        r'/etc/',       # System files
        r'/root/',      # Root home
        r'/var/',       # Variable data (except /var/log)
    ]

    def __init__(
        self,
        llm_router,
        metadata_path: str = "tools/metadata.yaml",
        validate_paths: bool = False
    ):
        """Initialize command builder.

        Args:
            llm_router: LLM router instance for command generation
            metadata_path: Path to tool metadata YAML file
            validate_paths: Whether to validate evidence paths exist (False for SSH)
        """
        self.llm_router = llm_router
        self.metadata_path = Path(metadata_path)
        self.validate_paths = validate_paths

        # Load tool metadata
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load tool metadata from YAML file.

        Returns:
            Metadata dictionary
        """
        with open(self.metadata_path, 'r') as f:
            return yaml.safe_load(f)

    def _get_tool_metadata(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool metadata dictionary or None if not found
        """
        for tool in self.metadata.get("tools", []):
            if tool["name"] == tool_name:
                return tool
        return None

    async def build_command(
        self,
        tool_selection: ToolSelection,
        context: Dict[str, Any]
    ) -> str:
        """Build command dynamically using LLM and metadata.

        Args:
            tool_selection: Selected tool with rationale
            context: Investigation context with incident, goal, evidence_paths

        Returns:
            Validated command string

        Raises:
            ValueError: If command contains injection or traversal attempts
            FileNotFoundError: If validate_paths=True and paths don't exist
        """
        # Get tool metadata
        tool_meta = self._get_tool_metadata(tool_selection.tool_name)
        if not tool_meta:
            raise ValueError(f"Tool {tool_selection.tool_name} not found in metadata")

        # Build LLM prompt for command construction
        prompt = self._build_command_prompt(tool_selection, tool_meta, context)

        # Generate command using LLM
        response = await self.llm_router.route(
            message=prompt,
            category="command_generation"
        )

        if not response.success:
            raise ValueError(f"LLM command generation failed: {response.error}")

        command = response.content.strip()

        # Validate command security
        self._validate_command(command, context.get("evidence_paths", []))

        return command

    def _build_command_prompt(
        self,
        tool_selection: ToolSelection,
        tool_meta: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Build LLM prompt for command generation.

        Args:
            tool_selection: Selected tool
            tool_meta: Tool metadata from YAML
            context: Investigation context

        Returns:
            Formatted prompt string
        """
        evidence_paths = context.get("evidence_paths", [])
        incident = context.get("incident", "")
        goal = context.get("goal", "")

        prompt = f"""You are a forensic command builder. Construct a valid command for the tool "{tool_selection.tool_name}".

**Tool Metadata:**
- Name: {tool_meta['name']}
- Description: {tool_meta['description']}
- Command: {tool_meta['command']}

**Inputs:**
"""
        for inp in tool_meta.get("inputs", []):
            desc = inp.get('description', 'No description')
            prompt += f"  - {inp['name']} ({inp['type']}): {desc}"
            if inp.get("required"):
                prompt += " [REQUIRED]"
            if "examples" in inp:
                prompt += f" Examples: {', '.join(inp['examples'])}"
            prompt += "\n"

        prompt += f"""
**Example Commands:**
"""
        for example in tool_meta.get("examples", []):
            prompt += f"  - {example}\n"

        prompt += f"""
**Investigation Context:**
- Incident: {incident}
- Goal: {goal}
- Tool Selection Reason: {tool_selection.reason}

**Available Evidence Files:**
"""
        for path in evidence_paths:
            prompt += f"  - {path}\n"

        prompt += """
**Instructions:**
1. Construct a valid command using the tool's syntax from the examples
2. Use appropriate evidence file(s) from the available paths
3. Include necessary parameters based on the investigation goal
4. Return ONLY the command string, no explanations
5. Do NOT include multiple commands, pipes, redirects, or shell metacharacters
6. If the tool requires a profile (e.g., volatility), infer from context or use a common default

**Command:**"""

        return prompt

    def _validate_command(self, command: str, evidence_paths: List[str]) -> None:
        """Validate command for security issues.

        Args:
            command: Generated command string
            evidence_paths: List of allowed evidence paths

        Raises:
            ValueError: If command contains injection or traversal attempts
            FileNotFoundError: If validate_paths=True and paths don't exist
        """
        # Check for command injection patterns
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, command):
                raise ValueError(f"Command injection detected: {pattern}")

        # Check for path traversal (except /var/log which is allowed)
        for pattern in self.TRAVERSAL_PATTERNS:
            if pattern == r'/var/' and '/var/log' in command:
                continue  # Allow /var/log
            if re.search(pattern, command):
                raise ValueError(f"Path traversal detected: {pattern}")

        # Optionally validate evidence paths exist
        if self.validate_paths:
            for path_str in evidence_paths:
                path = Path(path_str)
                if not path.exists():
                    raise FileNotFoundError(f"Evidence path not found: {path_str}")
