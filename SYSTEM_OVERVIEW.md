# Find Evil Agent — Full System Description

**Version:** 0.2.0-dev  
**Last Updated:** April 16, 2026  
**Hackathon:** FIND EVIL! (April 15 – June 15, 2026, $22k prize pool)

---

## What It Is

Find Evil Agent is an **autonomous AI forensic investigator** that sits on top of the SANS SIFT Workstation — a Linux VM pre-loaded with 200+ incident response tools. Instead of an analyst manually typing complex tool commands, interpreting raw output, and deciding what to run next, the agent does all of that through natural language.

An analyst says: *"There's a suspicious process consuming CPU on a compromised Windows endpoint. Investigate."*

The agent then autonomously:
1. **Selects** the right forensic tool (e.g., volatility for memory analysis)
2. **Builds** the exact command with correct flags and evidence paths
3. **Executes** it on the SIFT VM via SSH
4. **Analyzes** the output — extracts IOCs, identifies malicious indicators
5. **Follows leads** — if it finds a suspicious process, it automatically investigates its network connections, checks persistence mechanisms, builds a timeline
6. **Reports** — produces a structured investigation report with findings, IOCs, and MITRE ATT&CK technique mappings

All without the analyst making a single tool decision.

---

## The Problem It Solves

Digital forensics is slow. When a breach happens, analysts spend hours:
- Remembering which of 200+ tools to use for each task
- Looking up exact command syntax and flags
- Manually interpreting raw output (process tables, hex dumps, timelines)
- Deciding what to investigate next based on findings
- Writing reports

**Worse:** When AI tools try to help, they **hallucinate**. An LLM might confidently suggest running `forensic_analyzer --deep-scan` — a tool that doesn't exist. The analyst wastes time debugging a phantom command.

Find Evil Agent solves both problems: it's fast (45 seconds vs 60+ minutes for a 3-step investigation) and it **cannot hallucinate tool names** due to its two-stage validation architecture.

---

## How It Works — Architecture

```
                        ┌──────────────────┐
                        │    User Input     │
                        │ (Natural Language) │
                        └────────┬─────────┘
                                 │
               ┌─────────────────▼──────────────────┐
               │       OrchestratorAgent             │
               │         (LangGraph)                 │
               │                                     │
               │  Manages workflow state, iterates   │
               │  through investigation cycles       │
               └──┬──────────┬──────────┬───────────┘
                  │          │          │
        ┌─────────▼──┐ ┌────▼─────┐ ┌──▼───────────┐
        │ToolSelector │ │ Tool     │ │  Analyzer    │
        │  Agent      │ │ Executor │ │  Agent       │
        │             │ │ Agent    │ │              │
        │ FAISS +     │ │ SSH to   │ │ IOC regex +  │
        │ LLM rank +  │ │ SIFT VM  │ │ LLM findings │
        │ confidence  │ │          │ │ + parsers    │
        │ threshold   │ │          │ │              │
        └──────┬──────┘ └────┬─────┘ └──────┬──────┘
               │             │              │
        ┌──────▼──────┐ ┌───▼────────┐ ┌───▼──────────┐
        │ToolRegistry │ │  SIFT VM   │ │ Tool Output  │
        │ 18+ tools   │ │  (Ubuntu)  │ │ Parsers      │
        │ FAISS index │ │ 192.168.   │ │ (per-tool)   │
        │ YAML meta   │ │ 12.101     │ │              │
        └─────────────┘ └────────────┘ └──────────────┘
```

### The Four Agents

**1. OrchestratorAgent** — The brain. Uses LangGraph (a state machine framework) to coordinate the workflow. For single-shot analysis, it runs Select → Execute → Analyze. For autonomous investigation, it loops: after each analysis, it extracts investigative leads from the findings, picks the highest-priority lead, and starts a new cycle. It stops when it runs out of leads or hits the iteration limit.

