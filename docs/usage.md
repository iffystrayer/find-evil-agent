# Usage Guide

Comprehensive guide to using Find Evil Agent across all interfaces.

## Overview

Find Evil Agent provides four interfaces for incident response:

1. **CLI** - Command-line interface for power users and automation
2. **Web UI** - Modern React interface for interactive analysis
3. **REST API** - HTTP API for programmatic access
4. **MCP Server** - Model Context Protocol for Claude integration

## CLI Interface

### Basic Commands

#### Analysis Mode

Single-shot analysis with automatic tool selection:

```bash
find-evil analyze \
  "Suspicious network traffic to 185.220.101.42" \
  "Identify malicious processes and C2 communication" \
  -o report.md \
  --verbose
```

**Options:**
- `-o, --output PATH` - Output file path (default: stdout)
- `-v, --verbose` - Show detailed progress
- `--provider TEXT` - LLM provider (ollama/openai/anthropic)
- `--model TEXT` - Specific model to use
- `--confidence FLOAT` - Minimum confidence threshold (default: 0.7)
- `--timeout INT` - Tool execution timeout in seconds (default: 60)

#### Investigation Mode

Autonomous multi-iteration investigation:

```bash
find-evil investigate \
  "Unknown process 'cryptominer.exe' consuming high CPU" \
  "Identify origin, C2 servers, and lateral movement" \
  --max-iterations 5 \
  -o investigation.md \
  --verbose
```

**Options:**
- `--max-iterations INT` - Maximum investigation cycles (default: 3, max: 10)
- All options from `analyze` command

### Advanced Usage

#### Custom LLM Provider

```bash
# Use OpenAI
find-evil analyze "..." "..." --provider openai --model gpt-4

# Use Anthropic Claude
find-evil analyze "..." "..." --provider anthropic --model claude-3-5-sonnet-20241022

# Use local Ollama
find-evil analyze "..." "..." --provider ollama --model llama3:70b
```

#### Pipeline Integration

```bash
# Run analysis and extract IOCs
find-evil analyze "..." "..." -o report.json --format json | \
  jq '.iocs[] | select(.type=="ip")' > ips.txt
```

## Web UI

### Accessing the Interface

```bash
# Using Docker (recommended)
docker-compose up -d

# Access at: http://localhost:15173
```

### Single Analysis Tab

1. **Incident Description** - Describe the security incident
2. **Analysis Goal** - What you want to discover
3. **LLM Provider** - Choose provider (Ollama/OpenAI/Anthropic)
4. **Model** - Select specific model
5. **Click Analyze** - Start analysis

### Investigation Tab

For autonomous multi-iteration analysis - set max iterations (2-10) and click "Start Investigation".

## REST API

### Starting the API Server

```bash
uvicorn find_evil_agent.api.server:app --host 0.0.0.0 --port 18000
```

### Endpoints

#### POST /api/v1/analyze

```bash
curl -X POST http://localhost:18000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "incident_description": "Suspicious process connecting to 185.220.101.42",
    "analysis_goal": "Identify malicious activity",
    "provider": "ollama",
    "model": "llama3:8b"
  }'
```

#### POST /api/v1/investigate

```bash
curl -X POST http://localhost:18000/api/v1/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "incident_description": "Ransomware detected",
    "analysis_goal": "Complete attack chain analysis",
    "max_iterations": 5
  }'
```

See [REST API Reference](api/rest.md) for complete documentation.

## MCP Server

### Starting the Server

```bash
find-evil mcp-server
```

### Claude Desktop Integration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "find-evil": {
      "command": "find-evil",
      "args": ["mcp-server"]
    }
  }
}
```

See [MCP Server Reference](api/mcp.md) for 12 available tools.

## Best Practices

**Specific Descriptions Work Best:**
```
✅ Good: "Suspicious outbound connections from svchost.exe to 185.220.101.42:443"
❌ Poor: "Something wrong with network"
```

**Clear Goals:**
```
✅ Good: "Identify C2 communication patterns and extract domains"
❌ Poor: "Check if bad"
```

## Common Workflows

### Malware Analysis

```bash
# Initial triage
find-evil analyze \
  "Unknown binary at /tmp/malware.exe" \
  "Identify file type and initial indicators"

# Deep investigation
find-evil investigate \
  "Malware /tmp/malware.exe identified as trojan" \
  "Complete behavioral analysis and IOC extraction" \
  --max-iterations 5
```

### Network Forensics

```bash
# Analyze suspicious traffic
find-evil analyze \
  "PCAP file shows suspicious DNS queries" \
  "Extract domains and identify C2 traffic"
```

## Next Steps

- [Configuration Guide](configuration.md) - Configure LLM providers and SIFT VM
- [API Reference](api/cli.md) - Complete CLI command reference
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
