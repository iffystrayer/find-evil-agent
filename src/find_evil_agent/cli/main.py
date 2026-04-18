"""Find Evil Agent - CLI Interface.

Main entry point for the Find Evil Agent incident response tool.
Provides interactive and non-interactive modes for forensic analysis.

Usage:
    find-evil analyze "Ransomware detected" "Find malicious processes"
    find-evil --help
"""

import asyncio
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

from find_evil_agent.agents.orchestrator import OrchestratorAgent
from find_evil_agent.agents.reporter import ReporterAgent
from find_evil_agent.agents.report_schemas import ReportFormat
from find_evil_agent.agents.schemas import (
    Finding, FindingSeverity, AnalysisResult, IterativeAnalysisResult,
    IterationResult, InvestigativeLead, LeadType, LeadPriority, ToolSelection
)
from find_evil_agent.config.settings import get_settings

app = typer.Typer(
    name="find-evil",
    help="Find Evil Agent - Autonomous AI incident response for SANS SIFT Workstation",
    add_completion=False
)

console = Console()


@app.command()
def analyze(
    incident_description: str = typer.Argument(
        ...,
        help="Description of the security incident"
    ),
    analysis_goal: str = typer.Argument(
        ...,
        help="What you want to analyze or discover"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for results (markdown format)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
):
    """Analyze a security incident using SIFT tools.

    Examples:
        find-evil analyze "Ransomware detected on Windows 10" "Find malicious processes in memory"
        find-evil analyze "Suspicious network traffic" "Identify C2 communication" -o report.md
    """
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Find Evil Agent[/bold cyan]\n"
        "[dim]Autonomous AI Incident Response[/dim]",
        border_style="cyan"
    ))
    console.print()

    # Display input
    console.print(f"[yellow]Incident:[/yellow] {incident_description}")
    console.print(f"[yellow]Goal:[/yellow] {analysis_goal}")
    console.print()

    # Run analysis
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing incident...", total=None)

        try:
            # Run workflow
            result = asyncio.run(_run_analysis(incident_description, analysis_goal, verbose))

            progress.update(task, completed=True)

            if result["success"]:
                _display_results(result, console)

                # Save to file if requested
                if output:
                    _save_results(result, output, console)

            else:
                console.print(f"\n[red]✗ Analysis failed:[/red] {result['error']}")
                raise typer.Exit(code=1)

        except Exception as e:
            progress.stop()
            console.print(f"\n[red]✗ Error:[/red] {str(e)}")
            if verbose:
                console.print_exception()
            raise typer.Exit(code=1)


@app.command()
def investigate(
    incident_description: str = typer.Argument(
        ...,
        help="Description of the security incident"
    ),
    analysis_goal: str = typer.Argument(
        ...,
        help="Investigation goal (e.g., 'Reconstruct complete attack chain')"
    ),
    max_iterations: int = typer.Option(
        5,
        "--max-iterations",
        "-n",
        help="Maximum number of analysis iterations"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for investigation report (markdown format)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
):
    """Autonomous iterative investigation - follows leads automatically.

    Unlike 'analyze' which runs once, 'investigate' automatically follows
    investigative leads to build a complete attack chain. The agent will:

    1. Run initial analysis
    2. Extract investigative leads from findings
    3. Automatically follow highest-priority leads
    4. Repeat until max iterations or no leads remain
    5. Synthesize complete investigation narrative

    Examples:
        find-evil investigate "Ransomware detected" "Reconstruct complete attack chain" -n 5 -o investigation.md
        find-evil investigate "Data exfiltration" "Trace from network to file access" -v
    """
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Find Evil Agent - Autonomous Investigation[/bold cyan]\n"
        "[dim]Automatically follows investigative leads[/dim]",
        border_style="cyan"
    ))
    console.print()

    # Display input
    console.print(f"[yellow]Incident:[/yellow] {incident_description}")
    console.print(f"[yellow]Goal:[/yellow] {analysis_goal}")
    console.print(f"[yellow]Max Iterations:[/yellow] {max_iterations}")
    console.print()

    # Run investigation
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Starting investigation...", total=None)

        try:
            # Run iterative workflow
            result = asyncio.run(_run_investigation(
                incident_description,
                analysis_goal,
                max_iterations,
                verbose
            ))

            progress.update(task, completed=True)

            if result["success"]:
                _display_investigation_results(result, console)

                # Save to file if requested
                if output:
                    _save_investigation_results(result, output, console)

            else:
                console.print(f"\n[red]✗ Investigation failed:[/red] {result['error']}")
                raise typer.Exit(code=1)

        except Exception as e:
            progress.stop()
            console.print(f"\n[red]✗ Error:[/red] {str(e)}")
            if verbose:
                console.print_exception()
            raise typer.Exit(code=1)


