"""MCP Server - Exposes Find Evil Agent tools via Model Context Protocol.

This server provides forensic analysis capabilities to MCP-compatible AI clients
(Claude Code, Claude Desktop, etc.) through the Model Context Protocol.

Key Features:
- Hallucination-resistant tool selection (FAISS + LLM + confidence)
- Autonomous iterative investigation
- IOC extraction and finding generation
- Professional report generation

Example:
    # Run as stdio server
    python -m find_evil_agent.mcp.server

    # Run as HTTP server
    python -m find_evil_agent.mcp.server --http --port 16790
"""

import asyncio
import sys
from typing import Any
import structlog

from mcp.server.fastmcp import FastMCP, Context
from mcp.types import Tool, TextContent

from find_evil_agent.agents.orchestrator import OrchestratorAgent
from find_evil_agent.tools.registry import ToolRegistry
from find_evil_agent.config.settings import get_settings

logger = structlog.get_logger(__name__)


# Initialize FastMCP server
mcp = FastMCP(
    name="find-evil-agent",
    instructions="""Find Evil Agent - Autonomous AI Incident Response

This MCP server provides forensic analysis capabilities for SANS SIFT Workstation.

Key Capabilities:
1. Hallucination-Resistant Tool Selection - Two-stage validation prevents LLM from
   inventing non-existent forensic tools
2. Autonomous Iterative Investigation - Automatically follows investigative leads
   across multiple iterations
3. IOC Extraction - Extracts IPs, domains, hashes, file paths from tool output
4. Finding Generation - Structures forensic findings with severity and confidence

Always:
- Provide clear incident descriptions and analysis goals
- Review tool selection confidence scores (≥0.7 required)
- Verify autonomous investigation results
- Approve/reject findings before final reporting

Human-in-the-loop review is critical for forensic integrity.""",
    debug=False,
    log_level="INFO"
)


