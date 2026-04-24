# Examples and Tutorials

Real-world usage examples for Find Evil Agent.

## Quick Examples

### Example 1: Malware Analysis

**Scenario:** Suspicious executable found in /tmp directory.

```bash
find-evil analyze \
  "Unknown binary /tmp/xmrig found consuming high CPU" \
  "Identify if cryptominer and extract C2 domains" \
  -o malware_report.md \
  --verbose
```

**Expected Tool:** `strings` or `file`

**Expected IOCs:**
- Cryptocurrency wallet addresses
- Mining pool domains
- Embedded C2 URLs

---

### Example 2: Network Forensics

**Scenario:** Suspicious outbound connections detected.

```bash
find-evil investigate \
  "Multiple connections to 185.220.101.42 from svchost.exe" \
  "Complete analysis: identify C2 patterns, extract domains, build timeline" \
  --max-iterations 5 \
  -o network_investigation.md
```

**Expected Flow:**
1. `netstat` - Identify connections
2. `tcpdump` - Analyze traffic patterns
3. `strings` - Extract domains from memory
4. `log2timeline` - Build timeline
5. `grep` - Find related log entries

---

### Example 3: Memory Forensics

**Scenario:** Memory dump from compromised system.

```bash
find-evil analyze \
  "Memory dump memory.dmp from Windows 10 system showing signs of code injection" \
  "Identify injected processes and extract malicious code" \
  -o memory_analysis.md
```

**Expected Tool:** `volatility`

**Expected Findings:**
- Injected processes
- Suspicious DLLs
- Network connections from memory

---

## Tutorial: Complete Incident Response

### Scenario: Ransomware Investigation

You receive an alert about a ransomware infection on a Windows 10 endpoint. The user reports files are encrypted with a `.locked` extension.

#### Step 1: Initial Triage

```bash
find-evil analyze \
  "Ransomware detected - files encrypted with .locked extension on Windows 10" \
  "Identify ransomware variant and initial infection vector" \
  -o step1_triage.md \
  --provider ollama \
  --verbose
```

**Review Output:**
```markdown
## Tool Selected: strings
**Confidence:** 0.87
**Reasoning:** Analyzing encrypted files for ransom notes and metadata

## Findings:
- Ransom note detected: DECRYPT_INSTRUCTIONS.txt
- Bitcoin wallet: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
- Contact email: unlock@evil.com
- Variant: Likely Maze ransomware based on note format
```

#### Step 2: Deep Investigation

Now that we know it's ransomware, let's trace the attack chain:

```bash
find-evil investigate \
  "Maze ransomware infection detected, Bitcoin wallet 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" \
  "Build complete attack timeline: initial access, lateral movement, data exfiltration, encryption" \
  --max-iterations 7 \
  -o step2_investigation.md
```

**Investigation Flow:**
```
Iteration 1: log2timeline
  → Found: Initial phishing email at 2024-04-15 14:32:18
  → Lead: Suspicious attachment invoice_2024.pdf.exe
  
Iteration 2: volatility
  → Found: invoice_2024.pdf.exe created process winlogon.exe (PID 2847)
  → Lead: Process injection detected
  
Iteration 3: netstat
  → Found: Connections to 185.220.101.42:443 (C2 server)
  → Lead: Data exfiltration detected (3.2 GB uploaded)
  
Iteration 4: strings
  → Found: Embedded PowerShell commands for lateral movement
  → Lead: SMB connections to DC01 and FILE01
  
Iteration 5: grep
  → Found: Windows Event logs showing successful lateral movement
  → Lead: Domain admin credentials used
  
Iteration 6: fls
  → Found: Ransomware binary copied to network shares
  → Lead: Encryption started at 2024-04-15 16:45:22
  
Iteration 7: tcpdump
  → Found: TOR communication for C2
  → Investigation complete: Full attack chain mapped
```

#### Step 3: Extract IOCs

```bash
# Extract IOCs from investigation report
grep -E "([0-9]{1,3}\.){3}[0-9]{1,3}|[a-zA-Z0-9-]+\.(com|net|org)" step2_investigation.md > iocs.txt

# Result:
# 185.220.101.42
# unlock@evil.com
# evil-tor-node.onion
```

#### Step 4: Generate Executive Report

```bash
find-evil analyze \
  "Complete ransomware investigation results: Initial access via phishing, lateral movement using stolen domain admin creds, 3.2GB exfiltrated, Maze ransomware deployed" \
  "Generate executive summary for management highlighting impact, timeline, and recommendations" \
  -o executive_summary.html \
  --format html
```