@app.command()
def version():
    """Show version information."""
    console.print("[cyan]Find Evil Agent[/cyan] v0.1.0")
    console.print("Hackathon: FIND EVIL! (April 15 - June 15, 2026)")
    console.print("Built with: LangGraph, Ollama, SIFT Workstation")


@app.command()
def config():
    """Show current configuration."""
    settings = get_settings()

    table = Table(title="Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="yellow")
    table.add_column("Value", style="green")

    table.add_row("LLM Provider", settings.llm_provider.value)
    table.add_row("LLM Model", settings.llm_model_name)
    table.add_row("SIFT VM Host", settings.sift_vm_host)
    table.add_row("SIFT VM Port", str(settings.sift_vm_port))
    table.add_row("SIFT SSH User", settings.sift_ssh_user or "Not configured")

    if settings.llm_provider.value == "ollama":
        table.add_row("Ollama URL", settings.ollama_base_url)

    table.add_row("Langfuse Enabled", "Yes" if settings.langfuse_enabled else "No")

    console.print()
    console.print(table)
    console.print()


@app.command()
def web(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Host to bind to"
    ),
    port: int = typer.Option(
        17000,
        "--port",
        "-p",
        help="Port to run on (5-digit required)"
    ),
    share: bool = typer.Option(
        False,
        "--share",
        help="Create a public share link"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode"
    )
):
    """Launch the Gradio web interface.

    Provides an accessible web UI with three tabs:
    - Single Analysis: One-shot incident analysis
    - Investigative Mode: Multi-iteration autonomous investigation
    - About: Project information and features

    Example:
        find-evil web
        find-evil web --port 17000 --share
    """
    try:
        from find_evil_agent.web.gradio_app import launch_app

        console.print(Panel.fit(
            "[bold cyan]🌐 Find Evil Agent - Web Interface[/bold cyan]\n\n"
            f"[green]Starting server at:[/green] http://{host}:{port}\n"
            f"[dim]Press Ctrl+C to stop[/dim]",
            title="Web UI",
            border_style="cyan"
        ))

        launch_app(
            server_name=host,
            server_port=port,
            share=share,
            debug=debug
        )

    except ImportError as e:
        console.print(f"[red]✗ Failed to import Gradio:[/red] {e}")
        console.print("[yellow]Install Gradio with:[/yellow] uv pip install gradio")
    except Exception as e:
        console.print(f"[red]✗ Failed to launch web interface:[/red] {e}")
        if debug:
            console.print_exception()