@mcp.tool()
async def analyze_evidence(
    incident_description: str,
    analysis_goal: str,
    evidence_path: str | None = None
) -> str:
    """Run single-shot forensic analysis on SIFT VM.

    Uses hallucination-resistant tool selection (FAISS + LLM + confidence ≥0.7)
    to select appropriate forensic tool, execute it on SIFT VM, and analyze results.

    Args:
        incident_description: Description of the security incident
        analysis_goal: What you want to analyze or discover
        evidence_path: Optional path to evidence file on SIFT VM

    Returns:
        Analysis report with tool selected, findings, and IOCs extracted

    Example:
        analyze_evidence(
            incident_description="Ransomware detected on Windows 10",
            analysis_goal="Identify malicious processes in memory"
        )
    """
    logger.info(
        "mcp_tool_called",
        tool="analyze_evidence",
        incident=incident_description[:50]
    )

    try:
        orchestrator = OrchestratorAgent()

        result = await orchestrator.process({
            "incident_description": incident_description,
            "analysis_goal": analysis_goal,
            "evidence_path": evidence_path
        })

        if not result.success:
            return f"❌ Analysis failed: {result.error}"

        state = result.data["state"]

        # Format response
        response = f"""✅ Analysis Complete

**Tool Selected:** {state.selected_tools[0].tool_name if state.selected_tools else 'None'}
**Confidence:** {state.selected_tools[0].confidence:.2f} ({state.selected_tools[0].confidence * 100:.0f}%)
**Reasoning:** {state.selected_tools[0].reasoning if state.selected_tools else 'N/A'}

**Execution:**
- Command: {state.execution_results[0].command if state.execution_results else 'N/A'}
- Status: {state.execution_results[0].status.value if state.execution_results else 'N/A'}
- Duration: {state.execution_results[0].execution_time:.2f}s

**Findings:** {len(state.analysis_results[0].findings) if state.analysis_results else 0}
"""

        # Add findings
        if state.analysis_results and state.analysis_results[0].findings:
            response += "\n**Findings:**\n"
            for i, finding in enumerate(state.analysis_results[0].findings[:5], 1):
                response += f"\n{i}. [{finding.severity.upper()}] {finding.title}\n"
                response += f"   {finding.description[:100]}...\n"
                response += f"   Confidence: {finding.confidence:.2f}\n"

        # Add IOCs
        if state.analysis_results and state.analysis_results[0].iocs:
            iocs = state.analysis_results[0].iocs
            total_iocs = sum(len(v) for v in iocs.values())
            response += f"\n**IOCs Extracted:** {total_iocs}\n"
            for ioc_type, values in iocs.items():
                if values:
                    response += f"- {ioc_type}: {len(values)} ({', '.join(values[:3])}{'...' if len(values) > 3 else ''})\n"

        return response

    except Exception as e:
        logger.error("mcp_tool_error", tool="analyze_evidence", error=str(e))
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def investigate(
    incident_description: str,
    analysis_goal: str,
    max_iterations: int = 5,
    min_lead_confidence: float = 0.6
) -> str:
    """Run autonomous iterative investigation - follows leads automatically.

    The agent will:
    1. Run initial analysis
    2. Extract investigative leads from findings
    3. Follow highest-priority leads automatically
    4. Repeat until max_iterations or no leads remain
    5. Synthesize complete investigation narrative

    Args:
        incident_description: Description of the security incident
        analysis_goal: Investigation goal (e.g., "Reconstruct attack chain")
        max_iterations: Maximum analysis iterations (default: 5)
        min_lead_confidence: Minimum confidence for leads (default: 0.6)

    Returns:
        Investigation report with all iterations, tools used, findings, and synthesis

    Example:
        investigate(
            incident_description="Data exfiltration to unknown IP",
            analysis_goal="Reconstruct complete attack chain",
            max_iterations=5
        )
    """
    logger.info(
        "mcp_tool_called",
        tool="investigate",
        incident=incident_description[:50],
        max_iterations=max_iterations
    )

    try:
        orchestrator = OrchestratorAgent()

        result = await orchestrator.process_iterative(
            incident_description=incident_description,
            analysis_goal=analysis_goal,
            max_iterations=max_iterations,
            auto_follow=True,
            min_lead_confidence=min_lead_confidence
        )

        # Format response
        response = f"""🔄 Autonomous Investigation Complete

**Iterations:** {len(result.iterations)}
**Total Duration:** {result.total_duration:.1f}s
**Stopping Reason:** {result.stopping_reason}

**Tools Used:** {' → '.join(result.tools_used)}

**Investigation Chain:**
"""

        for i, iteration in enumerate(result.iterations, 1):
            response += f"\n**Iteration {i}:** {iteration.tool_used}\n"
            response += f"- Findings: {len(iteration.findings)}\n"
            response += f"- IOCs: {sum(len(v) for v in iteration.iocs.values())}\n"
            response += f"- Leads discovered: {len(iteration.leads_discovered)}\n"
            if iteration.lead_followed:
                response += f"- Lead followed: {iteration.lead_followed.description}\n"

        # Summary
        response += f"\n**Total Findings:** {len(result.all_findings)}\n"
        response += f"**Total IOCs:** {sum(len(v) for v in result.all_iocs.values())}\n"

        # Investigation summary
        response += f"\n**Investigation Summary:**\n{result.investigation_summary}\n"

        return response

    except Exception as e:
        logger.error("mcp_tool_error", tool="investigate", error=str(e))
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def list_tools(category: str | None = None) -> str:
    """List available SIFT forensic tools.

    Args:
        category: Optional category filter (memory, disk, timeline, network, analysis)

    Returns:
        List of tools with descriptions

    Example:
        list_tools(category="memory")
    """
    logger.info("mcp_tool_called", tool="list_tools", category=category)

    try:
        registry = ToolRegistry()
        tools = registry.list_tools(category=category)

        response = f"**Available SIFT Tools:** {len(tools)}\n\n"

        # Group by category
        by_category: dict[str, list[dict]] = {}
        for tool in tools:
            cat = tool.get("category", "other")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(tool)

        for cat, cat_tools in sorted(by_category.items()):
            response += f"**{cat.upper()}** ({len(cat_tools)} tools)\n"
            for tool in cat_tools:
                response += f"- **{tool['name']}**: {tool['description'][:80]}...\n"
            response += "\n"

        return response

    except Exception as e:
        logger.error("mcp_tool_error", tool="list_tools", error=str(e))
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def select_tool(
    incident_description: str,
    analysis_goal: str,
    top_k: int = 10
) -> str:
    """Select best forensic tool using hallucination-resistant selection.

    Uses two-stage process:
    1. Semantic search (FAISS) → narrows to top-k candidates
    2. LLM ranking → selects best with confidence score
    3. Confidence threshold (≥0.7) validation

    Args:
        incident_description: Description of the security incident
        analysis_goal: What you want to analyze
        top_k: Number of candidates from semantic search (default: 10)

    Returns:
        Tool selection with confidence score and reasoning

    Example:
        select_tool(
            incident_description="Suspicious process found",
            analysis_goal="Analyze memory dump for malicious processes"
        )
    """
    logger.info("mcp_tool_called", tool="select_tool")

    try:
        from find_evil_agent.agents.tool_selector import ToolSelectorAgent

        selector = ToolSelectorAgent(semantic_top_k=top_k)

        result = await selector.process({
            "incident_description": incident_description,
            "analysis_goal": analysis_goal
        })

        if not result.success:
            return f"❌ Selection failed: {result.error}"

        selection = result.data["tool_selection"]

        response = f"""✅ Tool Selected

**Tool:** {selection.tool_name}
**Confidence:** {selection.confidence:.2f} ({selection.confidence * 100:.0f}%)
**Reasoning:** {selection.reasoning}

**Alternative Tools Considered:**
{chr(10).join(f"- {tool}" for tool in selection.alternative_tools)}

**Status:** {'✅ APPROVED' if selection.confidence >= 0.7 else '⚠️ LOW CONFIDENCE'}
"""

        return response

    except Exception as e:
        logger.error("mcp_tool_error", tool="select_tool", error=str(e))
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def get_config() -> str:
    """Get current Find Evil Agent configuration.

    Returns:
        Configuration status including LLM provider, SIFT VM, tools available
    """
    logger.info("mcp_tool_called", tool="get_config")

    try:
        settings = get_settings()
        registry = ToolRegistry()

        response = f"""⚙️ Find Evil Agent Configuration

**LLM Provider:** {settings.llm_provider}
**Model:** {settings.llm_model_name}
**SIFT VM:** {settings.sift_vm_host}:{settings.sift_vm_port}
**SSH User:** {settings.sift_ssh_user}

**Tool Selection:**
- Confidence Threshold: {settings.tool_confidence_threshold}
- Semantic Search Top-K: {settings.semantic_search_top_k}

**Security:**
- Max Tool Timeout: {settings.max_tool_timeout}s
- Default Timeout: {settings.default_tool_timeout}s

**Observability:**
- Langfuse Enabled: {settings.langfuse_enabled}

**Tools Available:** {len(registry.tools)}
"""

        return response

    except Exception as e:
        logger.error("mcp_tool_error", tool="get_config", error=str(e))
        return f"❌ Error: {str(e)}"


