# MCP Server Reference

Model Context Protocol server exposing Find Evil Agent's forensic analysis capabilities to AI clients (Claude Code, Claude Desktop, etc.).

## Overview

The MCP server provides **5 tools**, **2 resources**, and **2 prompts** for AI-assisted forensic investigation.

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

## Running the Server

### Stdio Mode (Claude Code, Claude Desktop)

```bash
python -m find_evil_agent.mcp.server
```

### HTTP Mode (Remote Clients)

```bash
python -m find_evil_agent.mcp.server --http --port 16790 --host 127.0.0.1
```

## Configuration

### Claude Code

Add to `~/.claude/settings.json`:

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

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac):

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

## Tool Reference

### analyze_evidence

Run single-shot forensic analysis on SIFT VM.

**Parameters:**

- `incident_description` (string, required): Description of the security incident
- `analysis_goal` (string, required): What you want to analyze or discover
- `evidence_path` (string, optional): Path to evidence file on SIFT VM

**Returns:**

Analysis report with tool selected, findings, and IOCs extracted.

**Example:**

```
User: Use find-evil-agent to analyze suspicious process activity

Claude: I'll use the analyze_evidence tool...

Result:
✅ Analysis Complete
Tool Selected: volatility (Confidence: 0.92)
Findings: 3 critical, 2 high severity
IOCs: 5 IPs, 2 domains, 3 hashes
```

### investigate

Run autonomous iterative investigation - follows leads automatically.

**Parameters:**

- `incident_description` (string, required): Description of the security incident
- `analysis_goal` (string, required): Investigation goal
- `max_iterations` (int, optional): Maximum analysis iterations (default: 5)
- `min_lead_confidence` (float, optional): Minimum confidence for leads (default: 0.6)

**Returns:**

Investigation report with all iterations, tools used, findings, and synthesis.

**Example:**

```
User: Investigate the ransomware incident - follow all leads

Claude: I'll use the investigate tool for autonomous analysis...

Result:
🔄 Investigation Complete (3 iterations)
Tools Used: volatility → log2timeline → log2timeline
Total Findings: 9
Investigation Summary: [Complete attack chain from entry to encryption]
```

### list_tools

List available SIFT forensic tools.

**Parameters:**

- `category` (string, optional): Category filter (memory, disk, timeline, network, analysis)

**Returns:**

List of tools with descriptions grouped by category.

### select_tool

Select best forensic tool using hallucination-resistant selection.

**Parameters:**

- `incident_description` (string, required): Description of the security incident
- `analysis_goal` (string, required): What you want to analyze
- `top_k` (int, optional): Number of candidates from semantic search (default: 10)

**Returns:**

Tool selection with confidence score and reasoning.

### get_config

Get current Find Evil Agent configuration.

**Returns:**

Configuration status including LLM provider, SIFT VM, tools available.

## Resources

### tools://registry

Complete tool registry with metadata for all 18+ SIFT tools.

**Format:** JSON

**Content:**

```json
[
  {
    "name": "volatility",
    "category": "memory_analysis",
    "description": "Memory forensics framework...",
    "requires_evidence": true,
    "inputs": [...],
    "output_format": "text"
  },
  ...
]
```

### config://settings

Current configuration settings.

**Format:** JSON

**Content:**

```json
{
  "llm_provider": "ollama",
  "llm_model_name": "gemma4:31b-cloud",
  "sift_vm_host": "192.168.12.101",
  "sift_vm_port": 22,
  "tool_confidence_threshold": 0.7,
  "semantic_search_top_k": 10
}
```

## Prompts

### memory_analysis

Template for memory forensics analysis workflow.

**Parameters:**

- `evidence_file` (string): Path to memory dump file

**Returns:**

Prompt template guiding through memory analysis steps.

### disk_triage

Template for disk image investigation workflow.

**Parameters:**

- `disk_image` (string): Path to disk image file

**Returns:**

Prompt template guiding through disk triage steps.

## Security

- **Command Validation:** Blocks destructive patterns (rm -rf, dd, curl)
- **SSH Key Auth:** No password prompts
- **Timeout Enforcement:** 60s default, 3600s max
- **Confidence Threshold:** Rejects low-confidence tool selections

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

## Testing

```bash
# Verify server initialization
python -c "from find_evil_agent.mcp.server import mcp; print(f'Tools: {len(mcp._tool_manager._tools)}')"

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

## Next Steps

- [CLI Reference](cli.md) - Command-line interface
- [REST API Reference](rest.md) - HTTP API
- [Python API Reference](python.md) - Programmatic usage
