"""Analyzer Agent - Tool output analysis and finding extraction.

This agent analyzes SIFT tool output and extracts forensic findings:
1. Extracts IOCs (IPs, domains, hashes, file paths)
2. Uses LLM to analyze unstructured output
3. Generates structured findings with severity and confidence
4. Tool-aware parsing strategies

Example:
    >>> agent = AnalyzerAgent()
    >>> result = await agent.process({
    ...     "execution_result": exec_result
    ... })
    >>> analysis = result.data['analysis_result']
    >>> analysis.findings
    [Finding(title="Suspicious Process", severity="high", ...)]
"""

import re
from typing import Any

import structlog
from pydantic import BaseModel, Field

from find_evil_agent.telemetry import log_agent_error

from .base import AgentResult, AgentStatus, BaseAgent
from .schemas import AnalysisResult, ExecutionResult, Finding, FindingSeverity

agent_logger = structlog.get_logger()


# IOC extraction patterns
IOC_PATTERNS = {
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "domain": re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b", re.IGNORECASE),
    "md5": re.compile(r"\b[a-fA-F0-9]{32}\b"),
    "sha1": re.compile(r"\b[a-fA-F0-9]{40}\b"),
    "sha256": re.compile(r"\b[a-fA-F0-9]{64}\b"),
    "file_path_unix": re.compile(r"(?:/[^/\s]+)+"),
    "file_path_windows": re.compile(r"[A-Z]:\\[^\s]+", re.IGNORECASE),
    "email": re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),
    "url": re.compile(r"https?://[^\s]+"),
}


# LLM prompt for analysis
ANALYSIS_PROMPT = """You are a DFIR (Digital Forensics and Incident Response) expert analyzing forensic tool output.

Your task is to analyze the tool output and generate structured findings about security incidents.

CRITICAL REQUIREMENTS:
1. Identify suspicious activities, malware indicators, and security issues
2. Assign appropriate severity levels (critical, high, medium, low, info)
3. Provide confidence scores (0.0-1.0) for each finding
4. Include specific evidence from the tool output
5. Be concise but thorough in descriptions

SEVERITY GUIDELINES:
- CRITICAL: Active malware, C2 communication, privilege escalation, data exfiltration
- HIGH: Suspicious processes, unknown network connections, persistence mechanisms
- MEDIUM: Unusual activity, suspicious files, configuration changes
- LOW: Minor anomalies, potential false positives
- INFO: Contextual information, baseline data

CONFIDENCE GUIDELINES:
- 1.0: Definitive evidence (known malware signatures, confirmed IOCs)
- 0.8-0.9: Strong indicators (suspicious patterns, anomalies)
- 0.6-0.7: Moderate confidence (unusual but not conclusive)
- 0.4-0.5: Weak indicators (may be legitimate)
- <0.4: Uncertain (requires further investigation)

Focus on actionable findings that would help incident responders."""


class AnalysisRequest(BaseModel):
    """Schema for LLM analysis request."""

    findings: list[Finding] = Field(
        description="List of forensic findings extracted from tool output"
    )


