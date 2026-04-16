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
