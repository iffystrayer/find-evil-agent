# Frequently Asked Questions

## General Questions

### What is Find Evil Agent?

Find Evil Agent is an autonomous AI-powered incident response agent that runs on the SANS SIFT Workstation. It uses LLMs (Large Language Models) to automatically select and execute forensic tools, extract IOCs, and generate professional incident response reports.

### What makes it unique?

Two groundbreaking features:

1. **Hallucination-Resistant Tool Selection** - Two-stage validation (semantic search + LLM ranking) prevents the agent from selecting non-existent or inappropriate tools
2. **Autonomous Investigative Reasoning** - Multi-iteration workflow that automatically follows leads without analyst intervention

### Who should use Find Evil Agent?

- **Digital forensic analysts** - Automate routine investigations
- **Incident responders** - Faster triage and analysis
- **Security operations teams** - Reduce analyst workload
- **DFIR students** - Learn forensic workflows

### Is it production-ready?

Find Evil Agent is a hackathon project demonstrating novel AI capabilities in DFIR. While functional and tested (462 tests), it requires additional hardening for production use in critical environments.

## Installation & Setup

### What are the system requirements?

**Minimum:**
- Python 3.11+
- 4GB RAM
- SANS SIFT Workstation VM
- LLM provider (Ollama/OpenAI/Anthropic)

**Recommended:**
- Python 3.13
- 8GB RAM
- Local Ollama with 8B parameter model
- SSH key-based authentication

### Why do I need a SIFT VM?

Find Evil Agent executes forensic tools on the SIFT VM via SSH to maintain evidence integrity and security. The tools (strings, fls, volatility, etc.) are pre-installed on SIFT.

### Can I use it without SIFT?

Not currently. The agent is designed specifically for SIFT Workstation integration. However, the architecture could be adapted for other forensic platforms.

### Which LLM provider should I use?

**For Development:**
- Ollama (local) - Free, private, fast for testing

**For Production:**
- OpenAI GPT-4 - Best quality, costs apply
- Anthropic Claude 3.5 - Excellent reasoning, costs apply

**For Hackathon Demo:**
- Ollama with llama3:8b or gemma2:27b - Good balance

### How do I get SSH access to SIFT VM?

1. Download SIFT VM from https://www.sans.org/tools/sift-workstation/
2. Import into VirtualBox/VMware
3. Generate SSH key: `ssh-keygen -t ed25519`
4. Copy to SIFT: `ssh-copy-id sansforensics@<sift-ip>`
5. Configure in `.env`: `SIFT_VM_HOST=<sift-ip>`

## Usage Questions

### How long does an analysis take?

**Single Analysis:**
- Tool selection: 10-30 seconds (depends on LLM)
- Execution: 0.1-5 seconds (depends on tool)
- Analysis: 10-20 seconds (LLM processing)
- **Total: 30-60 seconds**

**Investigation (3 iterations):**
- **Total: 45-90 seconds**

### What if the confidence score is low?

If confidence < 0.7 (default threshold):

1. **Improve description** - Be more specific
2. **Lower threshold** - Use `--confidence 0.6` if appropriate
3. **Manual selection** - If you know the right tool, use REST API to execute directly

### How accurate is tool selection?

In testing with specific incident descriptions, tool selection accuracy is **~90%** when incidents clearly describe forensic needs. Vague descriptions reduce accuracy to ~60-70%.

### Can it analyze multiple evidence files?

Not currently in a single run. You can:
- Run separate analyses for each file
- Use investigation mode to follow leads across files
- Build a pipeline with the Python API

### Does it modify evidence?

No. All SIFT tool executions are read-only. Commands that could modify evidence (rm, dd, etc.) are blocked by security validation.

## Technical Questions

### How does two-stage tool selection work?

**Stage 1: Semantic Search**
- Incident description → embeddings (SentenceTransformers)
- FAISS search → top 10 candidate tools

