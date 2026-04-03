"""Analysis Agent - Threat detection and reasoning.

STUB: Implementation pending April 15 starter code.

The Analysis Agent:
1. Parses tool output for patterns
2. Matches known IOCs
3. Detects anomalies
4. Correlates events by timestamp
5. Assigns confidence scores
"""

from .base import BaseAgent, AgentResult


class AnalysisAgent(BaseAgent):
    """Analyzes tool output for security threats.
    
    Capabilities:
    - Pattern matching for known malware
    - Anomaly detection
    - Timeline correlation
    - Confidence scoring per finding
    """
    
    def __init__(self):
        super().__init__(name="analyzer")
    
    async def process(self, input_data: dict) -> AgentResult:
        """Stub: Implement after April 15 starter code."""
        raise NotImplementedError(
            "AnalysisAgent implementation pending starter code. "
            "Will integrate pattern matching and anomaly detection."
        )
