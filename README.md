# 🔍 Find Evil Agent

**Autonomous AI Incident Response Agent for SANS SIFT Workstation**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hackathon](https://img.shields.io/badge/FIND%20EVIL!-Hackathon-red.svg)](https://findevil.devpost.com)

> **Mission**: Minimize LLM hallucination in DFIR workflows through multi-agent validation and semantic tool selection.

## 🏆 Hackathon Submission

- **Event**: [FIND EVIL! Hackathon](https://findevil.devpost.com)
- **Timeline**: April 15 - June 15, 2026
- **Prize Pool**: $22,000

## 🚀 Key Differentiator

Unlike existing solutions, Find Evil Agent implements a **multi-agent LangGraph workflow** with mandatory tool confidence thresholds to minimize hallucination:

| Agent | Purpose | Key Feature |
|-------|---------|-------------|
| **Orchestrator** | Workflow entry point | Workflow path selection |
| **Tool Selector** | SIFT tool selection | Semantic search + confidence threshold (≥0.7) |
| **Executor** | Safe tool execution | Path validation + subprocess sandbox |
| **Analyzer** | Result interpretation | Anomaly detection + IOC matching |
| **Reporter** | Report generation | Structured IOC + timeline |
| **Memory** | Context management | LangGraph state persistence |

## 📁 Architecture

```
find-evil-agent/
├── src/find_evil_agent/
│   ├── agents/           # Multi-agent orchestration
│   │   ├── orchestrator.py    # Workflow entry
│   │   ├── tool_selector.py   # Semantic tool selection (CRITICAL)
│   │   ├── executor.py        # Safe subprocess execution
│   │   ├── analyzer.py        # Pattern detection
│   │   ├── reporter.py        # Report generation
│   │   └── memory.py          # State management
│   ├── tools/            # SIFT tool integration
│   │   ├── registry.py        # Tool catalog
│   │   ├── wrapper.py         # Safe execution
│   │   └── parser.py          # Output parsing
│   ├── mcp/              # Model Context Protocol
│   │   ├── server.py          # MCP server
│   │   └── client.py          # MCP client
│   ├── graph/            # LangGraph workflow
│   │   ├── workflow.py        # Graph definition
│   │   ├── state.py           # Shared state
│   │   ├── conditions.py      # Routing logic
│   │   └── checkpoint.py      # Persistence
│   ├── cli/              # Command-line interface
│   ├── config/           # Configuration management
│   └── telemetry/        # Observability
├── tests/                # Comprehensive test suite
│   ├── unit/
│   ├── integration/
│   └── benchmark/
└── docs/                 # Documentation
```

## 🔧 Quick Start

### Prerequisites

- Python 3.11+
- SANS SIFT Workstation (OVA ~15GB)
- MCP-compatible LLM (OpenAI, Anthropic, etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/iffystrayer/find-evil-agent.git
cd find-evil-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Usage

```bash
# Start interactive CLI
find-evil

# Analyze specific evidence
find-evil analyze --evidence /mnt/evidence/disk.raw --memory-only

# Start MCP server for integration
find-evil mcp-server --port 8080
```

## 🛡️ Security Features

| Threat | Mitigation |
|--------|------------|
| Shell Injection | NEVER use `shell=True`, pass args as list |
| Path Traversal | Whitelist allowed directories before execution |
| Evidence Corruption | Always work on copies, never originals |
| Tool Hallucination | Confidence threshold + semantic validation |
| Timeout Handling | Configurable timeouts with progress callbacks |

## 🧪 Development

### Testing

```bash
# Run all tests
pytest tests/ -q

# Run with coverage
pytest --cov=src/find_evil_agent --cov-report=html

# Run benchmarks
pytest tests/benchmark/ -v
```

### Linting

```bash
black src/ tests/
ruff check src/ tests/
mypy src/find_evil_agent
```

## 📊 Roadmap

- [x] Phase 0: Project structure and dependencies
- [ ] Phase 1: Foundation (starter code integration expected Apr 15)
- [ ] Phase 2: MCP bridge and tool discovery
- [ ] Phase 3: Agent implementation
- [ ] Phase 4: CLI and workflow
- [ ] Phase 5: Testing and documentation
- [ ] Phase 6: Demo video preparation

## 📚 Resources

- [Protocol SIFT](https://github.com/teamdfir/protocol-sift) - Reference implementation
- [Valhuntir](https://github.com/AppliedIR/Valhuntir) - Valhalla integration sub
- [SIFT Workstation](https://sans.org/tools/sift-workstation) - SANS DFIR tools

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- SANS Institute for the SIFT Workstation platform
- Sublte for the FIND EVIL! hackathon opportunity
- Open source DFIR community for tool documentation

---

**⚠️ Important**: This project is under active development for the FIND EVIL! hackathon. Starter code integration expected April 15, 2026.
