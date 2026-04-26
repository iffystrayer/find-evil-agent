"""Tool Selector Agent - Intelligent SIFT tool selection.

This agent reduces LLM hallucination by:
1. Semantic search to narrow candidate tools (top-10)
2. LLM ranks with mandatory reasoning
3. Confidence threshold (≥0.7 required)
4. Registry validation before returning

This is the CRITICAL agent for hackathon success - the key differentiator
for minimizing hallucination in DFIR workflows.

Example:
    >>> agent = ToolSelectorAgent()
    >>> result = await agent.process({
    ...     "incident_description": "Suspicious process found",
    ...     "analysis_goal": "Find running processes in memory dump"
    ... })
    >>> selection = result.data['tool_selection']
    >>> selection.tool_name
    'volatility'
    >>> selection.confidence
    0.95
"""

from typing import Any

import structlog

from find_evil_agent.telemetry import log_agent_error
from find_evil_agent.tools.registry import ToolRegistry

from .base import AgentResult, AgentStatus, BaseAgent
from .schemas import ToolSelection

agent_logger = structlog.get_logger()


# System prompt for tool selection
TOOL_SELECTION_PROMPT = """You are a DFIR (Digital Forensics and Incident Response) expert selecting SIFT tools for forensic analysis.

Your task is to select the MOST APPROPRIATE tool from the provided candidates based on the incident description and analysis goal.

CRITICAL REQUIREMENTS:
1. Select EXACTLY ONE tool (the best match)
2. Provide detailed reasoning explaining WHY this tool is appropriate
3. Assign a confidence score (0.0-1.0) reflecting how certain you are
4. List alternative tools considered (if any)
5. Specify required inputs for the selected tool

CONFIDENCE SCORING GUIDE:
- 1.0: Perfect match, tool is specifically designed for this exact task
- 0.8-0.9: Very good match, tool can accomplish the task effectively
- 0.7-0.79: Good match, tool can work but may not be optimal
- 0.5-0.69: Uncertain, tool might work but unclear
- Below 0.5: Poor match, tool unlikely to help

IMPORTANT:
- If confidence is below 0.7, this indicates the tool selection is unreliable
- Only recommend tools you are confident will work for the given scenario
- Be honest about uncertainty - low confidence scores are valuable feedback"""


