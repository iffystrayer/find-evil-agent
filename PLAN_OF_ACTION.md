# Find Evil Agent — Plan of Action

**Hackathon:** FIND EVIL! (April 15 – June 15, 2026)  
**Prize Pool:** $22,000  
**DevPost:** https://findevil.devpost.com  
**Last Updated:** April 16, 2026

---

## 1. Executive Summary

Find Evil Agent is an autonomous AI incident-response agent for the SANS SIFT Workstation. It orchestrates 18+ forensic tools through a multi-agent LangGraph workflow, using a novel two-stage hallucination-resistant tool selection system (FAISS semantic search → LLM ranking → confidence threshold) and autonomous iterative investigation that follows leads without analyst intervention.

The codebase has a strong architectural foundation but contains **critical gaps** that must be closed to produce a competitive submission. This document is the step-by-step plan to get there.

---

## 2. Gap Analysis

### What Works Today

| Component | Status | Details |
|-----------|--------|---------|
| **Multi-Agent Architecture** | ✅ Complete | LangGraph: Orchestrator → ToolSelector → ToolExecutor → Analyzer |
| **ToolSelectorAgent** | ✅ Complete | FAISS + LLM ranking, confidence ≥0.7, registry validation |
| **ToolExecutorAgent** | ✅ Complete | SSH via asyncssh to SIFT VM (192.168.12.101) |
| **AnalyzerAgent** | ✅ Complete | IOC regex extraction + LLM finding generation |
| **ToolRegistry** | ✅ Complete | 18 tools, YAML metadata, SentenceTransformers + FAISS |
| **Ollama Provider** | ✅ Complete | HTTP API, structured JSON output, schema validation |
| **CLI** | ✅ Complete | Typer + Rich: `analyze`, `investigate`, `config`, `version` |
| **REST API** | ✅ Complete | FastAPI with OpenAPI docs on port 18000 |
| **Iterative Investigation** | ✅ Complete | Autonomous lead extraction + follow-up (up to N iterations) |
| **Tests** | ✅ Complete | 239 tests (191 unit + 48 integration) |

### What's Broken or Missing

| Gap | Severity | Impact |
|-----|----------|--------|
| **MCP server/client are stubs** | 🔴 Critical | Hackathon *requires* MCP integration |
| **Tool commands are hardcoded** | 🔴 Critical | `_build_tool_command()` returns demo strings like `strings /etc/hostname` — nothing works on real evidence |
| **No evidence management** | 🔴 Critical | Can't register disk images, memory dumps, artifacts |
| **No Protocol SIFT integration** | 🟡 High | The reference framework from the organizers |
| **executor.py is a dead stub** | 🟡 Medium | Confusing duplicate of the working tool_executor.py |
| **OpenAI/Anthropic providers** | 🟡 Medium | Only Ollama implemented |
| **No case management** | 🟡 Medium | No case lifecycle (create → investigate → report) |
| **No tool output parsers** | 🟡 Medium | Analyzer uses generic regex, no per-tool structured parsing |
| **No MITRE ATT&CK mapping** | 🟢 Low | Differentiation feature |
| **No HTML reports** | 🟢 Low | Only markdown today |

### Benchmark: Valhuntir (Example Submission by SANS Author Steve Anson)

Valhuntir sets the quality bar. Key features to match or exceed:

- Full case lifecycle CLI (`vhir case init`, `evidence register`, `execute`, `report`)
- MCP servers for forensics, case management, reporting, Windows triage
- HMAC-based approval/rejection workflow for safe execution
- Identity management and verification
- Evidence provenance tracking
- Gateway for remote SIFT communication
- CI/CD pipeline, documentation site (mkdocs), security policy

---

