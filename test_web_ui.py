#!/usr/bin/env python3
"""Quick test to verify web UI analysis works end-to-end."""

import asyncio
from find_evil_agent.agents.orchestrator import OrchestratorAgent
from find_evil_agent.agents.reporter import ReporterAgent
from find_evil_agent.agents.report_schemas import ReportFormat

async def test_single_analysis():
    """Test single analysis workflow (as used by web UI)."""
    print("Testing single analysis workflow...")

    # Create orchestrator
    orchestrator = OrchestratorAgent()

    # Test scenario
    incident = "Ransomware detected encrypting files on Windows server"
    goal = "Identify malicious processes and IOCs for containment"

    print(f"\nIncident: {incident}")
    print(f"Goal: {goal}\n")

    try:
        # Run analysis (same as web UI does)
        print("Running analysis...")
        result = await orchestrator.process({
            "incident_description": incident,
            "analysis_goal": goal
        })

        if result.success:
            print("✅ Analysis completed successfully!")
            print(f"   Tools selected: {result.data.get('tool_selection', {}).get('tool_name', 'N/A')}")
            print(f"   Findings count: {len(result.data.get('findings', []))}")

            # Generate report (same as web UI does)
            print("\nGenerating report...")
            reporter = ReporterAgent()
            report_result = await reporter.generate_report(
                result=result,
                format=ReportFormat.HTML,
                incident_description=incident,
                analysis_goal=goal
            )

            if report_result.success:
                print("✅ Report generated successfully!")
                report_path = "reports/test_web_ui_report.html"

                # Save report
                with open(report_path, "w") as f:
                    f.write(report_result.data["report"])

                print(f"   Report saved to: {report_path}")
                print(f"   Report size: {len(report_result.data['report'])} bytes")
                print(f"   Has graph: {'attack_graph' in report_result.data}")

                return True
            else:
                print(f"❌ Report generation failed: {report_result.message}")
                return False
        else:
            print(f"❌ Analysis failed: {result.message}")
            return False

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_investigative_mode():
    """Test investigative mode workflow (as used by web UI)."""
    print("\n" + "="*60)
    print("Testing investigative mode workflow...")

    # Create orchestrator
    orchestrator = OrchestratorAgent()

    # Test scenario
    incident = "Suspicious PowerShell execution detected"
    goal = "Reconstruct attack chain"
    iterations = 2  # Quick test with 2 iterations

    print(f"\nIncident: {incident}")
    print(f"Goal: {goal}")
    print(f"Iterations: {iterations}\n")

    try:
        print("Running investigation...")
        result = await orchestrator.iterative_investigation(
            incident_description=incident,
            analysis_goal=goal,
            max_iterations=iterations
        )

        if result.success:
            print(f"✅ Investigation completed successfully!")
            print(f"   Iterations completed: {len(result.data.get('iterations', []))}")
            print(f"   Total findings: {result.data.get('total_findings', 0)}")

            # Generate report
            print("\nGenerating investigation report...")
            reporter = ReporterAgent()
            report_result = await reporter.generate_report(
                result=result,
                format=ReportFormat.HTML,
                incident_description=incident,
                analysis_goal=goal
            )

            if report_result.success:
                print("✅ Investigation report generated!")
                report_path = "reports/test_investigation_report.html"

                with open(report_path, "w") as f:
                    f.write(report_result.data["report"])

                print(f"   Report saved to: {report_path}")
                print(f"   Report size: {len(report_result.data['report'])} bytes")

                return True
            else:
                print(f"❌ Report generation failed: {report_result.message}")
                return False
        else:
            print(f"❌ Investigation failed: {result.message}")
            return False

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("="*60)
    print("Find Evil Agent - Web UI Backend Testing")
    print("="*60)

    # Test 1: Single analysis
    test1 = await test_single_analysis()

    # Test 2: Investigative mode
    test2 = await test_investigative_mode()

    # Summary
    print("\n" + "="*60)
    print("Test Summary:")
    print(f"  Single Analysis: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"  Investigative Mode: {'✅ PASS' if test2 else '❌ FAIL'}")
    print("="*60)

    if test1 and test2:
        print("\n✅ All tests passed! Web UI backend is functional.")
        print("\nNext steps:")
        print("  1. Open http://localhost:17000 in browser")
        print("  2. Test UI with scenarios from DEMO_SCENARIOS.md")
        print("  3. Capture screenshots per SCREENSHOT_GUIDE.md")
        print("  4. Record demo video")
        return 0
    else:
        print("\n❌ Some tests failed. Check logs above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
