# Find Evil Agent - MCP Server

Model Context Protocol server exposing Find Evil Agent's forensic analysis capabilities to AI clients.

## Overview

The MCP server provides **5 tools**, **2 resources**, and **2 prompts** for AI-assisted forensic investigation:

### Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `analyze_evidence` | Single-shot forensic analysis | incident_description, analysis_goal, evidence_path |
| `investigate` | Autonomous iterative investigation | incident_description, analysis_goal, max_iterations |
| `list_tools` | List available SIFT tools | category (optional) |
| `select_tool` | Hallucination-resistant tool selection | incident_description, analysis_goal, top_k |
| `get_config` | Get current configuration | (none) |

### Resources

| URI | Content | Description |
|-----|---------|-------------|
| `tools://registry` | JSON | Complete tool registry with metadata (18+ tools) |
| `config://settings` | JSON | Current configuration settings |

### Prompts

| Prompt | Purpose | Parameters |
|--------|---------|------------|
| `memory_analysis` | Memory forensics workflow template | evidence_file |
| `disk_triage` | Disk image investigation template | disk_image |

## Usage

### Run as Stdio Server (Claude Code, Claude Desktop)

```bash
python -m find_evil_agent.mcp.server
```

### Run as HTTP Server (Remote Clients)

```bash
python -m find_evil_agent.mcp.server --http --port 16790 --host 127.0.0.1
```

### Configure in Claude Code

Add to your MCP settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "find-evil-agent": {
      "command": "python",
      "args": ["-m", "find_evil_agent.mcp.server"],
      "env": {
        "SIFT_VM_HOST": "192.168.12.101",
        "SIFT_VM_PORT": "22",
        "LLM_PROVIDER": "ollama",
        "LLM_MODEL_NAME": "gemma4:31b-cloud"
      }
    }
  }
}
```

### Configure in Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "find-evil-agent": {
      "command": "python3",
      "args": ["-m", "find_evil_agent.mcp.server"],
      "env": {
        "SIFT_VM_HOST": "192.168.12.101"
      }
    }
  }
}
```

## Example Usage

### Analyze Evidence

```
User: Use find-evil-agent to analyze suspicious process activity

Claude: I'll use the analyze_evidence tool...

[Calls analyze_evidence tool with appropriate parameters]

Result:
✅ Analysis Complete
Tool Selected: volatility (Confidence: 0.92)
Findings: 3 critical, 2 high severity
IOCs: 5 IPs, 2 domains, 3 hashes
```

### Autonomous Investigation

```
User: Investigate the ransomware incident - follow all leads

Claude: I'll use the investigate tool for autonomous analysis...

[Calls investigate tool with max_iterations=5]

Result:
🔄 Investigation Complete (3 iterations)
Tools Used: volatility → log2timeline → log2timeline  
Total Findings: 9
Investigation Summary: [Complete attack chain from entry to encryption]
```

## Key Features

### 1. Hallucination-Resistant Tool Selection

Two-stage validation prevents LLM from inventing tools:
- **Semantic Search** (FAISS) → top-10 real tools
- **LLM Ranking** → best tool with confidence
- **Threshold** (≥0.7) → reject uncertain selections

### 2. Autonomous Iterative Investigation

Agent automatically follows leads without human intervention:
- Extract leads from findings
- Prioritize (HIGH > MEDIUM > LOW)
- Follow highest-confidence lead
- Repeat until complete

### 3. Professional IOC Extraction

Automatically extracts indicators from tool output:
- IPs (IPv4/IPv6)
- Domains (FQDNs)
- Hashes (MD5, SHA1, SHA256)
- File paths (Unix/Windows)
- Emails, URLs

## Architecture

```
AI Client (Claude Code, Claude Desktop)
    ↓ (MCP Protocol)
FastMCP Server (this module)
    ↓
OrchestratorAgent → ToolSelector → ToolExecutor → Analyzer
    ↓
SIFT VM (SSH)
```

## Security

- **Command Validation**: Blocks destructive patterns (rm -rf, dd, curl)
- **SSH Key Auth**: No password prompts
- **Timeout Enforcement**: 60s default, 3600s max
- **Confidence Threshold**: Rejects low-confidence tool selections

## Requirements

- Python 3.11+
- MCP SDK (`mcp>=1.0.0`)
- Find Evil Agent dependencies
- SIFT VM with SSH access
- LLM provider (Ollama, OpenAI, or Anthropic)

## Testing

```bash
# Verify server initialization
python -c "from find_evil_agent.mcp.server import mcp; print(f'Tools: {len(mcp._tool_manager._tools)}')"

# Test help
python -m find_evil_agent.mcp.server --help

# Run server (stdio)
python -m find_evil_agent.mcp.server

# Run server (HTTP)
python -m find_evil_agent.mcp.server --http --port 16790
```

## Troubleshooting

### Server won't start

```bash
# Check Python version
python --version  # Must be 3.11+

# Check MCP SDK installed
python -c "import mcp; print(mcp.__version__)"

# Check dependencies
pip install -e ".[dev]"
```

### Tools not showing in client

- Verify MCP server is running (check logs)
- Restart AI client after configuration changes
- Check `~/.claude/settings.json` for correct paths

### Analysis failures

- Verify SIFT VM is accessible: `ssh user@192.168.12.101`
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Review `.env` configuration

## Development

See [SWE_SPECIFICATION.md](../../../../SWE_SPECIFICATION.md) Section 6.3 for complete MCP server specification and future enhancements.

## License

MIT - See [LICENSE](../../../../LICENSE) for details.