## 3. Architecture (Current + Planned)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Find Evil Agent                          │
│                                                                 │
│  ┌─────────┐  ┌──────────────────────────────────────────────┐ │
│  │  CLI    │──│           OrchestratorAgent                   │ │
│  │ (Typer) │  │             (LangGraph)                       │ │
│  └─────────┘  └──────────┬──────────┬──────────┬─────────────┘ │
│  ┌─────────┐             │          │          │               │
│  │REST API │─────────────┘          │          │               │
│  │(FastAPI)│                        │          │               │
│  └─────────┘                        │          │               │
│  ┌─────────┐             ┌──────────┴───┐  ┌──┴────────────┐  │
│  │MCP Srvr │◄──────────► │ToolSelector  │  │ToolExecutor   │  │
│  │ (NEW)   │             │ (FAISS+LLM)  │  │ (SSH asyncssh)│  │
│  └─────────┘             └──────┬───────┘  └──────┬────────┘  │
│                                 │                  │           │
│  ┌──────────┐           ┌──────┴───────┐  ┌──────┴────────┐  │
│  │Evidence  │◄─────────►│ToolRegistry  │  │   SIFT VM     │  │
│  │Manager   │           │(18 tools,    │  │192.168.12.101 │  │
│  │ (NEW)    │           │ FAISS index) │  └───────────────┘  │
│  └──────────┘           └──────────────┘          │           │
│                                                    ▼           │
│  ┌──────────┐                          ┌──────────────────┐   │
│  │  Case    │                          │  AnalyzerAgent   │   │
│  │ Manager  │                          │ (IOC + LLM)      │   │
│  │ (NEW)    │                          └────────┬─────────┘   │
│  └──────────┘                                   │             │
│                                          ┌──────┴─────────┐   │
│                                          │ Tool Parsers   │   │
│                                          │ (NEW)          │   │
│                                          └────────────────┘   │
└───────────────────────────────────────────┬───────────────────┘
                                            │
                    ┌───────────────────────────────────────┐
                    │          External Services            │
                    │  • Ollama LLM (192.168.12.124:11434)  │
                    │  • OpenAI API (NEW)                   │
                    │  • Anthropic API (NEW)                │
                    │  • Langfuse (observability)           │
                    │  • Protocol SIFT (NEW)                │
                    └───────────────────────────────────────┘
```

---

## 4. Implementation Phases

### Phase 1: Core Functionality (April 16 – April 30)

> **Goal:** Make the agent work with real forensic evidence end-to-end.

#### 1.1 Dynamic Command Building

**File:** `src/find_evil_agent/agents/orchestrator.py`

**Problem:** `_build_tool_command()` is hardcoded:
```python
# CURRENT (broken)
if tool_name == "strings":
    return "strings /etc/hostname"
elif tool_name == "grep":
    return "grep -i error /var/log/syslog 2>/dev/null || echo 'No errors found'"
else:
    return f"which {tool_name} || echo '{tool_name} not found'"
