"""Abstract base class for all agents.

This module defines the interface that all agents must implement.
The actual implementation will be adapted to the starter code provided
on April 15, 2026.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol
from dataclasses import dataclass
from enum import Enum


class AgentStatus(Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class AgentResult:
    """Standard result structure for all agents.
    
    Attributes:
        success: Whether the agent completed successfully
        data: Output data from the agent
        confidence: Confidence score (0.0-1.0)
        status: Execution status
        error: Error message if failed
        metadata: Additional context
    """
    success: bool
    data: dict[str, Any]
    confidence: float = 0.0
    status: AgentStatus = AgentStatus.PENDING
    error: str | None = None
    metadata: dict[str, Any] | None = None


class BaseAgent(ABC):
    """Abstract base class for all DFIR agents.
    
    All agents in the Find Evil system must inherit from this class
    and implement the process method. This ensures consistent
    interfaces and enables the LangGraph workflow.
    
    Note:
        This is an interface definition. Implementation will be
        completed after April 15 starter code release.
    
    Example:
        >>> class MyAgent(BaseAgent):
        ...     async def process(self, input_data: dict) -> AgentResult:
        ...         # Implementation here
        ...         return AgentResult(success=True, data={})
    """
    
    def __init__(self, name: str, config: dict[str, Any] | None = None) -> None:
        """Initialize the agent.
        
        Args:
            name: Unique agent identifier
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self._initialized = False
    
    @abstractmethod
    async def process(self, input_data: dict[str, Any]) -> AgentResult:
        """Process input data and return result.
        
        This is the core method that all agents must implement.
        The LangGraph workflow will call this method to execute
        each agent in the sequence.
        
        Args:
            input_data: Dictionary containing input parameters
            
        Returns:
            AgentResult with success status and output data
            
        Raises:
            AgentException: If processing fails unrecoverably
        """
        ...
    
    async def validate(self, input_data: dict[str, Any]) -> bool:
        """Validate input data before processing.
        
        Override this method to add custom validation.
        
        Args:
            input_data: Input to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True
    
    def get_confidence(self, result: AgentResult) -> float:
        """Extract confidence score from result.
        
        Args:
            result: Agent execution result
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        return min(max(result.confidence, 0.0), 1.0)
