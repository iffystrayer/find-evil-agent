"""Quick test script for graph visualization integration."""

import asyncio
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from find_evil_agent.agents.reporter import ReporterAgent
from find_evil_agent.agents.schemas import Finding, FindingSeverity
from find_evil_agent.agents.report_schemas import ReportFormat


async def main():
    """Test graph integration with mock findings."""

    # Create mock findings with relationships
    findings = [
        Finding(
            title="Suspicious PowerShell Execution",
            description="powershell.exe spawned cmd.exe which created file /tmp/malware.bin and connected to 192.168.1.100:4444",
            severity=FindingSeverity.CRITICAL,
            confidence=0.95,
            evidence=["Process tree analysis"],
            tool_references=["volatility"],
            timestamp=datetime.utcnow(),
        ),
        Finding(
            title="Malicious Registry Modification",
            description="Process malware.exe modified registry HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run for persistence",
            severity=FindingSeverity.HIGH,
            confidence=0.90,
            evidence=["Registry analysis"],
            tool_references=["regripper"],
            timestamp=datetime.utcnow(),
        ),
        Finding(
            title="Network Connection to C2 Server",
            description="Process cmd.exe connected to malicious.com via DNS query and established connection to 192.168.1.100:4444",
            severity=FindingSeverity.CRITICAL,
            confidence=0.98,
            evidence=["Network traffic analysis"],
            tool_references=["wireshark"],
            timestamp=datetime.utcnow(),
        ),
    ]

    # Aggregate IOCs
    iocs = {
        "process": ["powershell.exe", "cmd.exe", "malware.exe"],
        "file": ["/tmp/malware.bin"],
        "ipv4": ["192.168.1.100"],
        "domain": ["malicious.com"],
        "registry": ["HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"],
    }

    # Create reporter and generate HTML report
    reporter = ReporterAgent()

    print("🔍 Generating report with graph visualization...")

    report_html = await reporter.generate_report(
        analysis_result=type('obj', (), {
            'findings': findings,
            'iocs': iocs,
        })(),
        format=ReportFormat.HTML,
        session_id=str(uuid4()),
        incident_description="Ransomware attack detected on production server",
        analysis_goal="Identify attack chain and IOCs",
    )

    # Save to file
    output_path = Path("test_graph_report.html")
    with open(output_path, 'w') as f:
        f.write(report_html)

    print(f"✅ Report generated: {output_path}")
    print(f"📊 Report size: {len(report_html):,} bytes")
    print(f"🕸️ Graph included: {'attack_graph' in report_html or 'D3.js' in report_html}")
    print(f"\n🌐 Open in browser: file://{output_path.absolute()}")

    # Check for graph indicators
    if "d3.v7.min.js" in report_html:
        print("✅ D3.js library included")
    if "graphData" in report_html or "GRAPH_DATA" in report_html:
        print("✅ Graph data present")
    if "entry_points" in report_html:
        print("✅ Graph metadata included")


if __name__ == "__main__":
    asyncio.run(main())