```

**Solution:** Replace with an LLM-powered command builder that:
1. Takes: ToolSelection + incident context + evidence file paths + tool metadata (inputs, examples from `metadata.yaml`)
2. Asks LLM: "Given this tool and this evidence, generate the exact command to run"
3. Validates: Command checked against blocked patterns before execution
4. Returns: Properly formed forensic command with correct flags and paths

**Acceptance criteria:**
- Given evidence `/mnt/evidence/case01/memory.raw` and tool `volatility`, produces `volatility -f /mnt/evidence/case01/memory.raw --profile=Win10x64 pslist`
- Given evidence `/mnt/evidence/case01/disk.dd` and tool `fls`, produces `fls -r /mnt/evidence/case01/disk.dd`
- All generated commands pass blocked-pattern validation

#### 1.2 Evidence Manager

**New files:**
- `src/find_evil_agent/evidence/__init__.py`
- `src/find_evil_agent/evidence/manager.py`

**Features:**
- Register evidence files: disk images (.E01, .dd, .raw), memory dumps (.raw, .vmem, .dmp), packet captures (.pcap, .pcapng), log directories, Windows artifacts ($MFT, registry hives, Amcache.hve)
- Evidence catalog: Pydantic models tracking file path, type, SHA256 hash, size, mount point, registration timestamp
- Evidence type detection → automatically inform which categories of tools are applicable (e.g., memory dump → volatility, rekall; disk image → fls, icat, mmls)
- Validate evidence files exist on SIFT VM via SSH before tool execution
- Mount management: auto-mount E01/dd images to `/mnt/evidence/<case_id>/` on SIFT VM

**Acceptance criteria:**
- Can register a `.raw` memory dump and have the system know volatility is applicable
- Can register a `.dd` disk image, auto-mount it, and have fls/icat available
- Hash is computed at registration for chain-of-custody

#### 1.3 Case Management

**New files:**
- `src/find_evil_agent/case/__init__.py`
- `src/find_evil_agent/case/case.py`

**Features:**
- Create cases with metadata (name, analyst, date, description, classification)
- Cases stored as JSON in `~/.find-evil/cases/<case_id>/case.json`
- Link evidence to cases
- Link findings and reports to cases
- CLI commands: `find-evil case create`, `find-evil case list`, `find-evil case show`, `find-evil case evidence add`

**Acceptance criteria:**
- `find-evil case create "Ransomware Investigation" --analyst "Ifiok Moses"` creates a case
- `find-evil case evidence add <case_id> /path/to/memory.raw` registers evidence
- `find-evil analyze` and `find-evil investigate` accept `--case` flag to link results

#### 1.4 Tool Output Parsers

**New files:**
- `src/find_evil_agent/tools/parsers/__init__.py`
- `src/find_evil_agent/tools/parsers/volatility_parser.py`
- `src/find_evil_agent/tools/parsers/timeline_parser.py`
- `src/find_evil_agent/tools/parsers/tsk_parser.py`
- `src/find_evil_agent/tools/parsers/network_parser.py`
- `src/find_evil_agent/tools/parsers/generic_parser.py`

**Features:**
- Each parser takes raw tool stdout and returns structured dicts
- `volatility_parser`: Parse pslist → list of process dicts (PID, name, PPID, threads, handles, start_time); Parse netscan → list of connection dicts (local_addr, remote_addr, state, PID, owner)
- `timeline_parser`: Parse l2tcsv → list of event dicts (datetime, source, sourcetype, type, user, host, description)
- `tsk_parser`: Parse fls output → list of file entries (inode, type, name, path, deleted flag); Parse mmls → list of partition entries
- `network_parser`: Parse tcpdump/tshark → list of packet summaries (timestamp, src, dst, proto, info)
- `generic_parser`: Fallback using regex line parsing
- AnalyzerAgent uses parsed output for more accurate LLM analysis

**Acceptance criteria:**
- Volatility pslist output parsed into structured process list
- AnalyzerAgent can reference specific process names and PIDs in findings

#### 1.5 Cleanup

- Delete `src/find_evil_agent/agents/executor.py` (dead stub, `tool_executor.py` is the real implementation)
- Remove any imports referencing `executor.py`

---

### Phase 2: MCP Integration (May 1 – May 14)

> **Goal:** Implement Model Context Protocol — the hackathon's core technical requirement.

#### 2.1 MCP Server

**File:** `src/find_evil_agent/mcp/server.py` (rewrite from stub)

**SDK:** Uses `mcp` Python package (already in pyproject.toml: `mcp>=1.0.0`)

**MCP Tools to expose:**

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `analyze_evidence` | Run full Select→Execute→Analyze workflow | incident_description, analysis_goal, evidence_path |
| `investigate` | Run autonomous multi-iteration investigation | incident_description, analysis_goal, max_iterations |
| `list_tools` | List available SIFT forensic tools | category (optional filter) |
| `select_tool` | Run hallucination-resistant tool selection | incident_description, analysis_goal |
| `execute_tool` | Execute a specific tool on SIFT VM | tool_name, command, timeout |
| `extract_iocs` | Extract IOCs from provided text | text |
| `get_findings` | Retrieve findings from a session | session_id |

**MCP Resources:**
- `evidence://catalog` — current evidence catalog
- `case://active` — active case data
- `tools://registry` — all 18+ SIFT tools with metadata

**MCP Prompts:**
- `memory-analysis` — template for memory forensics workflow
- `disk-triage` — template for disk image investigation
- `network-investigation` — template for packet capture analysis
- `incident-response` — comprehensive IR workflow template