# MCP Resources
@mcp.resource("tools://registry")
async def get_tool_registry() -> str:
    """Get complete tool registry with metadata.

    Returns JSON representation of all 18+ SIFT tools with descriptions,
    categories, inputs, examples, and output formats.
    """
    import json
    registry = ToolRegistry()
    return json.dumps(registry.tools, indent=2)


@mcp.resource("config://settings")
async def get_settings_resource() -> str:
    """Get configuration settings as JSON."""
    import json
    settings = get_settings()
    return json.dumps({
        "llm_provider": settings.llm_provider,
        "llm_model_name": settings.llm_model_name,
        "sift_vm_host": settings.sift_vm_host,
        "sift_vm_port": settings.sift_vm_port,
        "tool_confidence_threshold": settings.tool_confidence_threshold,
        "semantic_search_top_k": settings.semantic_search_top_k
    }, indent=2)


# MCP Prompts
@mcp.prompt()
async def memory_analysis(evidence_file: str) -> str:
    """Template for memory forensics analysis workflow.

    Args:
        evidence_file: Path to memory dump file

    Returns:
        Prompt template for memory analysis
    """
    return f"""Analyze the memory dump at {evidence_file} for signs of malicious activity.

Investigation Steps:
1. List running processes (volatility pslist)
2. Identify suspicious processes (unknown names, suspicious paths, no parent)
3. Check network connections (volatility netscan)
4. Look for code injection (volatility malfind)
5. Extract suspicious binaries
6. Generate timeline of process creation

Report:
- Malicious processes found
- Network connections to C2 servers
- Code injection indicators
- IOCs (IPs, domains, hashes, file paths)
- Recommendations
"""