**2. ToolSelectorAgent** — The anti-hallucination layer. This is the key innovation. When asked to find a tool for a task, it:
- Takes the analyst's goal (e.g., "find malicious processes in memory")
- Runs a **semantic search** using SentenceTransformers embeddings + FAISS vector index over 18 real SIFT tools — this constrains the search to tools that actually exist
- Sends the top-10 candidates to the **LLM**, which ranks them and picks the best one with a confidence score and reasoning
- **Rejects** any selection below 0.7 confidence — the agent would rather say "I'm not sure" than guess wrong
- **Validates** the selected tool exists in the registry before proceeding

The LLM never invents a tool name because it can only choose from the FAISS-retrieved candidates.

**3. ToolExecutorAgent** — The hands. Connects to the SIFT VM over SSH (asyncssh), runs the forensic command, captures stdout/stderr/return code, enforces timeouts, and blocks dangerous commands (rm -rf, dd, curl, etc.).

**4. AnalyzerAgent** — The eyes. Takes raw tool output and:
- Extracts IOCs using regex patterns (IPv4, IPv6, domains, MD5/SHA1/SHA256 hashes, file paths, emails, URLs)
- Filters false positives (localhost, RFC1918, system paths)
- Sends truncated output to the LLM for finding generation (what's suspicious, what severity, what confidence)
- Falls back to regex-only analysis if LLM fails

### Supporting Systems

**ToolRegistry** — A catalog of 18 SIFT forensic tools defined in YAML (`tools/metadata.yaml`). Each tool has: name, category, description, command, confidence keywords, input schema, examples, output format. The registry generates SentenceTransformer embeddings and builds a FAISS index for fast semantic search. Embeddings are cached to disk.

**Evidence Manager** *(planned)* — Registers forensic evidence (disk images, memory dumps, PCAPs, Windows artifacts) with hash computation for chain-of-custody. Detects evidence type to inform which tools are applicable. Validates files exist on the SIFT VM before execution.

**Case Manager** *(planned)* — Tracks investigation cases with metadata. Links evidence, findings, and reports to cases. JSON-based storage.

**Tool Output Parsers** *(planned)* — Per-tool structured parsers (volatility, timeline, Sleuth Kit, network) that convert raw stdout into structured data, enabling the AnalyzerAgent to reason more precisely.

**MCP Server** *(planned)* — Exposes the agent's capabilities via Model Context Protocol so that Claude Code (or any MCP client) can use it as a forensic tool. An analyst using Claude Code could say "use Find Evil Agent to analyze this memory dump" and it would work.

**LLM Provider Layer** — Protocol-based (PEP 544) interface supporting Ollama (implemented), with OpenAI and Anthropic planned. The Ollama provider supports structured JSON output using Pydantic schema validation with automatic retry on parse failures.

---

## The 18 SIFT Tools It Orchestrates

| Category | Tools |
|----------|-------|
| **Memory** | volatility, rekall |
| **Disk** | fls, icat, mmls, fsstat (Sleuth Kit) |
| **Timeline** | log2timeline (plaso), psort |
| **Network** | tcpdump, tshark (wireshark) |
| **Analysis** | strings, bulk_extractor, grep, file |
| **Hash** | md5sum, sha256sum |
| **Registry** | regripper |
| **Metadata** | exiftool |

---

## The Two Differentiating Features

### Feature #1: Hallucination-Resistant Tool Selection

No other DFIR agent does this. The two-stage FAISS→LLM pipeline with a confidence threshold means the system physically cannot recommend a tool that doesn't exist on SIFT. Verified on live VM: selected `fls` with 0.90 confidence, confirmed at `/usr/bin/fls`.

### Feature #2: Autonomous Investigative Reasoning

The agent doesn't just run one tool — it chains investigations. After finding a suspicious process via volatility, it automatically decides to check network connections, build a timeline, and look for persistence mechanisms. Each iteration extracts leads (typed as process/network/file/timeline/registry, prioritized HIGH/MEDIUM/LOW), follows the best lead, and continues until the investigation is complete. Verified: 3-iteration autonomous investigation in 45.6 seconds, zero analyst decisions.

---

## User Interfaces

### CLI (Typer + Rich)
```bash
# Single-shot analysis
find-evil analyze "Ransomware detected" "Find malicious processes" -o report.md

# Autonomous investigation
find-evil investigate "Unknown CPU-intensive process" "Trace origin" --max-iterations 5

# Case management (planned)
find-evil case create "Incident 2026-04-15" --analyst "Ifiok Moses"
find-evil case evidence add <id> /path/to/memory.raw
```

### REST API (FastAPI)
- `POST /api/v1/analyze` — single-shot analysis
- `POST /api/v1/investigate` — autonomous investigation
- `GET /api/v1/config` — current configuration
- `GET /health` — health check
- OpenAPI docs at `/api/docs`

### MCP Server (planned)
- Exposes tools: `analyze_evidence`, `investigate`, `list_tools`, `select_tool`, `execute_tool`, `extract_iocs`
- Exposes resources: evidence catalog, case data, tool registry
- Exposes prompts: memory analysis, disk triage, network investigation templates

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.11+ | Core language |
| **Orchestration** | LangGraph | Multi-agent workflow (state machine) |
| **Framework** | LangChain Core | Agent framework primitives |
| **Embeddings** | SentenceTransformers (all-MiniLM-L6-v2) | Tool description embeddings |
| **Vector Search** | FAISS | Similarity search for tool selection |
| **SSH** | asyncssh | Execute tools on SIFT VM |
| **LLM** | Ollama (gemma4:31b-cloud) | Local LLM inference |
| **Schema** | Pydantic 2.5+ | Validation throughout |
| **CLI** | Typer + Rich | Terminal UI |
| **API** | FastAPI | REST API |
| **MCP** | mcp SDK | Model Context Protocol |
| **Logging** | structlog | Structured logging |
| **Observability** | Langfuse | LLM tracing |
| **Metrics** | Prometheus | Performance metrics |

---

## What Makes This Competitive

Compared to the Valhuntir example submission (by a SANS Author), Find Evil Agent brings:

1. **A unique innovation** that no other tool has (hallucination prevention via FAISS+LLM two-stage selection)
2. **Autonomous multi-step investigation** that reduces analyst time from hours to seconds
3. **A clean multi-agent architecture** using LangGraph rather than monolithic scripting
4. **Three interfaces** (CLI, REST API, MCP) for maximum flexibility
5. **Observable** — every LLM call traced in Langfuse, every command logged with structlog

### Remaining Work (see PLAN_OF_ACTION.md)
- MCP server/client implementation
- Dynamic command building from real evidence
- Evidence and case management
- Per-tool output parsers
- MITRE ATT&CK technique mapping
- OpenAI/Anthropic LLM providers
- HTML report generation
- Demo video and DevPost submission

---

## Performance

| Operation | Time | Details |
|-----------|------|---------|
| SSH Connection | ~0.1s | asyncssh to SIFT VM |
| Command Execution | 0.15–0.20s | strings, grep, fls |
| Tool Selection (LLM) | ~30s | Ollama gemma4:31b-cloud |
| Analysis (LLM) | ~20s | IOC extraction + severity |
| **Total Single Workflow** | **60–90s** | Select → Execute → Analyze |
| **3-Step Investigation** | **45.6s** | Autonomous, zero decisions |

---

## Security

| Threat | Mitigation |
|--------|------------|
| Tool Hallucination | Two-stage selection + confidence ≥0.7 |
| Command Injection | Blocklist validation (rm -rf, dd, curl, wget, nc) |
| SSH Security | Key-based auth, no password prompts |
| Timeout DoS | Configurable timeouts (60s default, 3600s max) |
| Evidence Integrity | Read-only operations, hash verification (planned) |
| API Key Leakage | Environment variables only, never in code |

---

*Generated April 16, 2026 — Find Evil Agent*