**Acceptance criteria:**
- MCP server starts and exposes tools discoverable by Claude Code / other MCP clients
- `claude mcp add find-evil-agent python -m find_evil_agent.mcp.server` works
- Claude Code can call `analyze_evidence` and get structured results back

#### 2.2 MCP Client

**File:** `src/find_evil_agent/mcp/client.py` (rewrite from stub)

**Features:**
- Connect to external MCP servers (SSH-MCP, binary analysis, etc.)
- Discover available tools from remote servers
- Call remote tools and return results to the orchestrator
- Configuration via `~/.find-evil/mcp_servers.json`

**Acceptance criteria:**
- Can connect to an SSH-MCP server and execute remote commands
- Agent can orchestrate tools across local SIFT + remote MCP servers

#### 2.3 Protocol SIFT Integration

**Steps:**
1. Install Protocol SIFT on SIFT VM: `curl -fsSL https://raw.githubusercontent.com/teamdfir/protocol-sift/main/install.sh | bash`
2. Investigate what Protocol SIFT exposes (tools, APIs, MCP endpoints)
3. Integrate as an upstream tool source if compatible
4. Document any incompatibilities or workarounds

---

### Phase 3: Polish & Differentiation (May 15 – May 31)

> **Goal:** Raise quality to match/exceed the Valhuntir example submission.

#### 3.1 Additional LLM Providers

**New files:**
- `src/find_evil_agent/llm/providers/openai.py`
- `src/find_evil_agent/llm/providers/anthropic.py`

Both implement the same `LLMProvider` protocol (`chat()`, `chat_with_schema()`, `generate()`, `generate_json()`, `get_model_name()`). Same retry-on-validation-failure pattern as the Ollama provider.

#### 3.2 MITRE ATT&CK Mapping

**New files:**
- `src/find_evil_agent/enrichment/__init__.py`
- `src/find_evil_agent/enrichment/mitre.py`

**Features:**
- Local JSON database of ATT&CK techniques (embedded, no API dependency)
- Keyword-based mapping: finding description → matching ATT&CK technique IDs
- LLM-assisted mapping for ambiguous findings
- Report integration: each finding annotated with technique ID + tactic

**Example output in report:**
```
Finding: Registry Run key added for payload.dll
Severity: HIGH
MITRE ATT&CK: T1547.001 (Boot or Logon Autostart Execution: Registry Run Keys)
Tactic: Persistence
```

#### 3.3 Enhanced Reporting

**New files:**
- `src/find_evil_agent/reporting/__init__.py`
- `src/find_evil_agent/reporting/html.py`
- `src/find_evil_agent/reporting/templates/report.html`

**Features:**
- HTML reports with professional CSS styling (Jinja2 templates)
- Executive summary generation via LLM
- Timeline visualization (text in terminal, graphical in HTML)
- MITRE ATT&CK technique heatmap in HTML
- Improved markdown reports (better formatting, table of contents)

#### 3.4 Real SIFT Tool Integration

**Tasks:**
1. Install Volatility 3 on SIFT VM
2. Download starter case data from hackathon-provided Egnyte link
3. Test and verify end-to-end workflows:
   - **Memory analysis chain:** volatility pslist → netscan → malfind
   - **Disk triage chain:** mmls → fls → icat → strings
   - **Timeline chain:** log2timeline → psort → analysis
   - **Network chain:** tcpdump → tshark → bulk_extractor

#### 3.5 Security Hardening

- Human-in-the-loop approval before destructive/long-running commands
- Audit log of every command executed (timestamped, linked to case/session)
- Evidence integrity verification (SHA256 hash check before and after analysis)

---

### Phase 4: Submission Prep (June 1 – June 15)

> **Goal:** Package everything for a winning DevPost submission.

#### 4.1 Demo Video (3–5 minutes)

Follow the demo script structure from hackathon materials:
1. **Setup (0:00–0:45):** Show SIFT VM, evidence files, launch Find Evil Agent
2. **Tool Selection (0:45–1:30):** Demonstrate hallucination-resistant selection with confidence score
3. **Autonomous Investigation (1:30–3:00):** Show multi-iteration lead-following on real evidence
4. **MCP Integration (3:00–4:00):** Show Claude Code using Find Evil Agent as MCP server
5. **Report (4:00–4:30):** Show generated investigation report with MITRE mapping

