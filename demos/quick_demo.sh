#!/bin/bash
# Quick Demo - Professional Reporting Integration

set -e

echo "==================================="
echo "Find Evil Agent - Professional Reporting Demo"
echo "==================================="
echo ""

# Activate environment
source .venv/bin/activate

# Show version and config
echo "1. Configuration Check:"
find-evil config
echo ""

# Show help for analyze command
echo "2. Analyze Command Options:"
find-evil analyze --help
echo ""

# Create demo output directory
mkdir -p demos/output

# Simulate analysis with markdown report
echo "3. Running Analysis (Markdown Report):"
echo "   Command: find-evil analyze \"Suspicious PowerShell execution detected\" \"Identify malicious scripts\" -o demos/output/report.md"
echo ""
echo "   [Note: Full analysis requires ~60-90s with SIFT VM]"
echo ""

# Show what the command would generate
echo "4. Report Formats Supported:"
echo "   • Markdown (.md) - Human-readable text"
echo "   • HTML (.html) - Styled browser report with CSS"
echo "   • PDF (.pdf) - Professional document (requires weasyprint)"
echo ""

echo "5. Professional Report Features:"
echo "   ✓ Executive Summary (4 sections: overview, findings, impact, recommendations)"
echo "   ✓ MITRE ATT&CK Mapping (11 techniques across 5 tactics)"
echo "   ✓ IOC Tables (7 types with deduplication)"
echo "   ✓ Chronological Timeline"
echo "   ✓ Findings by Severity"
echo "   ✓ Prioritized Recommendations"
echo "   ✓ Evidence Citations"
echo "   ✓ Report Metadata"
echo ""

echo "Demo complete! For full live test, run:"
echo "  find-evil analyze \"<incident>\" \"<goal>\" -o report.html"
echo ""