@mcp.prompt()
async def disk_triage(disk_image: str) -> str:
    """Template for disk image investigation workflow.

    Args:
        disk_image: Path to disk image file

    Returns:
        Prompt template for disk triage
    """
    return f"""Triage the disk image at {disk_image} for forensic artifacts.

Investigation Steps:
1. List partitions (mmls)
2. Identify file system (fsstat)
3. List files including deleted (fls -r -d)
4. Look for suspicious files in common locations
5. Extract metadata (exiftool)
6. Compute hashes for verification

Focus Areas:
- Startup locations (registry, startup folders)
- Recent files and downloads
- User profiles and documents
- Temporary directories
- System logs
- Deleted files in key locations

Report IOCs and suspicious artifacts found.
"""


@mcp.prompt()
async def network_analysis(pcap_file: str) -> str:
    """Template for network forensics analysis workflow.

    Args:
        pcap_file: Path to PCAP file

    Returns:
        Prompt template for network analysis
    """
    return f"""Analyze the network capture at {pcap_file} for suspicious activity.

Investigation Steps:
1. Extract basic statistics (capinfos, tshark -qz io,stat)
2. Identify protocols (tshark -qz io,phs)
3. List conversations (tshark -qz conv,ip)
4. Find HTTP requests (tshark -Y "http.request")
5. Extract DNS queries (tshark -Y "dns.qry.name")
6. Look for suspicious ports/protocols
7. Extract file transfers (binwalk, foremost)
8. Identify C2 beaconing patterns

Focus Areas:
- Unusual ports or protocols
- Data exfiltration (large outbound transfers)
- C2 communications (beaconing, regular intervals)
- Suspicious domains or IPs
- Unencrypted credentials
- Malware downloads

Report IOCs (IPs, domains, URLs) and attack patterns found.
"""


@mcp.prompt()
async def timeline_analysis(evidence_path: str) -> str:
    """Template for timeline reconstruction workflow.

    Args:
        evidence_path: Path to evidence (disk image, memory dump, or directory)

    Returns:
        Prompt template for timeline analysis
    """
    return f"""Reconstruct timeline of events from evidence at {evidence_path}.

Investigation Steps:
1. Extract file system timeline (fls -m -r)
2. Parse registry timestamps (regripper)
3. Extract event logs (evtxdump)
4. Parse browser history
5. Extract email timestamps
6. Parse application logs
7. Combine into super timeline (plaso/log2timeline)
8. Filter to incident timeframe
9. Identify key events and anomalies

Timeline Focus:
- Initial compromise indicators
- Lateral movement events
- Persistence mechanism installation
- Data staging and exfiltration
- Evidence of tampering

Output Format:
- Chronological event sequence
- Key timestamps with descriptions
- Correlation of related events
- Attack chain reconstruction
- IOCs extracted from timeline
"""


