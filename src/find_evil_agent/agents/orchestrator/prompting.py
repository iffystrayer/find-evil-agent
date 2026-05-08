"""Prompting helpers for lead extraction in iterative investigation.

Extracted from orchestrator.py (C3c refactor).

Functions:
- build_lead_extraction_prompt: Create LLM prompt for extracting investigative leads
- parse_leads_from_response: Parse LLM response into InvestigativeLead objects
- extract_leads_fallback: Rule-based fallback when LLM extraction fails
"""

from typing import Any
import structlog

from ..schemas import InvestigativeLead, LeadType, LeadPriority

logger = structlog.get_logger()


def build_lead_extraction_prompt(
    findings: list[dict[str, Any]],
    iocs: dict[str, list[str]],
    iteration_number: int
) -> str:
    """Build LLM prompt for lead extraction.

    Args:
        findings: List of findings from current iteration
        iocs: IOCs extracted from current iteration
        iteration_number: Current iteration number

    Returns:
        Formatted prompt string for LLM
    """
    findings_text = "\n".join([
        f"- {f.get('description', 'N/A')} (Severity: {f.get('severity', 'unknown')})"
        for f in findings[:5]  # Limit to first 5
    ])

    iocs_text = "\n".join([
        f"- {ioc_type}: {', '.join(values[:3])}"  # First 3 of each type
        for ioc_type, values in iocs.items()
        if values
    ])

    return f"""You are a DFIR expert analyzing investigation findings. Based on the current findings and IOCs, identify the next investigative steps.

Current Findings:
{findings_text or "No findings yet"}

Current IOCs:
{iocs_text or "No IOCs yet"}

Iteration: {iteration_number}

Identify 1-3 investigative leads that would help build a complete attack chain. For each lead, provide:
1. Lead type (process/network/file/timeline/registry)
2. Clear description of what to investigate
3. Priority (high/medium/low)
4. Suggested tool (if applicable)
5. Confidence (0.0-1.0) that this lead is worth following

Focus on leads that would:
- Identify the initial infection vector
- Trace network communication (C2 servers)
- Identify malicious processes or files
- Build a timeline of events
- Uncover persistence mechanisms

Respond in this format (one lead per line):
LEAD: <type> | <priority> | <confidence> | <suggested_tool or none> | <description>

Example:
LEAD: network | high | 0.9 | bulk_extractor | Analyze network traffic to identify C2 server communication from suspicious process
"""


def parse_leads_from_response(
    response: str,
    findings: list[dict[str, Any]],
    iocs: dict[str, list[str]]
) -> list[InvestigativeLead]:
    """Parse LLM response into InvestigativeLead objects.

    Args:
        response: LLM response text containing LEAD: lines
        findings: Original findings for context building
        iocs: Original IOCs for context building

    Returns:
        List of parsed leads, sorted by priority and confidence
    """
    leads = []

    for line in response.split('\n'):
        if not line.strip().startswith('LEAD:'):
            continue

        try:
            # Parse: LEAD: <type> | <priority> | <confidence> | <tool> | <description>
            parts = line.replace('LEAD:', '').split('|')
            if len(parts) < 5:
                continue

            lead_type_str = parts[0].strip().lower()
            priority_str = parts[1].strip().lower()
            confidence = float(parts[2].strip())
            suggested_tool = parts[3].strip() if parts[3].strip() != 'none' else None
            description = parts[4].strip()

            # Map strings to enums
            lead_type = LeadType(lead_type_str) if lead_type_str in [t.value for t in LeadType] else LeadType.PROCESS
            priority = LeadPriority(priority_str) if priority_str in [p.value for p in LeadPriority] else LeadPriority.MEDIUM

            # Build context from IOCs
            context = {
                "findings_count": len(findings),
                "ioc_types": list(iocs.keys())
            }

            lead = InvestigativeLead(
                lead_type=lead_type,
                description=description,
                priority=priority,
                suggested_tool=suggested_tool,
                context=context,
                confidence=confidence,
                reasoning="LLM-generated lead based on current findings"
            )

            leads.append(lead)

        except Exception as e:
            logger.debug("failed_to_parse_lead", line=line, error=str(e))
            continue

    # Sort by priority and confidence
    leads.sort(key=lambda l: (
        0 if l.priority == LeadPriority.HIGH else 1 if l.priority == LeadPriority.MEDIUM else 2,
        -l.confidence
    ))

    return leads


def extract_leads_fallback(
    findings: list[dict[str, Any]],
    iocs: dict[str, list[str]]
) -> list[InvestigativeLead]:
    """Fallback rule-based lead extraction when LLM fails.

    Args:
        findings: List of findings from current iteration
        iocs: IOCs extracted from current iteration

    Returns:
        List of rule-based leads
    """
    leads = []

    # If we found processes, suggest network analysis
    if iocs.get("processes"):
        leads.append(InvestigativeLead(
            lead_type=LeadType.NETWORK,
            description="Analyze network activity for suspicious processes",
            priority=LeadPriority.HIGH,
            suggested_tool="bulk_extractor",
            context={"processes": iocs["processes"][:3]},
            confidence=0.75,
            reasoning="Processes found, network analysis is logical next step"
        ))

    # If we found IPs/domains, suggest timeline
    if iocs.get("ips") or iocs.get("domains"):
        leads.append(InvestigativeLead(
            lead_type=LeadType.TIMELINE,
            description="Build timeline to identify when IOCs first appeared",
            priority=LeadPriority.MEDIUM,
            suggested_tool="log2timeline",
            context={"iocs": {k: v for k, v in iocs.items() if v}},
            confidence=0.7,
            reasoning="IOCs found, timeline helps establish attack sequence"
        ))

    return leads
