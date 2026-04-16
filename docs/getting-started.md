# Getting Started

This guide will help you install and configure Find Evil Agent for forensic analysis.

## Prerequisites

### Required

- **Python 3.11+** (tested with 3.13)
- **SANS SIFT Workstation** with SSH access
- **LLM Provider:** Ollama (free, local) OR OpenAI OR Anthropic

### Recommended

- **uv** for Python package management: `pip install uv`
- **SSH key** configured for SIFT VM access
- **16GB+ RAM** for running local LLM models

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/iffystrayer/find-evil-agent.git
cd find-evil-agent
```

### Step 2: Create Virtual Environment

=== "Using uv (recommended)"
    ```bash
    uv venv
    source .venv/bin/activate  # Linux/Mac
    # or: .venv\Scripts\activate  # Windows
    ```

=== "Using standard venv"
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/Mac
    # or: .venv\Scripts\activate  # Windows
    ```

### Step 3: Install Dependencies

=== "Using uv"
    ```bash
    uv pip install -e ".[dev]"
    ```

=== "Using pip"
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

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

#### LLM Provider Configuration

=== "Ollama (Free, Local)"
    ```bash
    LLM_PROVIDER=ollama
    LLM_MODEL_NAME=gemma4:31b-cloud
    OLLAMA_BASE_URL=http://localhost:11434
    ```
    
    Install Ollama:
    ```bash
    # Mac
    brew install ollama
    
    # Linux
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Pull model
    ollama pull gemma4:31b-cloud
    
    # Start Ollama server
    ollama serve
    ```

=== "OpenAI"
    ```bash
    LLM_PROVIDER=openai
    LLM_MODEL_NAME=gpt-4
    OPENAI_API_KEY=sk-...
    ```
    
    Get API key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

=== "Anthropic"
    ```bash
    LLM_PROVIDER=anthropic
    LLM_MODEL_NAME=claude-3-opus-20240229
    ANTHROPIC_API_KEY=sk-ant-...
    ```
    
    Get API key from [console.anthropic.com](https://console.anthropic.com)

#### SIFT VM Configuration

```bash
SIFT_VM_HOST=192.168.12.101
SIFT_VM_PORT=22
SIFT_SSH_USER=sansforensics
SIFT_SSH_KEY_PATH=/path/to/ssh/key  # Optional, uses ~/.ssh/id_rsa by default
```

!!! warning "SIFT VM Required"
    Find Evil Agent requires a running SANS SIFT Workstation with SSH access. See [SIFT VM Setup](deployment/sift-setup.md) for installation instructions.

#### Tool Selection Configuration

```bash
# Minimum confidence for tool selection (0.0-1.0)
TOOL_CONFIDENCE_THRESHOLD=0.7

# Number of semantic search candidates
SEMANTIC_SEARCH_TOP_K=10

# Tool execution timeout (seconds)
DEFAULT_TOOL_TIMEOUT=60
MAX_TOOL_TIMEOUT=3600
```

#### Observability (Optional)

```bash
# Langfuse configuration
LANGFUSE_ENABLED=true
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=http://localhost:33000

# Prometheus metrics
PROMETHEUS_ENABLED=false
PROMETHEUS_PORT=60090
```

### SSH Key Setup

Generate SSH key for SIFT VM access:

```bash
# Generate key
ssh-keygen -t ed25519 -f ~/.ssh/sift_vm_key -C "find-evil-agent"

# Copy public key to SIFT VM
ssh-copy-id -i ~/.ssh/sift_vm_key sansforensics@192.168.12.101

# Test connection
ssh -i ~/.ssh/sift_vm_key sansforensics@192.168.12.101 hostname
```

!!! tip "SSH Key Permissions"
    Ensure your SSH key has correct permissions:
    ```bash
    chmod 600 ~/.ssh/sift_vm_key
    chmod 644 ~/.ssh/sift_vm_key.pub
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

## Quick Start

### Basic Analysis

Analyze an incident by providing:

1. **Incident description** - What happened
2. **Analysis goal** - What you want to find

```bash
find-evil analyze \
  "Ransomware detected on Windows 10 endpoint at 2026-04-10 14:30" \
  "Identify malicious processes and network connections"
```

### Output Example

```
🔍 Starting Analysis...

📋 Incident: Ransomware detected on Windows 10 endpoint
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

### Save Report to File

```bash
find-evil analyze \
  "Suspicious PowerShell execution" \
  "Find script content and parent process" \
  --output report.md
```

### Verbose Mode

```bash
find-evil analyze \
  "Data exfiltration detected" \
  "Identify destination IPs and transferred files" \
  --verbose
```

### Autonomous Investigation

Use the `investigate` command for multi-iteration autonomous analysis:

```bash
find-evil investigate \
  "Unknown process consuming high CPU" \
  "Identify the process, determine if malicious, and trace origin" \
  --max-iterations 3 \
  --output investigation.md \
  --verbose
```

!!! success "Feature #2: Autonomous Investigation"
    The agent will automatically:
    
    1. Run initial analysis
    2. Extract investigative leads from findings
    3. Follow highest-priority leads
    4. Repeat until max iterations or no leads remain
    5. Synthesize complete investigation narrative

## Common Workflows

### Ransomware Investigation

```bash
find-evil analyze \
  "Ransomware encrypted files on fileserver at 2026-04-10 02:15 UTC" \
  "Identify ransomware process, encryption method, and C2 communication" \
  -o ransomware_report.md -v
```

### Malware Binary Analysis

```bash
find-evil analyze \
  "Unknown binary downloaded from phishing email: malware.exe" \
  "Extract strings, identify packing, find network indicators" \
  -o malware_analysis.md
```

### Network Intrusion

```bash
find-evil analyze \
  "IDS alert: Port scan detected from 198.51.100.10 targeting internal network" \
  "Identify scan pattern, targeted ports, and lateral movement" \
  -o network_intrusion.md
```

### APT Investigation (Multi-Iteration)

```bash
find-evil investigate \
  "Suspected APT activity with lateral movement indicators" \
  "Map complete attack timeline from initial compromise to current state" \
  --max-iterations 7 \
  -o apt_timeline.md -v
```

## Next Steps

- [Configuration Guide](configuration.md) - Detailed configuration options
- [Usage Guide](usage.md) - Advanced usage patterns
- [Understanding Results](results.md) - Interpreting findings and IOCs
- [API Reference](api/cli.md) - Complete CLI command reference
- [Deployment Guide](deployment/sift-setup.md) - SIFT VM setup and security

## Troubleshooting

### SSH Connection Failed

**Error:**
```
❌ Error: Failed to connect to SIFT VM at 192.168.12.101:22
```

**Solutions:**

- Verify SIFT VM is running: `ping 192.168.12.101`
- Test SSH manually: `ssh sansforensics@192.168.12.101`
- Check SSH key permissions: `chmod 600 ~/.ssh/sift_vm_key`
- Verify `.env` has correct `SIFT_VM_HOST`, `SIFT_VM_PORT`, `SIFT_SSH_USER`

### LLM Provider Connection Failed

**Error:**
```
❌ Error: Failed to connect to Ollama at http://localhost:11434
```

**Solutions:**

- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Verify model is pulled: `ollama list`
- Pull model if missing: `ollama pull gemma4:31b-cloud`
- Check `.env` has correct `OLLAMA_BASE_URL`

For more troubleshooting help, see [Troubleshooting Guide](troubleshooting.md).