**Stage 2: LLM Ranking**
- LLM reviews candidates + incident
- Selects best tool with confidence score
- Returns reasoning for selection

Only proceeds if confidence ≥ threshold (default 0.7).

### What forensic tools are supported?

18 SIFT tools currently:
- File system: fls, icat, fsstat
- Analysis: strings, grep, file
- Network: netstat, tcpdump
- Memory: volatility
- Timeline: log2timeline, plaso
- And more...

See complete list: `find-evil tools list`

### How does autonomous investigation work?

1. Run initial analysis
2. Extract leads from findings (LLM + rules)
3. Select next tool based on highest priority lead
4. Execute and analyze
5. Repeat for N iterations or until no leads

Example: Malware → strings → grep suspicious domains → tcpdump on pcap → timeline analysis

### Can I add custom tools?

Yes! Extend the ToolRegistry:

```python
from find_evil_agent.tools.registry import ToolRegistry

registry = ToolRegistry()
registry.register_tool(
    name="custom_tool",
    description="...",
    command_template="custom_tool {args}",
    category="custom"
)
```

### How is observability implemented?

- **Langfuse** - LLM tracing and analytics
- **Prometheus** - Metrics collection
- **Structlog** - Structured JSON logging

All optional, enable in `.env`.

### Is the code open source?

Yes, MIT license. See GitHub repository.

## Integration Questions

### Can I integrate with SIEM/SOAR?

Yes, via REST API:

```bash
# From SIEM alert
curl -X POST http://localhost:18000/api/v1/analyze \
  -d '{"incident_description": "$ALERT", "analysis_goal": "Triage"}'
```

### Does it work with Claude Desktop?

Yes! Via MCP Server integration:

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

### Can I use it programmatically?

Yes, three ways:

1. **Python API** - Import and use classes directly
2. **REST API** - HTTP endpoints
3. **CLI** - Shell commands in scripts

See [Python API](api/python.md) and [REST API](api/rest.md).

### How do I deploy in production?

1. **Docker Compose** (recommended)
   ```bash
   docker-compose up -d
   ```

2. **Kubernetes** - YAML configs available

3. **Systemd service** - For CLI usage

See [Deployment Guide](deployment/sift-setup.md).

## Security Questions

### Is it secure?

Security features:
- ✅ SSH key authentication only
- ✅ Command injection prevention
- ✅ Dangerous command blocklist
- ✅ Configurable timeouts
- ✅ Read-only operations
- ✅ No API keys in code

See [Security Guide](deployment/security.md) for details.

### What commands are blocked?

Dangerous operations blocked:
- `rm -rf` - File deletion
- `dd` - Disk writes
- `mkfs` - Filesystem creation
- `curl`/`wget` - Network downloads
- And more...

Full list in security validation code.

### Can it access the internet?

Only if SIFT VM has internet access. The agent itself doesn't make external connections except to LLM APIs (OpenAI/Anthropic) if configured.

### How are API keys stored?

Environment variables only. Never in:
- Code
- Git repository
- Logs
- Reports

## Troubleshooting

### "SSH connection failed"

**Check:**
1. SIFT VM is running: `ping <sift-ip>`
2. SSH works manually: `ssh sansforensics@<sift-ip>`
3. Key permissions: `chmod 600 ~/.ssh/sift_vm`
4. Firewall allows port 22

### "Tool selection confidence too low"

**Fix:**
1. Be more specific in incident description
2. Include technical details (IPs, file paths, process names)
3. Clearly state analysis goal
4. Lower threshold: `--confidence 0.6`

### "Command timeout"

**Fix:**
1. Increase timeout: `--timeout 300`
2. Check SIFT VM resources: `ssh ... "top"`
3. Use faster LLM model
4. Split into multiple analyses

### "No IOCs found"

**Causes:**
- Tool output has no IOCs (normal for some tools)
- LLM failed to extract (check verbose output)
- Wrong tool selected (improve description)

