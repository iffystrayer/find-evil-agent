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
    """Save results to markdown file.

    Args:
        result: Analysis result dictionary
        output_path: Output file path
        console: Rich console
    """
    try:
        with open(output_path, "w") as f:
            f.write(f"# Find Evil Agent - Analysis Report\n\n")
            f.write(f"**Session ID:** {result['session_id']}\n\n")
            f.write(f"**Summary:** {result['summary']}\n\n")

            # Tools
            if result["tools_used"]:
                f.write("## Tools Used\n\n")
                for tool in result["tools_used"]:
                    f.write(f"- **{tool['tool_name']}** (confidence: {tool['confidence']:.2f})\n")
                    f.write(f"  - {tool['reason']}\n")
                f.write("\n")

            # Findings
            if result["findings"]:
                f.write(f"## Findings ({len(result['findings'])})\n\n")
                for i, finding in enumerate(result["findings"], 1):
                    f.write(f"### {i}. [{finding['severity'].upper()}] {finding['title']}\n\n")
                    f.write(f"{finding['description']}\n\n")
                    f.write(f"**Confidence:** {finding['confidence']:.2f}\n\n")
                    if finding.get("evidence"):
                        f.write(f"**Evidence:**\n")
                        for ev in finding["evidence"][:5]:
                            f.write(f"- `{ev}`\n")
                        f.write("\n")

            # IOCs
            if result["iocs"]:
                f.write("## Indicators of Compromise\n\n")
                for ioc in result["iocs"]:
                    f.write(f"### {ioc['type']}\n\n")
                    for value in ioc["values"][:20]:
                        f.write(f"- `{value}`\n")
                    f.write("\n")

            f.write(f"\n---\n")
            f.write(f"*Generated by Find Evil Agent v0.1.0*\n")

        console.print(f"[green]✓ Results saved to:[/green] {output_path}")

    except Exception as e:
        console.print(f"[red]✗ Failed to save results:[/red] {e}")


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