Record with OBS Studio. Speed up tool execution in post-production.

#### 4.2 Documentation

- **README.md:** Comprehensive rewrite with final feature list, installation, usage, architecture diagram
- **docs/getting-started.md:** Step-by-step setup guide
- **docs/architecture.md:** Technical architecture with Mermaid diagrams
- **docs/mcp-guide.md:** How to use Find Evil Agent as an MCP server
- **CONTRIBUTING.md:** Contribution guidelines

#### 4.3 Testing & CI

- All existing tests pass
- New tests for: evidence manager, case manager, MCP server, tool parsers, MITRE mapping
- GitHub Actions CI: lint (ruff), format (black), type-check (mypy), test (pytest)
- Coverage badge in README

#### 4.4 DevPost Submission

**Submission content:**
- Project title: "Find Evil Agent — Hallucination-Resistant AI for DFIR"
- Tagline: "Autonomous forensic investigation that never hallucinates tool names"
- Description emphasizing two differentiators:
  1. Two-stage hallucination prevention (FAISS + LLM + confidence threshold)
  2. Autonomous iterative investigation (lead extraction + follow-up)
- Architecture diagram
- Screenshots/GIFs of CLI output
- Demo video link
- GitHub repo link
- Tech stack: Python, LangGraph, FAISS, SentenceTransformers, asyncssh, MCP, FastAPI, Typer, Rich

---

## 5. Weekly Schedule

| Week | Dates | Focus | Deliverables |
|------|-------|-------|-------------|
| 1 | Apr 16–22 | Phase 1.1 + 1.5 | Dynamic command builder, delete executor.py stub |
| 2 | Apr 23–30 | Phase 1.2 + 1.3 + 1.4 | Evidence manager, case management, tool parsers |
| 3 | May 1–7 | Phase 2.1 | MCP server implementation |
| 4 | May 8–14 | Phase 2.2 + 2.3 | MCP client, Protocol SIFT integration |
| 5 | May 15–21 | Phase 3.1 + 3.2 | OpenAI/Anthropic providers, MITRE ATT&CK mapping |
| 6 | May 22–31 | Phase 3.3 + 3.4 + 3.5 | HTML reports, real SIFT tool testing, security hardening |
| 7 | Jun 1–7 | Phase 4.1 + 4.2 | Demo video, documentation |
| 8 | Jun 8–15 | Phase 4.3 + 4.4 | CI/CD, final testing, DevPost submission |

---

## 6. Priority Order (If Time Is Short)

If we can't complete everything, this is the order of importance:

1. **Dynamic command builder** (Phase 1.1) — nothing works on real evidence without this
2. **Evidence manager** (Phase 1.2) — needed for real forensic case work
3. **MCP server** (Phase 2.1) — hackathon core requirement
4. **Tool output parsers** (Phase 1.4) — dramatically improves analysis quality
5. **Case management** (Phase 1.3) — competitive feature vs Valhuntir
6. **Real SIFT tool integration** (Phase 3.4) — proves system works end-to-end
7. **More LLM providers** (Phase 3.1) — flexibility, judges may use different providers
8. **MITRE ATT&CK mapping** (Phase 3.2) — differentiation in reports
9. **HTML reports** (Phase 3.3) — visual polish
10. **Submission prep** (Phase 4) — required, but can be compressed

---

## 7. File Inventory

### Files to Create