class AnalyzerAgent(BaseAgent):
    """Analyzes tool output and extracts forensic findings.

    Key Features:
    - IOC extraction (IPs, domains, hashes, file paths, emails, URLs)
    - LLM-based analysis for unstructured output
    - Tool-aware parsing strategies
    - Severity and confidence scoring
    - Structured Finding generation

    Attributes:
        ioc_patterns: Regex patterns for IOC extraction
        min_confidence: Minimum confidence threshold for findings
    """

    def __init__(self, min_confidence: float = 0.5, **kwargs):
        """Initialize Analyzer Agent.

        Args:
            min_confidence: Minimum confidence to include findings (default: 0.5)
            **kwargs: Passed to BaseAgent
        """
        super().__init__(name="analyzer", **kwargs)
        self.ioc_patterns = IOC_PATTERNS
        self.min_confidence = min_confidence

        agent_logger.info("analyzer_initialized", min_confidence=self.min_confidence)

    async def process(self, input_data: dict[str, Any]) -> AgentResult:
        """Analyze tool output and extract findings.

        Args:
            input_data: Dict with keys:
                - execution_result: ExecutionResult from ToolExecutorAgent

        Returns:
            AgentResult with:
                - success: True if analysis completed
                - data: {"analysis_result": AnalysisResult}
                - status: SUCCESS or FAILED

        Example:
            >>> exec_result = ExecutionResult(...)
            >>> result = await agent.process({"execution_result": exec_result})
            >>> analysis = result.data['analysis_result']
            >>> len(analysis.findings)
            3
        """
        try:
            # Validate input
            if not await self.validate(input_data):
                return AgentResult(
                    success=False,
                    data={},
                    status=AgentStatus.FAILED,
                    error="Invalid input: execution_result is required",
                )

            exec_result: ExecutionResult = input_data["execution_result"]

            agent_logger.info(
                "analysis_started",
                agent=self.name,
                tool=exec_result.tool_name,
                output_length=len(exec_result.stdout or ""),
            )

            # Handle empty or failed execution
            if not exec_result.stdout or len(exec_result.stdout.strip()) == 0:
                agent_logger.warning(
                    "empty_output", tool=exec_result.tool_name, status=exec_result.status.value
                )

                return AgentResult(
                    success=True,
                    data={
                        "analysis_result": AnalysisResult(
                            tool_name=exec_result.tool_name,
                            findings=[],
                            iocs={},
                            raw_output=exec_result.stdout or "",
                            parsed_output={},
                            analysis_summary="No output to analyze",
                        )
                    },
                    status=AgentStatus.SUCCESS,
                )

            # Step 1: Extract IOCs
            iocs = self._extract_iocs(exec_result.stdout)

            agent_logger.debug(
                "iocs_extracted",
                tool=exec_result.tool_name,
                ioc_counts={k: len(v) for k, v in iocs.items()},
            )

            # Step 2: Use LLM to analyze and generate findings
            findings = await self._analyze_with_llm(
                tool_name=exec_result.tool_name, output=exec_result.stdout, iocs=iocs
            )

            # Step 3: Filter findings by confidence threshold
            filtered_findings = [f for f in findings if f.confidence >= self.min_confidence]

            agent_logger.info(
                "analysis_completed",
                tool=exec_result.tool_name,
                findings_count=len(filtered_findings),
                ioc_types=list(iocs.keys()),
            )

            # Step 4: Generate analysis summary
            summary = self._generate_summary(
                tool_name=exec_result.tool_name, findings=filtered_findings, iocs=iocs
            )

            # Create AnalysisResult
            analysis_result = AnalysisResult(
                tool_name=exec_result.tool_name,
                findings=filtered_findings,
                iocs=iocs,
                raw_output=exec_result.stdout,
                parsed_output={"execution_time": exec_result.execution_time},
                analysis_summary=summary,
            )

            return AgentResult(
                success=True,
                data={"analysis_result": analysis_result},
                status=AgentStatus.SUCCESS,
                confidence=self._calculate_overall_confidence(filtered_findings),
            )

        except Exception as e:
            log_agent_error(agent_name=self.name, error_type="analysis_error", error_message=str(e))

            return AgentResult(
                success=False, data={}, status=AgentStatus.FAILED, error=f"Analysis failed: {e}"
            )

    async def validate(self, input_data: dict[str, Any]) -> bool:
        """Validate input data.

        Args:
            input_data: Input dict to validate

        Returns:
            True if valid, False otherwise
        """
        if "execution_result" not in input_data:
            return False

        exec_result = input_data["execution_result"]
        if not isinstance(exec_result, ExecutionResult):
            return False

        return True

    def _extract_iocs(self, text: str) -> dict[str, list[str]]:
        """Extract IOCs from text using regex patterns.

        Args:
            text: Text to extract IOCs from

        Returns:
            Dict mapping IOC type to list of extracted values
        """
        iocs: dict[str, list[str]] = {}

        # Extract each IOC type
        for ioc_type, pattern in self.ioc_patterns.items():
            matches = pattern.findall(text)
            if matches:
                # Deduplicate and filter
                unique_matches = list(set(matches))
                # Filter out common false positives
                filtered = self._filter_false_positives(ioc_type, unique_matches)
                if filtered:
                    iocs[ioc_type] = filtered

        return iocs

    def _filter_false_positives(self, ioc_type: str, values: list[str]) -> list[str]:
        """Filter common false positives from IOC extractions.

        Args:
            ioc_type: Type of IOC
            values: List of extracted values

        Returns:
            Filtered list
        """
        if ioc_type == "ipv4":
            # Filter out private IPs and invalid addresses
            filtered = []
            for ip in values:
                parts = ip.split(".")
                # Basic validation
                if len(parts) == 4:
                    try:
                        nums = [int(p) for p in parts]
                        if all(0 <= n <= 255 for n in nums):
                            filtered.append(ip)
                    except ValueError:
                        pass
            return filtered

        elif ioc_type == "domain":
            # Filter out common non-domain strings
            filtered = []
            for domain in values:
                # Skip very short domains or all-numeric
                if len(domain) > 4 and not domain.replace(".", "").isdigit():
                    # Skip common extensions that aren't domains
                    if not domain.endswith((".dll", ".exe", ".sys", ".bin")):
                        filtered.append(domain.lower())
            return filtered

        return values

    async def _analyze_with_llm(
        self, tool_name: str, output: str, iocs: dict[str, list[str]]
    ) -> list[Finding]:
        """Use LLM to analyze tool output and generate findings.

        Args:
            tool_name: Name of the tool
            output: Tool output text
            iocs: Extracted IOCs

        Returns:
            List of Finding objects
        """
        # Truncate output if too long (LLM context limits)
        max_output_length = 8000
        truncated_output = output[:max_output_length]
        if len(output) > max_output_length:
            truncated_output += "\n... (output truncated)"

        # Format IOCs for prompt
        ioc_summary = "\n".join(
            [f"{ioc_type.upper()}: {', '.join(values[:10])}" for ioc_type, values in iocs.items()]
        )

        # Build LLM prompt
        messages = [
            {"role": "system", "content": ANALYSIS_PROMPT},
            {
                "role": "user",
                "content": f"""TOOL: {tool_name}

EXTRACTED IOCs:
{ioc_summary if ioc_summary else "None"}

TOOL OUTPUT:
{truncated_output}

Analyze this output and generate findings. For each finding, provide:
- Title (brief, specific)
- Description (detailed explanation)
- Severity (critical, high, medium, low, info)
- Confidence (0.0-1.0)
- Evidence (specific lines or indicators from output)

Generate 0-5 findings based on the output. Focus on the most significant security-relevant findings.""",
            },
        ]

        try:
            # Use LLM with structured output
            response = await self.llm.chat_with_schema(
                messages=messages,
                schema=AnalysisRequest,
                temperature=0.2,  # Low temperature for consistent analysis
            )

            agent_logger.debug(
                "llm_analysis_completed", tool=tool_name, findings_generated=len(response.findings)
            )

            return response.findings

        except Exception as e:
            agent_logger.error("llm_analysis_failed", tool=tool_name, error=str(e))

            # Fallback: Generate basic findings from IOCs
            return self._generate_fallback_findings(tool_name, iocs, output)

    def _generate_fallback_findings(
        self, tool_name: str, iocs: dict[str, list[str]], output: str
    ) -> list[Finding]:
        """Generate basic findings from IOCs when LLM fails.

        Args:
            tool_name: Name of the tool
            iocs: Extracted IOCs
            output: Tool output

        Returns:
            List of Finding objects
        """
        findings = []

        # Generate finding for each IOC type
        for ioc_type, values in iocs.items():
            if len(values) > 0:
                finding = Finding(
                    title=f"{ioc_type.upper()} Indicators Found",
                    description=f"Extracted {len(values)} {ioc_type} indicator(s) from {tool_name} output: {', '.join(values[:5])}",
                    severity=FindingSeverity.INFO,
                    confidence=0.6,
                    evidence=values[:10],
                    tool_references=[tool_name],
                )
                findings.append(finding)

        return findings

    def _generate_summary(
        self, tool_name: str, findings: list[Finding], iocs: dict[str, list[str]]
    ) -> str:
        """Generate analysis summary.

        Args:
            tool_name: Name of the tool
            findings: List of findings
            iocs: Extracted IOCs

        Returns:
            Summary string
        """
        if not findings and not iocs:
            return f"No significant findings from {tool_name}"

        parts = []

        if findings:
            severity_counts = {}
            for finding in findings:
                sev = finding.severity.value
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

            severity_str = ", ".join(
                [f"{count} {severity}" for severity, count in sorted(severity_counts.items())]
            )
            parts.append(f"{len(findings)} finding(s): {severity_str}")

        if iocs:
            ioc_str = ", ".join([f"{len(values)} {ioc_type}" for ioc_type, values in iocs.items()])
            parts.append(f"IOCs: {ioc_str}")

        return f"{tool_name} analysis: " + "; ".join(parts)

    def _calculate_overall_confidence(self, findings: list[Finding]) -> float:
        """Calculate overall confidence from findings.

        Args:
            findings: List of findings

        Returns:
            Average confidence score
        """
        if not findings:
            return 0.5

        return sum(f.confidence for f in findings) / len(findings)
