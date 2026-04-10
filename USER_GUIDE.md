# 📖 Find Evil Agent - User Guide

**Version:** 0.1.0  
**Last Updated:** April 10, 2026

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Understanding Results](#understanding-results)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## Introduction

Find Evil Agent is an autonomous AI-powered incident response tool that analyzes forensic evidence using the SANS SIFT Workstation. It uses a multi-agent system to:

1. **Select** the right forensic tool based on your incident description
2. **Execute** the tool safely on a SIFT VM via SSH
3. **Analyze** the results to extract IOCs and assess severity

**Key Benefits:**
- 🎯 **Prevents tool hallucination** - Two-stage selection with confidence thresholds
- ⚡ **Automates workflow** - From incident description to IOC report
- 🔒 **Secure execution** - SSH-based, read-only operations
- 📊 **Rich output** - Markdown reports with severity ratings

---

## Installation

### Prerequisites

**Required:**
- Python 3.11 or higher (tested with 3.13)
- SANS SIFT Workstation with SSH access
- LLM provider (Ollama, OpenAI, or Anthropic)

**Recommended:**
- `uv` for Python package management: `pip install uv`
- SSH key configured for SIFT VM access

### Step 1: Clone Repository

```bash
git clone https://github.com/iffystrayer/find-evil-agent.git
cd find-evil-agent
```

### Step 2: Create Virtual Environment

**Using uv (recommended):**
```bash
uv venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows
```

**Using standard venv:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows
```

### Step 3: Install Dependencies

**Using uv:**
```bash
uv pip install -e ".[dev]"
```

**Using pip:**
```bash
pip install -e ".[dev]"
```

### Step 4: Verify Installation

```bash
find-evil version
```

Expected output:
```
Find Evil Agent v0.1.0
Python: 3.13.3
LangGraph: 0.2.x
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

#### LLM Provider Configuration

**Option 1: Ollama (Free, Local)**
```bash
LLM_PROVIDER=ollama
LLM_MODEL_NAME=gemma4:31b-cloud
OLLAMA_BASE_URL=http://localhost:11434
```

**Option 2: OpenAI**
```bash
LLM_PROVIDER=openai
LLM_MODEL_NAME=gpt-4
OPENAI_API_KEY=sk-...
```

**Option 3: Anthropic**
```bash
LLM_PROVIDER=anthropic
LLM_MODEL_NAME=claude-3-opus-20240229
ANTHROPIC_API_KEY=sk-ant-...
```

#### SIFT VM Configuration

```bash
SIFT_VM_HOST=192.168.12.101
SIFT_VM_PORT=22
SIFT_SSH_USER=sansforensics
SIFT_SSH_KEY_PATH=/path/to/ssh/key  # Optional, uses ~/.ssh/id_rsa by default
```

#### Observability (Optional)

```bash
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=http://localhost:33000
```

### SSH Key Setup

Generate SSH key for SIFT VM access:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/sift_vm_key -C "find-evil-agent"
```

Copy public key to SIFT VM:

```bash
ssh-copy-id -i ~/.ssh/sift_vm_key sansforensics@192.168.12.101
```

Test SSH connection:

```bash
ssh -i ~/.ssh/sift_vm_key sansforensics@192.168.12.101 hostname
```

### Configuration Verification

Check your configuration:

```bash
find-evil config
```

Expected output:
```
✅ LLM Provider: ollama (gemma4:31b-cloud)
✅ SIFT VM: sansforensics@192.168.12.101:22
✅ SSH Key: /Users/username/.ssh/sift_vm_key
✅ Langfuse: http://localhost:33000 (enabled)
✅ Tool Registry: 18 tools loaded
```

---

## Usage

### Basic Analysis

Analyze an incident by providing:
1. **Incident description** - What happened
2. **Analysis goal** - What you want to find

```bash
find-evil analyze \
  "Ransomware detected on Windows endpoint at 2026-04-10 14:30" \
  "Identify malicious processes and network connections"
```

### Advanced Options

**Save report to file:**
```bash
find-evil analyze \
  "Suspicious PowerShell execution" \
  "Find script content and parent process" \
  --output report.md
```

**Verbose mode (show detailed logs):**
```bash
find-evil analyze \
  "Data exfiltration detected" \
  "Identify destination IPs and transferred files" \
  --verbose
```

**Specify custom timeout:**
```bash
find-evil analyze \
  "Memory dump analysis" \
  "Extract running processes" \
  --timeout 300  # 5 minutes
```

### Example Workflows

#### 1. Ransomware Investigation

```bash
find-evil analyze \
  "Ransomware encrypted files on fileserver at 2026-04-10 02:15 UTC" \
  "Identify ransomware process, encryption method, and C2 communication" \
  -o ransomware_report.md -v
```

**Expected Tools Selected:**
- `volatility` - Memory analysis for process identification
- `bulk_extractor` - Network packet analysis for C2

#### 2. Suspicious Login Activity

```bash
find-evil analyze \
  "Multiple failed SSH login attempts from unknown IP 203.0.113.42" \
  "Identify attack pattern and successful breaches" \
  -o ssh_breach_report.md
```

**Expected Tools Selected:**
- `log2timeline` - Parse authentication logs
- `grep` - Filter relevant log entries

#### 3. Malware Binary Analysis

```bash
find-evil analyze \
  "Unknown binary downloaded from phishing email: malware.exe" \
  "Extract strings, identify packing, find network indicators" \
  -o malware_analysis.md
```

**Expected Tools Selected:**
- `strings` - Extract readable strings
- `pescanner` - Analyze PE structure
- `bulk_extractor` - Find embedded IPs/domains

#### 4. Network Intrusion

```bash
find-evil analyze \
  "IDS alert: Port scan detected from 198.51.100.10 targeting internal network" \
  "Identify scan pattern, targeted ports, and lateral movement" \
  -o network_intrusion.md
```

**Expected Tools Selected:**
- `tcpdump` - Packet capture analysis
- `wireshark` - Protocol analysis

---

## Understanding Results

### Output Format

Analysis results are displayed in the terminal and optionally saved to markdown:

```
🔍 Starting Analysis...

📋 Incident: Ransomware detected on Windows endpoint
🎯 Goal: Identify malicious processes and network connections

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
  └─ Report saved: report.md

✅ Analysis Complete (Total: 92.1s)
```

### Report Structure

Markdown reports contain:

#### 1. Executive Summary
- Incident description
- Key findings count
- Severity distribution
- Timeline

#### 2. Tool Selection
- Selected tool and confidence score
- Selection reasoning
- Alternative tools considered

#### 3. Execution Details
- Command executed
- Execution duration
- Output size
- Any errors or warnings

#### 4. Findings
For each finding:
- **Severity:** Critical / High / Medium / Low / Info
- **Confidence:** 0.0-1.0 (LLM's confidence in this finding)
- **Description:** What was found
- **Evidence:** Supporting data from tool output

#### 5. Indicators of Compromise (IOCs)
- **IP Addresses:** External IPs contacted
- **Domains:** Suspicious domains
- **File Hashes:** MD5, SHA1, SHA256
- **File Paths:** Suspicious files
- **Emails:** Email addresses found
- **URLs:** URLs accessed

### Severity Levels

| Level | Meaning | Example |
|-------|---------|---------|
| **Critical** | Immediate threat, active exploitation | Ransomware encryption in progress |
| **High** | Serious security issue | Backdoor installed, C2 communication |
| **Medium** | Potential security concern | Suspicious process, unknown binary |
| **Low** | Minor anomaly | Unusual port listening |
| **Info** | Informational, no threat | System information, benign findings |

### Confidence Scores

**Tool Selection Confidence (≥0.7 required):**
- `0.9-1.0` - High confidence, perfect match
- `0.8-0.9` - Good confidence, likely correct
- `0.7-0.8` - Acceptable confidence, proceed with caution
- `<0.7` - Low confidence, selection rejected

**Finding Confidence:**
- `0.9-1.0` - Very likely true positive
- `0.7-0.9` - Likely true positive
- `0.5-0.7` - Uncertain, needs validation
- `<0.5` - Possible false positive

---

## Troubleshooting

### Common Issues

#### 1. SSH Connection Failed

**Error:**
```
❌ Error: Failed to connect to SIFT VM at 192.168.12.101:22
```

**Solutions:**
- Verify SIFT VM is running: `ping 192.168.12.101`
- Test SSH manually: `ssh sansforensics@192.168.12.101`
- Check SSH key permissions: `chmod 600 ~/.ssh/sift_vm_key`
- Verify `.env` has correct `SIFT_VM_HOST`, `SIFT_VM_PORT`, `SIFT_SSH_USER`

#### 2. LLM Provider Connection Failed

**Error:**
```
❌ Error: Failed to connect to Ollama at http://localhost:11434
```

**Solutions:**
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Verify model is pulled: `ollama list`
- Pull model if missing: `ollama pull gemma4:31b-cloud`
- Check `.env` has correct `OLLAMA_BASE_URL`

For OpenAI/Anthropic:
- Verify API key is valid
- Check account has sufficient credits
- Test API manually: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`

#### 3. Low Tool Selection Confidence

**Error:**
```
⚠️  Warning: Tool selection confidence (0.62) below threshold (0.7)
```

**Causes:**
- Incident description too vague
- Analysis goal not specific enough
- No perfect tool match in registry

**Solutions:**
- Provide more context in incident description (dates, IPs, file names)
- Clarify analysis goal (what specifically to find)
- Check available tools: `grep 'name:' tools/metadata.yaml`
- Lower threshold (not recommended): Set `TOOL_SELECTION_CONFIDENCE_THRESHOLD=0.6` in `.env`

#### 4. Tool Execution Timeout

**Error:**
```
❌ Error: Tool execution timed out after 60s
```

**Solutions:**
- Increase timeout: `find-evil analyze ... --timeout 300`
- Set default timeout in `.env`: `TOOL_EXECUTION_TIMEOUT=300`
- Check SIFT VM resource usage: `ssh sansforensics@192.168.12.101 top`
- Verify tool is appropriate for dataset size

#### 5. No IOCs Found

**Output:**
```
⚠️  Warning: No IOCs extracted from tool output
```

**Causes:**
- Tool output was empty or error
- Analysis goal didn't match tool capabilities
- LLM failed to parse output

**Solutions:**
- Check tool output in verbose mode: `find-evil analyze ... -v`
- Verify tool completed successfully (check stderr)
- Try different analysis goal or tool
- Check Langfuse traces for LLM parsing errors

#### 6. Permission Denied on SIFT VM

**Error:**
```
❌ Error: Permission denied: /mnt/evidence/disk.raw
```

**Solutions:**
- Ensure SSH user has read access: `ssh sansforensics@192.168.12.101 ls -la /mnt/evidence`
- Add user to forensics group: `sudo usermod -a -G forensics sansforensics`
- Use sudo if appropriate: Configure sudoers for specific tools

---

## Best Practices

### 1. Incident Descriptions

**Good:**
```
"Ransomware detected on Windows 10 endpoint WKS-042 at 2026-04-10 14:30 UTC. 
Files encrypted with .locked extension. Ransom note found at C:\ransom_note.txt."
```

**Bad:**
```
"Computer infected"
```

**Tips:**
- Include timestamp (when incident occurred)
- Specify system type (Windows/Linux, version)
- Mention specific indicators (file extensions, processes, IPs)
- Provide file paths or hostnames

### 2. Analysis Goals

**Good:**
```
"Identify the ransomware process name, parent process, C2 server IP, 
and encryption method used"
```

**Bad:**
```
"Find the problem"
```

**Tips:**
- Be specific about what you're looking for
- List multiple objectives if needed
- Mention IOC types of interest (IPs, domains, hashes)
- Specify scope (network activity, file system, memory)

### 3. Workflow Efficiency

- **Save reports:** Always use `-o` to save reports for documentation
- **Use verbose mode during investigation:** `-v` helps understand tool selection
- **Start broad, then narrow:** Initial analysis → Targeted re-analysis
- **Chain findings:** Use IOCs from first analysis to inform second

**Example Chain:**
```bash
# Step 1: Initial triage
find-evil analyze "Unknown binary detected" "Identify file type and strings" -o step1.md

# Step 2: Deep analysis (using hash from step1.md)
find-evil analyze "Binary hash: a3f8b9c2..." "Analyze PE structure and imports" -o step2.md

# Step 3: Network analysis (using C2 IP from step2.md)
find-evil analyze "Binary contacts 203.0.113.42" "Identify C2 protocol and beaconing" -o step3.md
```

### 4. Security Considerations

- **Never analyze evidence on production systems** - Use dedicated SIFT VM
- **Work on copies** - Never run tools on original evidence
- **Validate SSH keys** - Ensure proper key permissions (600)
- **Review reports before sharing** - May contain sensitive data
- **Monitor LLM costs** - OpenAI/Anthropic APIs charge per token

### 5. Observability

Enable Langfuse for:
- Tool selection reasoning visualization
- LLM prompt/response inspection
- Workflow debugging
- Performance metrics

Access Langfuse dashboard:
```
http://localhost:33000
```

Filter by:
- Session ID (shown in verbose output)
- Tool name
- Timestamp
- Error status

---

## Advanced Usage

### Custom Tool Metadata

Add custom SIFT tools to `tools/metadata.yaml`:

```yaml
- name: custom_tool
  category: network_analysis
  description: "Custom tool for specialized analysis"
  requires_evidence: true
  inputs:
    - name: pcap_file
      type: file
      required: true
  output_format: json
```

Rebuild embeddings cache:
```bash
rm -rf .cache/embeddings/
find-evil analyze ...  # Will regenerate on first run
```

### Programmatic Usage

Use Find Evil Agent in Python code:

```python
from find_evil_agent.agents.orchestrator import OrchestratorAgent
from find_evil_agent.agents.schemas import AgentContext
import asyncio

async def analyze_incident():
    orchestrator = OrchestratorAgent()
    
    context = AgentContext(
        incident_description="Ransomware detected",
        analysis_goal="Find malicious process"
    )
    
    result = await orchestrator.process(context)
    
    if result.success:
        print(f"Findings: {result.data['findings']}")
        print(f"IOCs: {result.data['iocs']}")
    else:
        print(f"Error: {result.error}")

asyncio.run(analyze_incident())
```

---

## Getting Help

**Documentation:**
- User Guide (this document)
- [System Description](SYSTEM_DESCRIPTION.md) - Architecture details
- [Admin Guide](ADMIN_GUIDE.md) - Deployment and monitoring

**Support:**
- GitHub Issues: https://github.com/iffystrayer/find-evil-agent/issues
- Hackathon Discord: [FIND EVIL! Discord](https://discord.gg/findevil)

**Logs:**
- Application logs: Check stdout (or use `-v`)
- SSH logs: `~/.ssh/known_hosts` and SSH debug mode
- LLM traces: Langfuse dashboard (if enabled)

---

**Last Updated:** April 10, 2026  
**Version:** 0.1.0