```
src/find_evil_agent/evidence/__init__.py
src/find_evil_agent/evidence/manager.py
src/find_evil_agent/case/__init__.py
src/find_evil_agent/case/case.py
src/find_evil_agent/tools/parsers/__init__.py
src/find_evil_agent/tools/parsers/volatility_parser.py
src/find_evil_agent/tools/parsers/timeline_parser.py
src/find_evil_agent/tools/parsers/tsk_parser.py
src/find_evil_agent/tools/parsers/network_parser.py
src/find_evil_agent/tools/parsers/generic_parser.py
src/find_evil_agent/enrichment/__init__.py
src/find_evil_agent/enrichment/mitre.py
src/find_evil_agent/reporting/__init__.py
src/find_evil_agent/reporting/html.py
src/find_evil_agent/reporting/templates/report.html
src/find_evil_agent/llm/providers/openai.py
src/find_evil_agent/llm/providers/anthropic.py
tests/unit/evidence/test_manager.py
tests/unit/case/test_case.py
tests/unit/tools/test_parsers.py
tests/unit/mcp/test_server.py
.github/workflows/ci.yml
docs/getting-started.md
docs/architecture.md
docs/mcp-guide.md
```

### Files to Modify

```
src/find_evil_agent/agents/orchestrator.py    — LLM-powered command builder
src/find_evil_agent/mcp/server.py             — full MCP implementation (rewrite stub)
src/find_evil_agent/mcp/client.py             — MCP client implementation (rewrite stub)
src/find_evil_agent/cli/main.py               — add case/evidence CLI commands
src/find_evil_agent/api/server.py             — add case/evidence API endpoints
src/find_evil_agent/config/settings.py        — evidence/case path settings
tools/metadata.yaml                           — richer tool details for command building
pyproject.toml                                — add Jinja2, new deps
README.md                                     — comprehensive update
```

### Files to Delete

```
src/find_evil_agent/agents/executor.py        — dead stub (tool_executor.py is the real one)
```

---

## 8. Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM for command building | Use same provider as tool selection | Consistency, already configured |
| Evidence storage | JSON catalog on local fs, evidence files on SIFT VM | Simple, no database dependency |
| Case storage | JSON files in `~/.find-evil/cases/` | Simple, portable, git-friendly |
| MCP SDK | `mcp` Python package (already in deps) | Official SDK, hackathon standard |
| Tool parsers | Per-tool Python modules | Precise structured output vs generic regex |
| MITRE mapping | Embedded JSON database | No external API dependency, works offline |
| HTML reports | Jinja2 templates | Industry standard, flexible, well-supported |
| Additional LLM providers | OpenAI + Anthropic | Cover most judge setups |

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| SIFT VM unavailable | Test locally with mock SSH, document VM setup |
| Ollama server down | Add OpenAI/Anthropic as fallback providers |
| Protocol SIFT incompatible | Our MCP server is standalone — Protocol SIFT is additive, not required |
| Time crunch | Priority order ensures most critical features first; Phase 3 items are nice-to-have |
| Volatility not on SIFT VM | Install via pip; if fails, focus on tools that are available (strings, grep, fls) |
| LLM command building unreliable | Fallback to template-based commands from tool metadata examples |

---

## 10. Two Differentiating Features (Hackathon Pitch)

### Feature #1: Hallucination-Resistant Tool Selection

**Problem:** LLM-based agents hallucinate non-existent tool names, leading to failed commands and wasted analyst time.

**Our solution — Two-stage validation:**
1. **Semantic Search** (SentenceTransformers + FAISS) narrows to real tools only
2. **LLM Ranking** selects best tool with mandatory reasoning
3. **Confidence Threshold** (≥0.7) rejects uncertain selections
4. **Registry Validation** confirms tool exists on SIFT VM

**Verified result:** fls selected with 0.90 confidence, confirmed at `/usr/bin/fls` on live SIFT VM.

### Feature #2: Autonomous Investigative Reasoning

**Problem:** Traditional workflows require analysts to manually run each tool, interpret results, and decide next steps — hours of tedious work.

**Our solution — Automatic lead following:**
1. Run initial analysis (Select → Execute → Analyze)
2. LLM extracts investigative leads from findings
3. Prioritize leads (HIGH > MEDIUM > LOW, then by confidence)
4. Automatically follow highest-priority lead as next analysis goal
5. Repeat until max iterations or no leads remain
6. Synthesize complete investigation narrative

**Verified result:** 3-iteration investigation in 45.6 seconds (volatility → log2timeline → log2timeline), zero analyst decisions required.

---

*Generated April 16, 2026 — Find Evil Agent v0.1.0*