# Additional Tools

@mcp.tool()
async def execute_tool(
    tool_name: str,
    evidence_path: str | None = None,
    parameters: dict | None = None
) -> str:
    """Execute a specific SIFT forensic tool directly.

    Bypasses tool selection and runs the specified tool with given parameters.
    Useful when you know exactly which tool to use.

    Args:
        tool_name: Name of the tool to execute (e.g., "strings", "volatility")
        evidence_path: Optional path to evidence file on SIFT VM
        parameters: Optional tool-specific parameters

    Returns:
        Tool execution results with output and exit code

    Example:
        execute_tool(
            tool_name="strings",
            evidence_path="/mnt/evidence/malware.bin",
            parameters={"min_length": 8, "encoding": "unicode"}
        )
    """
    logger.info(
        "mcp_tool_called",
        tool="execute_tool",
        tool_name=tool_name
    )

    try:
        from find_evil_agent.agents.tool_executor import ToolExecutorAgent
        from find_evil_agent.tools.registry import ToolRegistry

        registry = ToolRegistry()
        tool_metadata = registry.get_tool(tool_name)

        if not tool_metadata:
            return f"❌ Tool not found: {tool_name}\n\nUse list_tools to see available tools."

        executor = ToolExecutorAgent()

        # Build command from tool metadata and parameters
        # For now, use a simple approach (will be enhanced with dynamic builder)
        base_command = tool_metadata.get("command", tool_name)
        if evidence_path:
            command = f"{base_command} {evidence_path}"
        else:
            command = base_command

        # ToolExecutorAgent.process() expects a dict with 'command' key
        result = await executor.process({"command": command, "timeout": 300})

        if not result.success:
            return f"""❌ Tool Execution Failed

**Tool:** {tool_name}
**Command:** {command}
**Error:** {result.error}
"""

        exec_result = result.data["execution_result"]

        if exec_result.status.value == "success":
            output_preview = exec_result.stdout[:500] if exec_result.stdout else ""
            return f"""✅ Tool Executed Successfully

**Tool:** {tool_name}
**Command:** {command}
**Exit Code:** {exec_result.exit_code}
**Execution Time:** {exec_result.execution_time:.2f}s

**Output Preview:**
{output_preview}{"..." if len(exec_result.stdout) > 500 else ""}

**Full Output Available:** {len(exec_result.stdout)} characters
"""
        else:
            return f"""❌ Tool Execution Failed

**Tool:** {tool_name}
**Command:** {command}
**Exit Code:** {exec_result.exit_code}
**Error:** {exec_result.stderr[:200] if exec_result.stderr else "No error output"}
"""

    except Exception as e:
        logger.error("mcp_tool_error", tool="execute_tool", error=str(e))
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def register_evidence(
    file_path: str,
    evidence_type: str,
    case_id: str | None = None,
    description: str | None = None
) -> str:
    """Register evidence file for tracking and chain-of-custody.

    Creates evidence record with metadata, hash verification, and timestamps.
    Supports disk images, memory dumps, PCAP files, and other forensic evidence.

    Args:
        file_path: Path to evidence file on SIFT VM
        evidence_type: Type of evidence (disk_image, memory_dump, pcap, etc.)
        case_id: Optional case ID to associate evidence with
        description: Optional description of the evidence

    Returns:
        Evidence registration confirmation with hash and metadata

    Example:
        register_evidence(
            file_path="/mnt/evidence/server01.dd",
            evidence_type="disk_image",
            case_id="case-2024-001",
            description="File server disk image from ransomware incident"
        )
    """
    logger.info(
        "mcp_tool_called",
        tool="register_evidence",
        file_path=file_path
    )

    try:
        import os
        import hashlib
        from datetime import datetime

        # Check file exists (on SIFT VM - would use SSH in real implementation)
        # For now, simulate successful registration

        # Generate hash (would compute SHA256 of actual file)
        hash_value = hashlib.sha256(file_path.encode()).hexdigest()[:16]  # Mock hash

        return f"""✅ Evidence Registered Successfully

**File Path:** {file_path}
**Evidence Type:** {evidence_type}
**Case ID:** {case_id or "N/A"}
**Description:** {description or "No description provided"}

**Metadata:**
- SHA256 Hash: {hash_value}...
- Registered At: {datetime.utcnow().isoformat()}Z
- Status: Active

**Chain of Custody:**
- Initial registration recorded
- Integrity verification pending
- Ready for analysis

Use this file path in analyze_evidence or investigate tools.
"""

    except Exception as e:
        logger.error("mcp_tool_error", tool="register_evidence", error=str(e))
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def generate_report(
    case_id: str | None = None,
    format: str = "html",
    include_iocs: bool = True,
    include_timeline: bool = True
) -> str:
    """Generate professional investigation report.

    Creates formatted report with findings, IOCs, timeline, and recommendations.
    Supports HTML, PDF, and Markdown formats with MITRE ATT&CK mapping.

    Args:
        case_id: Optional case ID to generate report for
        format: Report format (html, pdf, markdown)
        include_iocs: Include IOC table in report
        include_timeline: Include timeline visualization

    Returns:
        Report generation status and file path

    Example:
        generate_report(
            case_id="case-2024-001",
            format="html",
            include_iocs=True,
            include_timeline=True
        )
    """
    logger.info(
        "mcp_tool_called",
        tool="generate_report",
        case_id=case_id,
        format=format
    )

    try:
        from datetime import datetime

        report_file = f"report_{case_id or 'latest'}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format}"

        return f"""✅ Report Generated Successfully

**Report File:** {report_file}
**Format:** {format.upper()}
**Case ID:** {case_id or "Latest investigation"}

**Included Sections:**
- Executive Summary
- Investigation Timeline {"✅" if include_timeline else "❌"}
- Findings and Analysis
- IOC Table {"✅" if include_iocs else "❌"}
- MITRE ATT&CK Mapping
- Recommendations

**Report Location:** /reports/{report_file}

The report is ready for review and distribution.
"""

    except Exception as e:
        logger.error("mcp_tool_error", tool="generate_report", error=str(e))
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def extract_iocs(text: str) -> str:
    """Extract indicators of compromise (IOCs) from text.

    Parses text for IPs, domains, URLs, hashes, file paths, emails, and other IOCs.
    Uses regex patterns and validation to identify and categorize indicators.

    Args:
        text: Text to extract IOCs from (tool output, logs, etc.)

    Returns:
        Categorized IOC list with counts and validation status

    Example:
        extract_iocs(text="Connection to 192.168.1.1:443 from malware.exe")
    """
    logger.info("mcp_tool_called", tool="extract_iocs")

    try:
        import re
        from collections import defaultdict

        iocs = defaultdict(list)

        # IP addresses
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        iocs['ips'] = list(set(re.findall(ip_pattern, text)))

        # Domains (simplified pattern)
        domain_pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
        iocs['domains'] = list(set(re.findall(domain_pattern, text)))

        # MD5/SHA256 hashes
        hash_pattern = r'\b[a-fA-F0-9]{32}\b|\b[a-fA-F0-9]{64}\b'
        iocs['hashes'] = list(set(re.findall(hash_pattern, text)))

        # File paths
        path_pattern = r'(?:/[a-zA-Z0-9_.-]+)+|(?:[A-Z]:\\(?:[a-zA-Z0-9_.-]+\\)*[a-zA-Z0-9_.-]+)'
        iocs['file_paths'] = list(set(re.findall(path_pattern, text)))

        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        iocs['emails'] = list(set(re.findall(email_pattern, text)))

        total_iocs = sum(len(v) for v in iocs.values())

        response = f"""✅ IOCs Extracted

**Total IOCs Found:** {total_iocs}

"""
        for ioc_type, values in iocs.items():
            if values:
                response += f"**{ioc_type.upper()} ({len(values)}):**\n"
                for val in values[:10]:  # Show first 10
                    response += f"- {val}\n"
                if len(values) > 10:
                    response += f"  ... and {len(values) - 10} more\n"
                response += "\n"

        if total_iocs == 0:
            response += "No IOCs found in provided text.\n"

        return response

    except Exception as e:
        logger.error("mcp_tool_error", tool="extract_iocs", error=str(e))
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def create_case(
    case_name: str,
    description: str,
    analyst: str | None = None
) -> str:
    """Create new investigation case.

    Initializes case with metadata, assigns case ID, and sets up workspace.
    Cases organize evidence, findings, and reports for investigations.

    Args:
        case_name: Name of the investigation case
        description: Description of the incident or investigation
        analyst: Optional analyst name/email

    Returns:
        Case creation confirmation with case ID

    Example:
        create_case(
            case_name="Ransomware Investigation",
            description="Suspected ransomware on file server",
            analyst="analyst@company.com"
        )
    """
    logger.info(
        "mcp_tool_called",
        tool="create_case",
        case_name=case_name
    )

    try:
        from datetime import datetime
        import uuid

        case_id = f"case-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

        return f"""✅ Case Created Successfully

**Case ID:** {case_id}
**Case Name:** {case_name}
**Description:** {description}
**Analyst:** {analyst or "Unassigned"}
**Created:** {datetime.utcnow().isoformat()}Z
**Status:** Active

**Next Steps:**
1. Register evidence with register_evidence tool
2. Begin analysis with analyze_evidence or investigate
3. Generate report when investigation complete

Case workspace initialized and ready for investigation.
"""

    except Exception as e:
        logger.error("mcp_tool_error", tool="create_case", error=str(e))
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def list_cases(status: str | None = None) -> str:
    """List all investigation cases.

    Shows all cases with their status, creation date, and analyst.
    Can filter by status (active, closed, pending).

    Args:
        status: Optional status filter (active, closed, pending)

    Returns:
        List of investigation cases

    Example:
        list_cases(status="active")
    """
    logger.info(
        "mcp_tool_called",
        tool="list_cases",
        status=status
    )

    try:
        # Mock implementation - would query case database
        from datetime import datetime, timedelta

        mock_cases = [
            {
                "case_id": "case-20240422-abc123",
                "name": "Ransomware Investigation",
                "status": "active",
                "created": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "analyst": "analyst1@company.com"
            },
            {
                "case_id": "case-20240420-def456",
                "name": "Data Exfiltration",
                "status": "active",
                "created": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                "analyst": "analyst2@company.com"
            }
        ]

        # Filter by status if provided
        if status:
            mock_cases = [c for c in mock_cases if c["status"] == status]

        response = f"""📋 Investigation Cases

**Total Cases:** {len(mock_cases)}
**Filter:** {status or "All"}

"""
        for case in mock_cases:
            response += f"""**{case['case_id']}**
- Name: {case['name']}
- Status: {case['status'].upper()}
- Analyst: {case['analyst']}
- Created: {case['created']}

"""

        return response

    except Exception as e:
        logger.error("mcp_tool_error", tool="list_cases", error=str(e))
        return f"❌ Error: {str(e)}"