**Fix:**
Run with `--verbose` to see raw tool output.

See [Troubleshooting Guide](troubleshooting.md) for more.

## Performance

### How can I make it faster?

1. **Use local Ollama** - No network latency
2. **Smaller LLM models** - llama3:8b vs llama3:70b
3. **SSH connection pooling** - Reuse connections
4. **Lower confidence threshold** - Accept faster decisions
5. **Limit iterations** - 3 instead of 10

### What's the bottleneck?

LLM inference time (10-30s per call). Using local Ollama with GPU acceleration helps significantly.

### Can I run analyses in parallel?

Yes, via Python API:

```python
import asyncio

async def parallel_analysis():
    tasks = [
        orchestrator.analyze(incident1, goal1),
        orchestrator.analyze(incident2, goal2),
        orchestrator.analyze(incident3, goal3)
    ]
    results = await asyncio.gather(*tasks)
```

## Hackathon-Specific

### What hackathon is this for?

[FIND EVIL! Hackathon](https://findevil.devpost.com) by Sublte
- **Timeline:** April 15 - June 15, 2026
- **Prize Pool:** $22,000

### Where's the demo?

Demo materials in `.archive/demo_materials/`:
- Playwright recordings
- CLI demo output
- API demo output
- Screenshots and videos

### How do I submit?

1. **Video** - Use demo_recording.webm
2. **Description** - Highlight two unique features
3. **Screenshots** - 5 PNGs in demo_final/
4. **GitHub** - Link to this repository
5. **Try it** - Deploy instructions in README

### What are the judging criteria?

Per DevPost:
- Innovation
- Technical complexity
- Practical application
- Code quality
- Presentation

Our strengths:
- ✅ Two unique features (hallucination prevention + autonomous reasoning)
- ✅ 462 tests with comprehensive coverage
- ✅ Four interfaces (CLI/Web/API/MCP)
- ✅ Production-grade architecture
- ✅ Professional documentation

## Contributing

### How can I contribute?

1. **Report bugs** - GitHub Issues
2. **Suggest features** - GitHub Discussions
3. **Submit PRs** - Follow TDD methodology
4. **Improve docs** - Documentation PRs welcome
5. **Share use cases** - Help us understand real-world needs

### What's the development workflow?

1. Tests first (TDD)
2. Real integrations (no mocks)
3. uv for Python management
4. 5-digit ports only
5. Ollama for development

See CLAUDE.md for complete guidelines.

## Future Plans

### What's on the roadmap?

**Short-term:**
- Enhanced command building from schemas
- Streaming progress updates
- More SIFT tool integrations

**Medium-term:**
- Multi-evidence correlation
- MITRE ATT&CK auto-mapping
- Report templates library

**Long-term:**
- Agent collaboration (multiple agents working together)
- Evidence graph visualization
- Machine learning for tool selection

### Will there be commercial version?

No current plans. This is an open-source research project demonstrating AI capabilities in DFIR.

### Can I use it commercially?

Yes, MIT license allows commercial use. Attribute properly and see LICENSE file.

## Getting Help

### Where can I get support?

1. **Documentation** - Start here (you are here!)
2. **GitHub Issues** - Bug reports and feature requests
3. **GitHub Discussions** - Questions and community help
4. **Troubleshooting Guide** - Common issues
5. **Examples** - Real-world use cases

### How do I report a bug?

GitHub Issues with:
1. Description of problem
2. Steps to reproduce
3. Expected vs actual behavior
4. Environment details (OS, Python version, etc.)
5. Relevant logs (`--verbose` output)

### Is there a community?

Starting! Join via:
- GitHub Discussions
- Watch the repository for updates
- Star if you find it useful

---

**Still have questions?** Check the [documentation index](index.md) or open a [GitHub Issue](https://github.com/iffystrayer/find-evil-agent/issues).
