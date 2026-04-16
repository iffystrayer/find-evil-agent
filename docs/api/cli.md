# CLI Reference

Complete reference for Find Evil Agent's command-line interface.

## Global Options

Available for all commands:

```bash
--help          Show help message and exit
--version       Show version information
```

## Commands

### analyze

Run single-shot forensic analysis (Feature #1: Hallucination-Resistant Tool Selection).

```bash
find-evil analyze <INCIDENT_DESCRIPTION> <ANALYSIS_GOAL> [OPTIONS]
```

**Arguments:**

- `INCIDENT_DESCRIPTION` (required): Description of the security incident
- `ANALYSIS_GOAL` (required): What you want to analyze or discover

**Options:**

- `-o, --output PATH`: Save report to file (markdown format)
- `-v, --verbose`: Show detailed logs
- `--timeout INTEGER`: Execution timeout in seconds (default: 60)
- `--help`: Show help message

**Example:**

```bash
find-evil analyze \
  "Ransomware detected on Windows 10 endpoint at 2026-04-10 14:30" \
  "Identify malicious processes and C2 communication" \
  --output ransomware_report.md \
  --verbose \
  --timeout 300
```

**Output:**

```
🔍 Starting Analysis...

📋 Incident: Ransomware detected on Windows 10 endpoint
🎯 Goal: Identify malicious processes and C2 communication

Step 1: Tool Selection
  ├─ Semantic search: 5 candidates identified
  ├─ LLM ranking: volatility selected
  ├─ Confidence: 0.85 (threshold: 0.7) ✅
  └─ Reasoning: Memory analysis required for process identification

Step 2: Tool Execution
  ├─ Tool: volatility
  ├─ Command: volatility -f memory.raw --profile=Win10x64 pslist
  ├─ Status: Running on SIFT VM (192.168.12.101)
  ├─ Duration: 90.2s
  └─ Output: 3,521 characters

Step 3: Analysis
  ├─ Findings: 4 critical, 2 high, 1 medium
  ├─ IOCs Extracted:
  │   ├─ IPs: 203.0.113.42, 198.51.100.10
  │   ├─ Domains: evil-c2.example.com
  │   ├─ Hashes: a3f8b9c2d1e4f5... (SHA256)
  │   └─ Paths: C:\Windows\Temp\ransom.exe
  └─ Report saved: ransomware_report.md

✅ Analysis Complete (Total: 92.1s)
```

**Exit Codes:**

- `0`: Analysis successful
- `1`: Analysis failed
- `2`: Invalid arguments
- `3`: Configuration error

---

### investigate

Run autonomous iterative investigation (Feature #2: Autonomous Investigative Reasoning).

```bash
find-evil investigate <INCIDENT_DESCRIPTION> <ANALYSIS_GOAL> [OPTIONS]
```

**Arguments:**

- `INCIDENT_DESCRIPTION` (required): Description of the security incident
- `ANALYSIS_GOAL` (required): Investigation goal (e.g., "Reconstruct attack chain")

**Options:**

- `--max-iterations INTEGER`: Maximum analysis iterations (default: 5)
- `--min-lead-confidence FLOAT`: Minimum confidence for leads (default: 0.6)
- `-o, --output PATH`: Save investigation report to file
- `-v, --verbose`: Show detailed progress
- `--help`: Show help message

**Example:**

```bash
find-evil investigate \
  "Unknown process consuming high CPU and making network connections" \
  "Identify the process, determine if malicious, and trace its origin" \
  --max-iterations 3 \
  --output investigation.md \
  --verbose
```

**Output:**

```
🔄 Autonomous Investigation Starting...

📋 Incident: Unknown process consuming high CPU
🎯 Goal: Identify the process, determine if malicious, and trace its origin
🔢 Max Iterations: 3

─────────────────────────────────────────────────────────────────────

Iteration 1/3

Step 1: Tool Selection
  ├─ Selected: volatility (confidence: 0.88)
  └─ Reasoning: Memory analysis required for process identification

Step 2: Execution
  ├─ Duration: 18.7s
  └─ Output: 4,213 characters

Step 3: Analysis
  ├─ Findings: 3 (2 high, 1 medium)
  └─ IOCs: 2 IPs, 1 domain

Leads Discovered: 3
  1. [HIGH] Create super-timeline to identify initial infection vector
  2. [MEDIUM] Analyze network connections from suspicious process
  3. [LOW] Extract file system metadata for suspicious files

Following Lead: "Create super-timeline to identify initial infection vector"

─────────────────────────────────────────────────────────────────────

Iteration 2/3

Step 1: Tool Selection
  ├─ Selected: log2timeline (confidence: 0.91)
  └─ Reasoning: Timeline creation for infection vector identification

Step 2: Execution
  ├─ Duration: 13.9s
  └─ Output: 2,891 characters

Step 3: Analysis
  ├─ Findings: 2 (1 high, 1 medium)
  └─ IOCs: 1 IP, 2 file paths

Leads Discovered: 2
  1. [HIGH] Analyze file system metadata for suspicious executables
  2. [MEDIUM] Check registry for persistence mechanisms

Following Lead: "Analyze file system metadata for suspicious executables"

─────────────────────────────────────────────────────────────────────

Iteration 3/3

Step 1: Tool Selection
  ├─ Selected: fls (confidence: 0.87)
  └─ Reasoning: File system metadata analysis

Step 2: Execution
  ├─ Duration: 13.0s
  └─ Output: 1,542 characters

Step 3: Analysis
  ├─ Findings: 4 (1 critical, 2 high, 1 medium)
  └─ IOCs: 3 file paths, 1 hash

Leads Discovered: 0
Investigation Complete: Maximum iterations reached

─────────────────────────────────────────────────────────────────────

✅ Investigation Complete

Iterations: 3
Total Duration: 45.6s
Stopping Reason: max_iterations_reached
Tools Used: volatility → log2timeline → fls

Total Findings: 9
Total IOCs:
  ├─ IPs: 3
  ├─ Domains: 1
  ├─ File Paths: 6
  └─ Hashes: 1

Investigation Summary:
The investigation revealed a multi-stage attack chain. Initial memory analysis
identified a suspicious process (PID 4892) making network connections to
203.0.113.42. Timeline analysis showed the process was spawned by a malicious
executable downloaded at 14:32 UTC. File system analysis confirmed the presence
of the dropper at C:\Users\victim\AppData\Local\Temp\update.exe with hash
a3f8b9c2d1e4f5a6b7c8d9e0f1a2b3c4. The complete attack chain: phishing email →
malicious attachment → dropper execution → C2 communication.

Report saved: investigation.md
```

**Stopping Conditions:**

- Max iterations reached
- No leads with confidence ≥ min-lead-confidence
- LLM explicitly signals investigation complete
- Critical error encountered

---

### config

Get current configuration status.

```bash
find-evil config
```

**Output:**

```
⚙️ Find Evil Agent Configuration

LLM Provider: ollama (gemma4:31b-cloud)
SIFT VM: sansforensics@192.168.12.101:22
SSH Key: /Users/username/.ssh/sift_vm_key
Langfuse: http://localhost:33000 (enabled)
Tool Registry: 18 tools loaded

Tool Selection:
  ├─ Confidence Threshold: 0.7
  └─ Semantic Search Top-K: 10

Security:
  ├─ Max Tool Timeout: 3600s
  └─ Default Timeout: 60s

Status: ✅ All systems operational
```

**Exit Codes:**

- `0`: Configuration valid
- `1`: Configuration error (missing required settings)

---

### version

Show version information.

```bash
find-evil version
```

**Output:**

```
Find Evil Agent v0.1.0
Python: 3.13.3
LangGraph: 0.2.x
LangChain Core: 0.3.x
FAISS: 1.9.x
```

---

## Environment Variables

Configuration via `.env` file:

### LLM Provider

```bash
# Provider selection
LLM_PROVIDER=ollama|openai|anthropic

# Ollama
LLM_MODEL_NAME=gemma4:31b-cloud
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI
OPENAI_API_KEY=sk-...
LLM_MODEL_NAME=gpt-4

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL_NAME=claude-3-opus-20240229
```

### SIFT VM

```bash
SIFT_VM_HOST=192.168.12.101
SIFT_VM_PORT=22
SIFT_SSH_USER=sansforensics
SIFT_SSH_KEY_PATH=/path/to/ssh/key  # Optional
```

### Tool Selection

```bash
# Minimum confidence for tool selection (0.0-1.0)
TOOL_CONFIDENCE_THRESHOLD=0.7

# Number of semantic search candidates
SEMANTIC_SEARCH_TOP_K=10

# Tool execution timeout (seconds)
DEFAULT_TOOL_TIMEOUT=60
MAX_TOOL_TIMEOUT=3600
```

### Observability

```bash
# Langfuse
LANGFUSE_ENABLED=true
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=http://localhost:33000

# Prometheus
PROMETHEUS_ENABLED=false
PROMETHEUS_PORT=60090
```

---

## Common Workflows

### Ransomware Investigation

```bash
# Single-shot analysis
find-evil analyze \
  "Ransomware encrypted files on fileserver at 2026-04-10 02:15 UTC" \
  "Identify ransomware process, encryption method, and C2 communication" \
  -o ransomware_report.md -v

# Multi-iteration investigation
find-evil investigate \
  "Ransomware encrypted files on fileserver" \
  "Reconstruct complete attack chain from initial access to encryption" \
  --max-iterations 5 \
  -o ransomware_chain.md -v
```

### Malware Binary Analysis

```bash
find-evil analyze \
  "Unknown binary downloaded from phishing email: malware.exe (SHA256: a3f8...)" \
  "Extract strings, identify packing, find network indicators" \
  -o malware_analysis.md --timeout 300
```

### Network Intrusion

```bash
find-evil analyze \
  "IDS alert: Port scan detected from 198.51.100.10 targeting internal network" \
  "Identify scan pattern, targeted ports, and lateral movement indicators" \
  -o network_intrusion.md
```

### APT Investigation

```bash
find-evil investigate \
  "Suspected APT activity with lateral movement across multiple hosts" \
  "Map complete attack timeline from initial compromise to current state" \
  --max-iterations 7 \
  -o apt_timeline.md -v
```

### Data Exfiltration

```bash
find-evil investigate \
  "Large data transfer detected to unknown external IP 203.0.113.42" \
  "Trace data source, identify accessed files, and network timeline" \
  --max-iterations 4 \
  -o exfiltration_investigation.md
```

---

## Report Format

### Markdown Report Structure

When using `--output`, reports are saved in markdown format:

```markdown
# Forensic Analysis Report

**Session ID:** 550e8400-e29b-41d4-a716-446655440000  
**Timestamp:** 2026-04-10 19:30:00 UTC  
**Duration:** 92.1s

## Incident

Ransomware detected on Windows 10 endpoint at 2026-04-10 14:30

## Analysis Goal

Identify malicious processes and C2 communication

## Tool Selection

**Tool:** volatility  
**Confidence:** 0.85 (85%)  
**Reasoning:** Memory analysis required for process identification

**Alternative Tools Considered:**
- bulk_extractor (confidence: 0.72)
- strings (confidence: 0.68)

## Execution

**Command:** volatility -f memory.raw --profile=Win10x64 pslist  
**Duration:** 90.2s  
**Return Code:** 0

## Findings

### Finding 1: Malicious Process Identified [CRITICAL]

**Confidence:** 0.92  
**Description:** Ransomware process "crypto.exe" (PID 4892) executing from temp directory  
**Evidence:** Process path: C:\Windows\Temp\crypto.exe, Parent PID: 1234 (explorer.exe)

### Finding 2: C2 Communication Detected [HIGH]

**Confidence:** 0.88  
**Description:** Network connection to known C2 server  
**Evidence:** Destination IP: 203.0.113.42:443, Protocol: HTTPS

[... more findings ...]

## Indicators of Compromise

**IP Addresses:**
- 203.0.113.42
- 198.51.100.10

**Domains:**
- evil-c2.example.com

**File Hashes (SHA256):**
- a3f8b9c2d1e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0

**File Paths:**
- C:\Windows\Temp\crypto.exe
- C:\Users\victim\Desktop\ransom_note.txt

## Recommendations

1. Isolate affected system immediately
2. Block C2 IP addresses at firewall
3. Search for IOCs across network
4. Restore from clean backups
```

---

## Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Command completed successfully |
| 1 | Error | General error (see stderr for details) |
| 2 | Invalid Arguments | Missing or invalid command-line arguments |
| 3 | Configuration Error | Missing or invalid `.env` configuration |
| 4 | Connection Error | Failed to connect to LLM or SIFT VM |
| 5 | Timeout Error | Tool execution exceeded timeout |
| 6 | Validation Error | Tool selection confidence below threshold |

---

## Troubleshooting

### Verbose Mode

Use `-v` or `--verbose` to see detailed logs:

```bash
find-evil analyze "..." "..." -v
```

Output includes:

- LLM prompts and responses
- Semantic search candidates
- SSH connection details
- Tool execution logs
- IOC extraction details

### Configuration Check

Verify configuration before analysis:

```bash
find-evil config
```

Check for:

- ✅ LLM provider accessible
- ✅ SIFT VM SSH connection
- ✅ Tool registry loaded
- ✅ Langfuse enabled (if configured)

### Common Errors

**SSH Connection Failed:**

```bash
# Test SSH manually
ssh -i ~/.ssh/sift_vm_key sansforensics@192.168.12.101

# Check SSH key permissions
chmod 600 ~/.ssh/sift_vm_key
```

**LLM Provider Connection Failed:**

```bash
# Ollama
curl http://localhost:11434/api/tags

# OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Low Tool Selection Confidence:**

Provide more context in incident description:

- Include timestamps
- Specify system details (OS, version)
- Mention specific indicators (IPs, file names)

---

## Next Steps

- [REST API Reference](rest.md) - HTTP API documentation
- [Python API Reference](python.md) - Programmatic usage
- [MCP Server Reference](mcp.md) - Model Context Protocol
- [Configuration Guide](../configuration.md) - Detailed configuration options