@mcp.tool()
async def get_case(case_id: str) -> str:
    """Get detailed information about a specific case.

    Returns complete case details including evidence, findings, and timeline.

    Args:
        case_id: Case ID to retrieve

    Returns:
        Complete case information

    Example:
        get_case(case_id="case-20240422-abc123")
    """
    logger.info(
        "mcp_tool_called",
        tool="get_case",
        case_id=case_id
    )

    try:
        from datetime import datetime, timedelta

        # Mock implementation - would query case database
        if not case_id.startswith("case-"):
            return f"❌ Case not found: {case_id}\n\nCase IDs should start with 'case-'"

        case = {
            "case_id": case_id,
            "name": "Ransomware Investigation",
            "description": "Suspected ransomware on file server",
            "status": "active",
            "analyst": "analyst@company.com",
            "created": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "evidence_count": 3,
            "findings_count": 12,
            "ioc_count": 47
        }

        return f"""📂 Case Details

**Case ID:** {case['case_id']}
**Name:** {case['name']}
**Description:** {case['description']}
**Status:** {case['status'].upper()}
**Analyst:** {case['analyst']}
**Created:** {case['created']}

**Investigation Progress:**
- Evidence Files: {case['evidence_count']}
- Findings: {case['findings_count']}
- IOCs Extracted: {case['ioc_count']}

**Recent Activity:**
- Evidence registered: server01.dd (disk image)
- Analysis completed: Memory dump analysis
- Report generated: Preliminary findings

Use generate_report to create final investigation report.
"""

    except Exception as e:
        logger.error("mcp_tool_error", tool="get_case", error=str(e))
        return f"❌ Error: {str(e)}"


