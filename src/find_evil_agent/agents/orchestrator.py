"""Orchestrator Agent - Entry point for DFIR workflow.

STUB: Implementation pending April 15 starter code.

The Orchestrator Agent:
1. Receives incident description from user
2. Initializes workflow state
3. Dispatches to appropriate workflow path
4. Coordinates overall execution
"""

from .base import BaseAgent, AgentResult


class OrchestratorAgent(BaseAgent):
    """Entry point for the Find Evil DFIR agent system.    
    This agent is responsible for:
    - Validating user input
    - Selecting appropriate workflow (memory, disk, network)
    - Initializing shared state
    - Coordinating agent execution
    """
    
    def __init__(self):
        super().__init__(name="orchestrator")
    
    async def process(self, input_data: dict) -> AgentResult:
        """Stub: Implement after April 15 starter code."""
        raise NotImplementedError(
            "Orchestrator implementation pending starter code release. "
            "Scheduled for April 15, 2026."
        )
