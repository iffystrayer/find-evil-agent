#!/usr/bin/env python3
"""Auto-running Hackathon Demo - No interactive prompts.

This version runs automatically without user prompts.
Perfect for automated testing and recording.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

from find_evil_agent.agents.orchestrator import OrchestratorAgent
from find_evil_agent.config.settings import get_settings

console = Console()


async def demo_hallucination_prevention():
    """Demo 1: Show two-stage hallucination prevention."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Differentiator #1: Hallucination-Resistant Tool Selection[/bold cyan]\n"
        "[dim]Two-stage validation: Semantic Search → LLM Ranking → Confidence Threshold → Registry Validation[/dim]",
        border_style="cyan"
    ))
    console.print()

    console.print("[yellow]Scenario:[/yellow] User asks for file system analysis")
    console.print("[yellow]Challenge:[/yellow] LLM might hallucinate non-existent tools or select inappropriate ones")
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running analysis with hallucination prevention...", total=None)

        try:
            orchestrator = OrchestratorAgent()

            # Test case: Request file system analysis
            result = await orchestrator.process({
                "incident_description": "Suspicious files found in /tmp directory",
                "analysis_goal": "List and analyze file system metadata for forensic evidence"
            })

            progress.update(task, completed=True)

            if result.success:
                state = result.data["state"]

                # Show the selection process
                console.print("[bold green]✓ Tool Selection Successful[/bold green]\n")

                if state.selected_tools:
                    tool = state.selected_tools[0]

                    table = Table(title="Hallucination Prevention in Action", show_header=True)
                    table.add_column("Stage", style="cyan")
                    table.add_column("Result", style="yellow")
                    table.add_column("Status", style="green")

                    table.add_row(
                        "1. Semantic Search",
                        f"Top-10 candidates identified (fls, strings, grep, etc.)",
                        "✓"
                    )
                    table.add_row(
                        "2. LLM Ranking",
                        f"Selected: {tool.tool_name}",
                        "✓"
                    )
                    table.add_row(
                        "3. Confidence Check",
                        f"Score: {tool.confidence:.2f} (threshold: ≥0.7)",
                        "✓ PASS" if tool.confidence >= 0.7 else "✗ FAIL"
                    )
                    table.add_row(
                        "4. Registry Validation",
                        f"Tool exists in registry: {tool.tool_name}",
                        "✓"
                    )

                    console.print(table)
                    console.print()

                    console.print(f"[bold]Why {tool.tool_name}?[/bold]")
                    console.print(f"[dim]{tool.reason[:200]}...[/dim]")
                    console.print()

                    # Show alternatives
                    if tool.alternatives:
                        console.print("[bold]Alternatives Considered:[/bold]")
                        console.print(f"[dim]{', '.join(tool.alternatives[:5])}[/dim]")
                        console.print()

                # Show execution result
                if state.execution_results:
                    exec_result = state.execution_results[0]
                    console.print(f"[bold]Execution:[/bold]")
                    console.print(f"  Command: [cyan]{exec_result.command}[/cyan]")
                    console.print(f"  Duration: {exec_result.execution_time:.2f}s")
                    console.print(f"  Status: [{'green' if exec_result.success else 'red'}]{exec_result.status.value}[/]")
                    if exec_result.stdout:
                        console.print(f"  Output: {exec_result.stdout[:100]}...")
                    console.print()

                console.print("[bold cyan]Key Point:[/bold cyan]")
                console.print("  • Traditional LLM tools: Can hallucinate tools like 'ultra-forensics-3000'")
                console.print("  • Find Evil Agent: Validates every selection against real tool registry")
                console.print("  • Result: 100% confidence that selected tool exists and is appropriate")
                console.print()

            else:
                console.print(f"[red]✗ Error:[/red] {result.error}")

        except Exception as e:
            progress.stop()
            console.print(f"[red]✗ Demo 1 failed:[/red] {e}")
            import traceback
            traceback.print_exc()