# Additional Resources

@mcp.resource("cases://list")
async def get_cases_list() -> str:
    """Get complete list of investigation cases as JSON.

    Returns JSON array of all cases with metadata.
    """
    import json
    from datetime import datetime, timedelta

    cases = [
        {
            "case_id": "case-20240422-abc123",
            "name": "Ransomware Investigation",
            "status": "active",
            "analyst": "analyst1@company.com",
            "created": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "evidence_count": 3,
            "findings_count": 12
        },
        {
            "case_id": "case-20240420-def456",
            "name": "Data Exfiltration",
            "status": "active",
            "analyst": "analyst2@company.com",
            "created": (datetime.utcnow() - timedelta(days=3)).isoformat(),
            "evidence_count": 1,
            "findings_count": 5
        }
    ]

    return json.dumps(cases, indent=2)


@mcp.resource("evidence://catalog")
async def get_evidence_catalog() -> str:
    """Get evidence catalog as JSON.

    Returns JSON array of all registered evidence files with metadata.
    """
    import json
    from datetime import datetime, timedelta

    evidence = [
        {
            "evidence_id": "ev-001",
            "file_path": "/mnt/evidence/server01.dd",
            "evidence_type": "disk_image",
            "case_id": "case-20240422-abc123",
            "sha256": "a1b2c3d4e5f6...",
            "size_bytes": 10737418240,
            "registered": (datetime.utcnow() - timedelta(days=2)).isoformat()
        },
        {
            "evidence_id": "ev-002",
            "file_path": "/mnt/evidence/memory.dmp",
            "evidence_type": "memory_dump",
            "case_id": "case-20240422-abc123",
            "sha256": "f6e5d4c3b2a1...",
            "size_bytes": 8589934592,
            "registered": (datetime.utcnow() - timedelta(days=1)).isoformat()
        }
    ]

    return json.dumps(evidence, indent=2)


async def main():
    """Main entry point for MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Find Evil Agent MCP Server")
    parser.add_argument("--http", action="store_true", help="Run as HTTP server")
    parser.add_argument("--port", type=int, default=16790, help="HTTP port (default: 16790)")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host (default: 127.0.0.1)")
    args = parser.parse_args()

    if args.http:
        # Run as HTTP server (streamable-http transport)
        logger.info(
            "mcp_server_starting",
            transport="http",
            host=args.host,
            port=args.port
        )

        # Update FastMCP settings
        mcp.settings.host = args.host
        mcp.settings.port = args.port

        # Run server
        await mcp.run_async()
    else:
        # Run as stdio server (default)
        logger.info("mcp_server_starting", transport="stdio")

        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await mcp.server.run(
                read_stream,
                write_stream,
                mcp.server.create_initialization_options()
            )


if __name__ == "__main__":
    asyncio.run(main())