class ToolSelectorAgent(BaseAgent):
    """Selects appropriate SIFT tools with confidence scoring.

    This agent implements a two-stage process:
    1. **Semantic Search**: Narrow down to top-k candidate tools using embeddings
    2. **LLM Ranking**: Have LLM select best tool with confidence score + reasoning

    Key Features:
    - Hallucination resistance via semantic search (constrains LLM to real tools)
    - Mandatory confidence threshold (≥0.7 required)
    - Structured output (ToolSelection schema)
    - Registry validation
    - Detailed reasoning for transparency

    Attributes:
        registry: ToolRegistry for semantic search
        confidence_threshold: Minimum confidence to accept selection
        semantic_top_k: Number of candidates from semantic search
    """

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        confidence_threshold: float = 0.7,
        semantic_top_k: int = 10,
        **kwargs,
    ):
        """Initialize Tool Selector Agent.

        Args:
            registry: ToolRegistry instance (created if None)
            confidence_threshold: Minimum confidence to accept (default: 0.7)
            semantic_top_k: Number of candidates from semantic search (default: 10)
            **kwargs: Passed to BaseAgent
        """
        super().__init__(name="tool_selector", **kwargs)
        self.registry = registry or ToolRegistry()
        self.confidence_threshold = confidence_threshold
        self.semantic_top_k = semantic_top_k

    async def process(self, input_data: dict[str, Any]) -> AgentResult:
        """Select appropriate SIFT tool for the given incident.

        Args:
            input_data: Dict with keys:
                - incident_description: str (description of the incident)
                - analysis_goal: str (what needs to be analyzed)
                - evidence_type: str (optional: memory, disk, network, etc.)

        Returns:
            AgentResult with:
                - success: True if confidence threshold met
                - data: {"tool_selection": ToolSelection, "candidates": [...]}
                - confidence: LLM confidence score
                - error: Error message if failed

        Example:
            >>> result = await agent.process({
            ...     "incident_description": "Ransomware detected",
            ...     "analysis_goal": "Find malicious processes in memory"
            ... })
            >>> result.success
            True
            >>> result.data['tool_selection'].tool_name
            'volatility'
        """
        try:
            # Validate input
            if not await self.validate(input_data):
                return AgentResult(
                    success=False,
                    data={},
                    status=AgentStatus.FAILED,
                    error="Invalid input: incident_description and analysis_goal required",
                )

            incident_description = input_data["incident_description"]
            analysis_goal = input_data["analysis_goal"]
            evidence_type = input_data.get("evidence_type", "")

            agent_logger.info(
                "tool_selection_started",
                agent=self.name,
                incident=incident_description[:50],
                goal=analysis_goal[:50],
            )

            # Step 1: Semantic search for candidate tools
            query = f"{analysis_goal} {evidence_type}".strip()
            candidates = self.registry.search(query, top_k=self.semantic_top_k)

            agent_logger.debug(
                "semantic_search_completed",
                query=query,
                candidates_count=len(candidates),
                top_3=[c["tool"]["name"] for c in candidates[:3]],
            )

            # Step 2: Format candidates for LLM
            candidates_text = self._format_candidates(candidates)

            # Step 3: LLM selection with structured output
            messages = [
                {"role": "system", "content": TOOL_SELECTION_PROMPT},
                {
                    "role": "user",
                    "content": f"""INCIDENT: {incident_description}

ANALYSIS GOAL: {analysis_goal}

EVIDENCE TYPE: {evidence_type if evidence_type else "Not specified"}

CANDIDATE TOOLS:
{candidates_text}

Select the BEST tool for this scenario. Respond with your selection including tool name, confidence score, reasoning, and alternatives considered.""",
                },
            ]

            # Use LLM with structured output
            selection = await self.llm.chat_with_schema(
                messages=messages,
                schema=ToolSelection,
                temperature=0.1,  # Low temperature for deterministic selection
            )

            agent_logger.info(
                "llm_selection_completed",
                tool=selection.tool_name,
                confidence=selection.confidence,
                reason_length=len(selection.reason),
            )

            # Step 4: Validate confidence threshold
            if selection.confidence < self.confidence_threshold:
                log_agent_error(
                    agent_name=self.name,
                    error_type="confidence_threshold",
                    error_message=f"Tool selection confidence {selection.confidence:.2f} below threshold {self.confidence_threshold}",
                    tool=selection.tool_name,
                    confidence=selection.confidence,
                )

                return AgentResult(
                    success=False,
                    data={
                        "tool_selection": selection,
                        "candidates": candidates[:5],  # Include top 5 for debugging
                        "threshold": self.confidence_threshold,
                    },
                    confidence=selection.confidence,
                    status=AgentStatus.FAILED,
                    error=f"Tool selection confidence ({selection.confidence:.2f}) below threshold ({self.confidence_threshold}). Reason: {selection.reason}",
                )

            # Step 5: Validate tool exists in registry
            tool_meta = self.registry.get_tool(selection.tool_name)
            if tool_meta is None:
                log_agent_error(
                    agent_name=self.name,
                    error_type="tool_not_found",
                    error_message=f"LLM selected unknown tool: {selection.tool_name}",
                    tool=selection.tool_name,
                )

                return AgentResult(
                    success=False,
                    data={"tool_selection": selection, "candidates": candidates[:5]},
                    confidence=selection.confidence,
                    status=AgentStatus.FAILED,
                    error=f"Selected tool '{selection.tool_name}' not found in registry (possible hallucination)",
                )

            # Success!
            agent_logger.info(
                "tool_selection_success",
                tool=selection.tool_name,
                confidence=selection.confidence,
                category=tool_meta["category"],
            )

            return AgentResult(
                success=True,
                data={
                    "tool_selection": selection,
                    "tool_metadata": tool_meta,
                    "candidates": candidates[:5],  # Top 5 for context
                    "semantic_top_match": candidates[0]["tool"]["name"] if candidates else None,
                },
                confidence=selection.confidence,
                status=AgentStatus.SUCCESS,
            )

        except Exception as e:
            log_agent_error(
                agent_name=self.name, error_type="processing_error", error_message=str(e)
            )

            return AgentResult(
                success=False,
                data={},
                status=AgentStatus.FAILED,
                error=f"Tool selection failed: {e}",
            )

    async def validate(self, input_data: dict[str, Any]) -> bool:
        """Validate input data.

        Args:
            input_data: Input dict to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["incident_description", "analysis_goal"]
        for field in required_fields:
            if field not in input_data or not input_data[field]:
                return False
        return True

    def _format_candidates(self, candidates: list[dict[str, Any]]) -> str:
        """Format candidate tools for LLM prompt.

        Args:
            candidates: List of search results from registry

        Returns:
            Formatted string with candidate tools
        """
        lines = []
        for i, candidate in enumerate(candidates, 1):
            tool = candidate["tool"]
            similarity = candidate["similarity"]

            lines.append(f"{i}. {tool['name']} (similarity: {similarity:.3f})")
            lines.append(f"   Category: {tool['category']}")
            lines.append(f"   Description: {tool['description']}")

            # Include example usage if available
            if "examples" in tool and tool["examples"]:
                lines.append(f"   Example: {tool['examples'][0]}")

            lines.append("")  # Blank line between tools

        return "\n".join(lines)
