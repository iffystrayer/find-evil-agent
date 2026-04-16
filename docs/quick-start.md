# Quick Start

Get up and running with Find Evil Agent in 5 minutes.

## Prerequisites

- Python 3.11+
- SANS SIFT Workstation (VM with SSH access)
- Ollama (or OpenAI/Anthropic API key)

## 5-Minute Setup

### 1. Install

```bash
git clone https://github.com/iffystrayer/find-evil-agent.git
cd find-evil-agent
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# LLM Provider
LLM_PROVIDER=ollama
LLM_MODEL_NAME=gemma4:31b-cloud
OLLAMA_BASE_URL=http://localhost:11434

# SIFT VM
SIFT_VM_HOST=192.168.12.101
SIFT_VM_PORT=22
SIFT_SSH_USER=sansforensics
```

### 3. Setup SSH

```bash
ssh-keygen -t ed25519 -f ~/.ssh/sift_vm_key
ssh-copy-id -i ~/.ssh/sift_vm_key sansforensics@192.168.12.101
```

### 4. Verify

```bash
find-evil config
```

Expected: ✅ All systems operational

### 5. Run First Analysis

```bash
find-evil analyze \
  "Suspicious process detected on Windows 10" \
  "Identify process details and network connections" \
  -o report.md -v
```

## Example Workflows

### Ransomware Investigation

```bash
find-evil analyze \
  "Ransomware encrypted files at 2026-04-10 14:30" \
  "Identify ransomware process and C2 server" \
  -o ransomware.md
```

### Autonomous Investigation

```bash
find-evil investigate \
  "Unknown process consuming high CPU" \
  "Identify and trace origin" \
  --max-iterations 3 \
  -o investigation.md -v
```

## What's Next?

- [Full Installation Guide](getting-started.md)
- [Configuration Options](configuration.md)
- [API Reference](api/cli.md)
- [Architecture Overview](architecture.md)

## Troubleshooting

### SSH Failed

```bash
# Test connection
ssh -i ~/.ssh/sift_vm_key sansforensics@192.168.12.101

# Fix permissions
chmod 600 ~/.ssh/sift_vm_key
```

### LLM Connection Failed

```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Pull model
ollama pull gemma4:31b-cloud
```

### Low Confidence

Add more detail to incident description:

- Include timestamps
- Specify IP addresses
- Mention file names
- Add system details

## Getting Help

- [Documentation](index.md)
- [GitHub Issues](https://github.com/iffystrayer/find-evil-agent/issues)
- [Troubleshooting Guide](troubleshooting.md)