**Timeline Produced:**
```
2024-04-15 14:32:18 - Phishing email received
2024-04-15 14:35:42 - Malicious attachment executed
2024-04-15 14:36:15 - C2 connection established to 185.220.101.42
2024-04-15 15:12:33 - Lateral movement to DC01
2024-04-15 15:45:18 - Domain admin credentials stolen
2024-04-15 16:12:08 - Data exfiltration begins (3.2 GB)
2024-04-15 16:45:22 - Ransomware encryption starts
2024-04-15 17:03:17 - All files encrypted, ransom note displayed
```

---

## API Integration Examples

### Python Integration

```python
from find_evil_agent.agents.orchestrator import OrchestratorAgent
from find_evil_agent.config import Config

# Initialize
config = Config.from_env()
orchestrator = OrchestratorAgent(config)

# Batch processing incidents from SIEM
incidents = [
    "Suspicious PowerShell execution on DESKTOP-42",
    "Multiple failed login attempts from 10.0.0.99",
    "Unknown process connecting to pastebin.com"
]

for incident in incidents:
    result = orchestrator.analyze(
        incident_description=incident,
        analysis_goal="Triage and extract IOCs",
        confidence_threshold=0.7
    )
    
    # Send high-severity findings to SIEM
    if result.severity in ["HIGH", "CRITICAL"]:
        send_to_siem(result.iocs)
    
    # Generate report
    with open(f"reports/{incident[:20]}.md", "w") as f:
        f.write(result.report_markdown)
```

### REST API from JavaScript

```javascript
async function analyzeIncident(incident, goal) {
  const response = await fetch('http://localhost:18000/api/v1/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      incident_description: incident,
      analysis_goal: goal,
      provider: 'ollama'
    })
  });
  
  const result = await response.json();
  
  // Display results
  console.log(`Tool: ${result.tool_selected}`);
  console.log(`Confidence: ${result.confidence}`);
  console.log(`IOCs found: ${result.iocs.length}`);
  
  // Send to dashboard
  updateDashboard(result);
}

// Usage
analyzeIncident(
  "Malware detected in Downloads folder",
  "Identify malware family and C2 infrastructure"
);
```

---

## Advanced Workflows

### Multi-File Analysis Pipeline

Analyze multiple evidence files in sequence:

```bash
#!/bin/bash

# Evidence files
MEMORY_DUMP="evidence/memory.dmp"
DISK_IMAGE="evidence/disk.dd"
PCAP_FILE="evidence/network.pcap"

# Step 1: Memory analysis
find-evil analyze \
  "Memory dump $MEMORY_DUMP from compromised Windows system" \
  "Identify running malware and network connections" \
  -o reports/01_memory.md

# Step 2: Disk forensics
find-evil analyze \
  "Disk image $DISK_IMAGE - looking for persistence mechanisms" \
  "Find startup entries, scheduled tasks, and suspicious files" \
  -o reports/02_disk.md

# Step 3: Network analysis
find-evil analyze \
  "PCAP file $PCAP_FILE captured during incident" \
  "Extract C2 domains and data exfiltration evidence" \
  -o reports/03_network.md

# Step 4: Correlate findings
find-evil investigate \
  "Combined evidence: memory dump, disk image, and network capture" \
  "Build complete attack narrative connecting all findings" \
  --max-iterations 10 \
  -o reports/04_final_report.html \
  --format html
```

### Integration with Security Tools

