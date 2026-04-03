"""Report Agent - Structured incident report generation.

STUB: Implementation pending April 15 starter code.

The Report Agent:
1. Formats findings into structured report
2. Generates IOC list
3. Creates timeline
4. Links to raw evidence
5. Outputs machine-readable format
"""

from .base import BaseAgent, AgentResult


class ReporterAgent(BaseAgent):
    """Generates structured incident reports.
    
    Output Formats:
    - Markdown (human-readable)
    - JSON (machine-readable)
    - IOC list (importable to SIEM)
    """
    
    def __init__(self):
        super().__init__(name="reporter")
    
    async def process(self, input_data: dict) -> AgentResult:
        """Stub: Implement after April 15 starter code."""
        raise NotImplementedError(
            "ReporterAgent implementation pending starter code. "
            "Will integrate structured report generation."
        )