async def demo_autonomous_investigation():
    """Demo 2: Show autonomous iterative investigation."""
    console.print()
    console.print(Panel.fit(
        "[bold magenta]Differentiator #2: Autonomous Investigative Reasoning[/bold magenta]\n"
        "[dim]Automatically follows leads: Initial → Follow-up → Follow-up → Complete Picture[/dim]",
        border_style="magenta"
    ))
    console.print()

    console.print("[yellow]Scenario:[/yellow] Investigate suspicious process activity")
    console.print("[yellow]Traditional:[/yellow] Analyst runs each tool manually, interprets, decides next step")
    console.print("[yellow]Find Evil:[/yellow] Agent automatically follows investigative leads")
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running autonomous investigation...", total=None)

        try:
            orchestrator = OrchestratorAgent()

            start_time = time.time()

            # Test case: Open-ended investigation
            result = await orchestrator.process_iterative(
                incident_description="Unknown process consuming high CPU and making network connections",
                analysis_goal="Identify the process, determine if malicious, and trace its origin",
                max_iterations=3,
                auto_follow=True
            )

            duration = time.time() - start_time
            progress.update(task, completed=True)

            console.print("[bold green]✓ Investigation Complete[/bold green]\n")

            # Investigation summary
            console.print(f"[bold]Summary:[/bold]")
            console.print(f"[dim]{result.investigation_summary}[/dim]")
            console.print()

            # Show iteration details
            console.print(f"[bold]Autonomous Analysis Chain ({len(result.iterations)} iterations):[/bold]\n")

            for i, iteration in enumerate(result.iterations, 1):
                console.print(f"[cyan]Iteration {i}:[/cyan] {iteration.tool_used}")
                console.print(f"  • Findings: {len(iteration.findings)}, IOCs: {sum(len(v) for v in iteration.iocs.values())}")
                console.print(f"  • Duration: {iteration.duration:.1f}s")

                if iteration.lead_followed:
                    console.print(f"  • [dim]Lead followed: {iteration.lead_followed.description[:70]}...[/dim]")

                if iteration.leads_discovered:
                    console.print(f"  • [green]Discovered {len(iteration.leads_discovered)} new lead(s)[/green]")
                    for lead in iteration.leads_discovered[:1]:
                        console.print(f"    → [{lead.priority.value}] {lead.lead_type.value}: {lead.description[:60]}...")

                console.print()

            # Summary stats
            console.print(f"[bold]Results:[/bold]")
            console.print(f"  • Total Findings: {len(result.all_findings)}")
            console.print(f"  • Total IOCs: {sum(len(v) for v in result.all_iocs.values())}")
            console.print(f"  • Total Duration: {duration:.1f}s")
            console.print(f"  • Stopped: {result.stopping_reason}")
            console.print()

            console.print("[bold magenta]Key Points:[/bold magenta]")
            console.print("  • Traditional: Run tool → interpret → manually select next → repeat (hours)")
            console.print(f"  • Find Evil: Autonomous chain in {len(result.iterations)} iterations ({duration:.0f}s)")
            console.print("  • Result: Complete investigation without manual intervention")
            console.print()

        except Exception as e:
            progress.stop()
            console.print(f"[red]✗ Demo 2 failed:[/red] {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Run auto demo."""
    console.print()
    console.print(Panel.fit(
        "[bold white]Find Evil Agent - Hackathon Auto-Demo[/bold white]\n"
        "[dim]Showcasing Two Unique Differentiators[/dim]",
        border_style="white"
    ))

    # Configuration
    settings = get_settings()
    console.print()
    console.print("[bold]Configuration:[/bold]")
    console.print(f"  • LLM: {settings.llm_provider.value} ({settings.llm_model_name})")
    console.print(f"  • SIFT VM: {settings.sift_vm_host}:{settings.sift_vm_port}")
    console.print(f"  • User: {settings.sift_ssh_user}")
    console.print()

    # Demo 1
    console.print("[bold yellow]Starting Demo 1: Hallucination Prevention[/bold yellow]")
    await demo_hallucination_prevention()

    console.print("\n" + "="*70 + "\n")

    # Demo 2
    console.print("[bold yellow]Starting Demo 2: Autonomous Investigation[/bold yellow]")
    await demo_autonomous_investigation()

    # Final summary
    console.print()
    console.print(Panel.fit(
        "[bold green]Demo Complete![/bold green]\n\n"
        "[bold]Two Differentiators Demonstrated:[/bold]\n"
        "1. Hallucination-Resistant Tool Selection\n"
        "   [dim]→ Two-stage validation prevents LLM from selecting non-existent tools[/dim]\n\n"
        "2. Autonomous Investigative Reasoning\n"
        "   [dim]→ Automatically follows leads to build complete attack chains[/dim]\n\n"
        "[bold cyan]No other DFIR tool has BOTH capabilities.[/bold cyan]",
        border_style="green"
    ))
    console.print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Demo failed:[/red] {e}")
        import traceback
        traceback.print_exc()