```python
# Integration with VirusTotal, MISP, and TheHive

from find_evil_agent.agents.orchestrator import OrchestratorAgent
import requests

def enrich_with_vt(ioc):
    """Query VirusTotal for IOC reputation"""
    response = requests.get(
        f"https://www.virustotal.com/api/v3/ip_addresses/{ioc}",
        headers={"x-apikey": VT_API_KEY}
    )
    return response.json()

def send_to_misp(iocs):
    """Create MISP event with IOCs"""
    event = {
        "Event": {
            "info": "Find Evil Agent - Automated Analysis",
            "Attribute": [
                {"type": ioc.type, "value": ioc.value}
                for ioc in iocs
            ]
        }
    }
    requests.post(f"{MISP_URL}/events", json=event)

def create_thehive_case(result):
    """Create TheHive case from analysis"""
    case = {
        "title": f"Automated Analysis: {result.incident[:50]}",
        "description": result.report_markdown,
        "severity": 2 if result.severity == "HIGH" else 1,
        "observables": [
            {"dataType": ioc.type, "data": ioc.value}
            for ioc in result.iocs
        ]
    }
    requests.post(f"{HIVE_URL}/api/case", json=case)

# Run analysis
orchestrator = OrchestratorAgent.from_env()
result = orchestrator.analyze(
    incident_description="Suspicious lateral movement detected",
    analysis_goal="Identify compromised systems and attacker tools"
)

# Enrich and distribute
for ioc in result.iocs:
    if ioc.type == "ip":
        vt_data = enrich_with_vt(ioc.value)
        print(f"{ioc.value}: {vt_data['data']['attributes']['reputation']}")

send_to_misp(result.iocs)
create_thehive_case(result)
```

---

## MCP Server Examples

### Use with Claude Desktop

1. Configure MCP server in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "find-evil": {
      "command": "find-evil",
      "args": ["mcp-server"],
      "env": {
        "SIFT_VM_HOST": "192.168.12.101",
        "LLM_PROVIDER": "ollama"
      }
    }
  }
}
```

2. Use in Claude conversation:

```
User: I need to analyze a suspicious network connection to 185.220.101.42

Claude: I'll use the find-evil MCP server to analyze this.

[calls analyze_incident tool]

Based on the analysis:
- Tool selected: netstat (confidence: 0.88)
- Connection is to a known C2 server
- Process: svchost.exe (suspicious)
- Recommendation: Isolate system immediately

IOCs extracted:
- IP: 185.220.101.42 (C2 server)
- Process: svchost.exe
- Port: 443
```

---

## Performance Optimization

### Parallel Analysis

```python
import asyncio
from find_evil_agent.agents.orchestrator import OrchestratorAgent

async def analyze_many(incidents):
    orchestrator = OrchestratorAgent.from_env()
    
    tasks = [
        orchestrator.analyze(incident["description"], incident["goal"])
        for incident in incidents
    ]
    
    results = await asyncio.gather(*tasks)
    return results

# Analyze 10 incidents in parallel
incidents = [
    {"description": "...", "goal": "..."},
    # ... 9 more
]

results = asyncio.run(analyze_many(incidents))
print(f"Completed {len(results)} analyses")
```

---

## Testing Examples

### Unit Test for Custom Tool

```python
import pytest
from find_evil_agent.tools.registry import ToolRegistry

def test_custom_tool_registration():
    registry = ToolRegistry()
    
    registry.register_tool(
        name="my_scanner",
        description="Custom malware scanner",
        command_template="my_scanner {target}",
        category="analysis"
    )
    
    tool = registry.get_tool("my_scanner")
    assert tool.name == "my_scanner"
    assert tool.category == "analysis"

def test_tool_search():
    registry = ToolRegistry()
    
    results = registry.search("network traffic analysis", top_k=5)
    
    assert len(results) > 0
    assert results[0][1] > 0.5  # Confidence score
```

---

## Common Patterns

### Error Handling

```python
from find_evil_agent.exceptions import (
    ToolSelectionError,
    SSHConnectionError
)

try:
    result = orchestrator.analyze(incident, goal)
except ToolSelectionError as e:
    # Tool selection failed - try with lower confidence
    result = orchestrator.analyze(
        incident, goal,
        confidence_threshold=0.6
    )
except SSHConnectionError:
    # SIFT VM unreachable - check connection
    print("Error: Cannot connect to SIFT VM")
    print("Check: ping 192.168.12.101")
```

### Configuration Management

```python
# Different configs for different environments

# Development
dev_config = Config(
    llm_provider="ollama",
    ollama_base_url="http://localhost:11434",
    sift_vm_host="192.168.12.101",
    min_confidence=0.6  # Lower for testing
)

# Production
prod_config = Config(
    llm_provider="openai",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    sift_vm_host="sift-prod.company.com",
    min_confidence=0.8,  # Higher for production
    langfuse_enabled=True
)

orchestrator = OrchestratorAgent(
    config=prod_config if IS_PRODUCTION else dev_config
)
```

---

## Next Steps

- [Usage Guide](usage.md) - Complete usage documentation
- [API Reference](api/python.md) - Python API details
- [Troubleshooting](troubleshooting.md) - Common issues
- [FAQ](faq.md) - Frequently asked questions