async def _run_analysis(
    incident_description: str,
    analysis_goal: str,
    verbose: bool = False
) -> dict:
    """Run the analysis workflow.

    Args:
        incident_description: Description of incident
        analysis_goal: Analysis goal
        verbose: Enable verbose logging

    Returns:
        Result dictionary
    """
    try:
        # Create orchestrator
        orchestrator = OrchestratorAgent()

        # Run workflow
        result = await orchestrator.process({
            "incident_description": incident_description,
            "analysis_goal": analysis_goal
        })

        # Format results
        if result.success:
            state = result.data["state"]
            summary = result.data["summary"]

            return {
                "success": True,
                "session_id": state.session_id,
                "incident_description": incident_description,
                "analysis_goal": analysis_goal,
                "summary": summary,
                "tools_used": [t.model_dump() for t in state.selected_tools],
                "findings": state.findings,
                "iocs": state.iocs,
                "step_count": state.step_count,
                "confidence": result.confidence
            }
        else:
            return {
                "success": False,
                "error": result.error
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def _run_investigation(
    incident_description: str,
    analysis_goal: str,
    max_iterations: int = 5,
    verbose: bool = False
) -> dict:
    """Run the iterative investigation workflow.

    Args:
        incident_description: Description of incident
        analysis_goal: Investigation goal
        max_iterations: Maximum iterations
        verbose: Enable verbose logging

    Returns:
        Result dictionary
    """
    try:
        # Create orchestrator
        orchestrator = OrchestratorAgent()

        # Run iterative workflow
        result = await orchestrator.process_iterative(
            incident_description=incident_description,
            analysis_goal=analysis_goal,
            max_iterations=max_iterations,
            auto_follow=True
        )

        # Format results
        return {
            "success": True,
            "session_id": result.session_id,
            "incident_description": incident_description,
            "analysis_goal": analysis_goal,
            "iterations": [
                {
                    "number": it.iteration_number,
                    "tool": it.tool_used,
                    "findings_count": len(it.findings),
                    "iocs_count": sum(len(v) for v in it.iocs.values()),
                    "leads_count": len(it.leads_discovered),
                    "duration": it.duration,
                    "lead_followed": it.lead_followed.description if it.lead_followed else None
                }
                for it in result.iterations
            ],
            "investigation_chain": [
                {
                    "type": lead.lead_type.value,
                    "description": lead.description,
                    "priority": lead.priority.value,
                    "confidence": lead.confidence
                }
                for lead in result.investigation_chain if lead
            ],
            "all_findings": [f.model_dump() for f in result.all_findings],
            "all_iocs": result.all_iocs,
            "total_duration": result.total_duration,
            "stopping_reason": result.stopping_reason,
            "summary": result.investigation_summary
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _display_results(result: dict, console: Console):
    """Display analysis results.

    Args:
        result: Analysis result dictionary
        console: Rich console
    """
    console.print("\n[bold green]✓ Analysis Complete[/bold green]\n")

    # Summary
    console.print(f"[dim]{result['summary']}[/dim]")
    console.print()

    # Tools Used
    if result["tools_used"]:
        console.print("[bold cyan]Tools Used:[/bold cyan]")
        for tool in result["tools_used"]:
            confidence_color = "green" if tool["confidence"] >= 0.8 else "yellow"
            console.print(f"  • {tool['tool_name']} ([{confidence_color}]{tool['confidence']:.2f}[/{confidence_color}])")
            console.print(f"    {tool['reason'][:100]}...")
        console.print()

    # Findings
    if result["findings"]:
        console.print(f"[bold yellow]Findings ({len(result['findings'])}):[/bold yellow]")

        for i, finding in enumerate(result["findings"][:5], 1):  # Show top 5
            severity = finding["severity"]
            severity_colors = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "dim",
                "info": "dim"
            }
            color = severity_colors.get(severity, "white")

            console.print(f"\n  [{color}]{i}. [{severity.upper()}] {finding['title']}[/{color}]")
            console.print(f"     {finding['description'][:150]}...")
            console.print(f"     Confidence: {finding['confidence']:.2f}")

        if len(result["findings"]) > 5:
            console.print(f"\n  [dim]... and {len(result['findings']) - 5} more findings[/dim]")

        console.print()

    # IOCs
    if result["iocs"]:
        console.print(f"[bold magenta]Indicators of Compromise:[/bold magenta]")

        ioc_counts = {}
        for ioc in result["iocs"]:
            ioc_type = ioc["type"]
            count = len(ioc["values"])
            ioc_counts[ioc_type] = ioc_counts.get(ioc_type, 0) + count

        for ioc_type, count in ioc_counts.items():
            console.print(f"  • {ioc_type}: {count}")

        console.print()

    # Overall confidence
    confidence = result["confidence"]
    conf_color = "green" if confidence >= 0.7 else "yellow" if confidence >= 0.5 else "red"
    console.print(f"[bold]Overall Confidence:[/bold] [{conf_color}]{confidence:.2f}[/{conf_color}]")
    console.print()


def _save_results(result: dict, output_path: Path, console: Console):
    """Save results using professional ReporterAgent.

    Args:
        result: Analysis result dictionary
        output_path: Output file path
        console: Rich console
    """
    try:
        # Reconstruct Finding objects from dicts
        findings = [
            Finding(
                title=f.get("title", "Unknown"),
                description=f.get("description", ""),
                severity=FindingSeverity(f.get("severity", "info")),
                confidence=f.get("confidence", 0.5),
                evidence=f.get("evidence", []),
                tool_references=f.get("tool_references", [])
            )
            for f in result.get("findings", [])
        ]

        # Reconstruct IOCs dict (already in correct format)
        iocs = {}
        for ioc in result.get("iocs", []):
            ioc_type = ioc.get("type", "unknown")
            values = ioc.get("values", [])
            if ioc_type not in iocs:
                iocs[ioc_type] = []
            iocs[ioc_type].extend(values)

        # Get tool name from first tool used
        tool_name = "unknown"
        if result.get("tools_used"):
            tool_name = result["tools_used"][0].get("tool_name", "unknown")

        # Create AnalysisResult object
        analysis_result = AnalysisResult(
            tool_name=tool_name,
            findings=findings,
            iocs=iocs,
            raw_output=result.get("summary", ""),
            analysis_summary=result.get("summary", "")
        )

        # Determine format from file extension
        format_map = {
            ".md": ReportFormat.MARKDOWN,
            ".html": ReportFormat.HTML,
            ".pdf": ReportFormat.PDF
        }
        report_format = format_map.get(output_path.suffix.lower(), ReportFormat.MARKDOWN)

        # Generate professional report
        reporter = ReporterAgent()
        report = asyncio.run(reporter.generate_report(
            analysis_result=analysis_result,
            format=report_format,
            session_id=result.get("session_id", "unknown"),
            incident_description=result.get("incident_description", ""),
            analysis_goal=result.get("analysis_goal", ""),
            output_path=output_path if report_format == ReportFormat.PDF else None
        ))

        # Write report (unless PDF which writes itself)
        if report_format != ReportFormat.PDF:
            with open(output_path, "w") as f:
                f.write(report)

        console.print(f"[green]✓ Professional report saved to:[/green] {output_path}")
        console.print(f"[dim]Format: {report_format.value}, MITRE ATT&CK mapping included[/dim]")

    except Exception as e:
        console.print(f"[red]✗ Failed to generate report:[/red] {e}")
        if console._force_terminal:  # verbose mode
            console.print_exception()


def _display_investigation_results(result: dict, console: Console):
    """Display iterative investigation results.

    Args:
        result: Investigation result dictionary
        console: Rich console
    """
    console.print("\n[bold green]✓ Investigation Complete[/bold green]\n")

    # Summary
    console.print(f"[dim]{result['summary']}[/dim]")
    console.print()

    # Investigation Chain
    if result["investigation_chain"]:
        console.print("[bold cyan]Investigation Chain:[/bold cyan]")
        for i, lead in enumerate(result["investigation_chain"], 1):
            priority_color = "red" if lead["priority"] == "high" else "yellow" if lead["priority"] == "medium" else "dim"
            console.print(f"  {i}. [{priority_color}]{lead['type']}[/{priority_color}]: {lead['description'][:80]}...")
            console.print(f"     [dim]Confidence: {lead['confidence']:.2f}[/dim]")
        console.print()

    # Iterations Summary
    console.print(f"[bold yellow]Iterations ({len(result['iterations'])}):[/bold yellow]")
    for iteration in result["iterations"]:
        console.print(f"\n  Iteration {iteration['number']}: {iteration['tool']}")
        console.print(f"    Findings: {iteration['findings_count']}, IOCs: {iteration['iocs_count']}, Leads: {iteration['leads_count']}")
        console.print(f"    Duration: {iteration['duration']:.1f}s")
        if iteration.get("lead_followed"):
            console.print(f"    [dim]→ Followed: {iteration['lead_followed'][:60]}...[/dim]")
    console.print()

    # All Findings Summary
    if result["all_findings"]:
        console.print(f"[bold magenta]Total Findings: {len(result['all_findings'])}[/bold magenta]")

        severity_counts = {}
        for finding in result["all_findings"]:
            sev = finding["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        for severity in ["critical", "high", "medium", "low", "info"]:
            if severity in severity_counts:
                color = {"critical": "red", "high": "yellow", "medium": "blue", "low": "dim", "info": "dim"}[severity]
                console.print(f"  [{color}]{severity.upper()}: {severity_counts[severity]}[/{color}]")
        console.print()

    # All IOCs Summary
    if result["all_iocs"]:
        console.print(f"[bold cyan]Total IOCs:[/bold cyan]")
        for ioc_type, values in result["all_iocs"].items():
            console.print(f"  • {ioc_type}: {len(values)}")
        console.print()

    # Duration & Stopping Reason
    console.print(f"[bold]Total Duration:[/bold] {result['total_duration']:.1f}s")
    console.print(f"[bold]Stopped:[/bold] {result['stopping_reason']}")
    console.print()


def _save_investigation_results(result: dict, output_path: Path, console: Console):
    """Save investigation results using professional ReporterAgent.

    Args:
        result: Investigation result dictionary
        output_path: Output file path
        console: Rich console
    """
    try:
        # Reconstruct Finding objects from all_findings
        all_findings = [
            Finding(
                title=f.get("title", "Unknown"),
                description=f.get("description", ""),
                severity=FindingSeverity(f.get("severity", "info")),
                confidence=f.get("confidence", 0.5),
                evidence=f.get("evidence", []),
                tool_references=f.get("tool_references", [])
            )
            for f in result.get("all_findings", [])
        ]

        # Reconstruct investigation chain
        investigation_chain = []
        for lead_data in result.get("investigation_chain", []):
            if lead_data:  # Can be None
                investigation_chain.append(InvestigativeLead(
                    lead_type=LeadType(lead_data.get("type", "process")),
                    description=lead_data.get("description", ""),
                    priority=LeadPriority(lead_data.get("priority", "medium")),
                    confidence=lead_data.get("confidence", 0.7)
                ))
            else:
                investigation_chain.append(None)

        # Reconstruct iterations (simplified - reporter doesn't use full iteration details)
        iterations = []
        for it in result.get("iterations", []):
            iterations.append(IterationResult(
                iteration_number=it.get("number", 1),
                tool_used=it.get("tool", "unknown"),
                findings=[],  # Already in all_findings
                iocs={},  # Already in all_iocs
                duration=it.get("duration", 0.0)
            ))

        # Create IterativeAnalysisResult object
        iterative_result = IterativeAnalysisResult(
            session_id=result.get("session_id", "unknown"),
            incident_description=result.get("incident_description", ""),
            analysis_goal=result.get("analysis_goal", ""),
            iterations=iterations,
            investigation_chain=investigation_chain,
            all_findings=all_findings,
            all_iocs=result.get("all_iocs", {}),
            total_duration=result.get("total_duration", 0.0),
            stopping_reason=result.get("stopping_reason", ""),
            investigation_summary=result.get("summary", "")
        )

        # Determine format from file extension
        format_map = {
            ".md": ReportFormat.MARKDOWN,
            ".html": ReportFormat.HTML,
            ".pdf": ReportFormat.PDF
        }
        report_format = format_map.get(output_path.suffix.lower(), ReportFormat.MARKDOWN)

        # Generate professional report
        reporter = ReporterAgent()
        report = asyncio.run(reporter.generate_report(
            iterative_result=iterative_result,
            format=report_format,
            session_id=result.get("session_id", "unknown"),
            incident_description=result.get("incident_description", ""),
            analysis_goal=result.get("analysis_goal", ""),
            output_path=output_path if report_format == ReportFormat.PDF else None
        ))

        # Write report (unless PDF which writes itself)
        if report_format != ReportFormat.PDF:
            with open(output_path, "w") as f:
                f.write(report)

        console.print(f"[green]✓ Professional investigation report saved to:[/green] {output_path}")
        console.print(f"[dim]Format: {report_format.value}, MITRE ATT&CK mapping included, {len(result['iterations'])} iterations analyzed[/dim]")

    except Exception as e:
        console.print(f"[red]✗ Failed to generate investigation report:[/red] {e}")
        if console._force_terminal:  # verbose mode
            console.print_exception()


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
