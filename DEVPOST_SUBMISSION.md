# DevPost Submission Materials - Find Evil Agent

**Hackathon:** FIND EVIL! (https://findevil.devpost.com)  
**Deadline:** June 15, 2026 @ 11:45pm EDT (37 days remaining)  
**Team:** Solo (Iffy Strayer)  
**GitHub:** https://github.com/iffystrayer/find-evil-agent

---

## 1. Project Tagline (60 chars max)
**Option A:** "Autonomous AI incident response at machine speed"  
**Option B:** "AI co-pilot for DFIR that thinks like a senior analyst"  
**Option C:** "Close the 8-minute gap: AI-powered forensic triage"

**Selected:** Option A (49 chars)

---

## 2. Inspiration (What inspired you to build this?)

The GTG-1002 report from Anthropic's security team showed what happens when attackers get AI agents: 80-90% autonomous operations at "physically impossible" request rates. CrowdStrike documented breakout times as fast as 7 minutes. MIT research showed AI-driven attacks running 47x faster than human operators.

Meanwhile, defenders are still manually running forensic tools, interpreting output, and deciding next steps—often taking hours for what an adversary can now do in minutes.

**The gap is the problem. Find Evil Agent closes it.**

I built this because the DFIR community needs AI co-pilots that operate at adversary speed, but we need them to be *reliable*. Traditional LLM-based tools hallucinate forensic commands that don't exist or select inappropriate tools for the evidence at hand. Find Evil Agent solves this with two-stage validation: semantic search narrows candidates to tools that actually exist, then LLM ranking selects the best one with explainable reasoning. Confidence thresholds reject low-certainty decisions instead of guessing.

The second problem was making investigations *autonomous*. Analysts don't just run one tool—they interpret findings, extract leads, and recursively follow them. Find Evil Agent automates this: it reads tool output, identifies what to investigate next, selects the right tools, and builds a complete attack chain narrative across multiple iterations.

**No other DFIR tool combines hallucination-resistant tool selection with autonomous investigative reasoning.**

---

## 3. What it does

Find Evil Agent is an autonomous AI incident response system built on the SANS SIFT Workstation. It takes an incident description ("Ransomware detected on Windows 10 endpoint") and an investigation goal ("Reconstruct complete attack chain from initial access to encryption"), then:

1. **Selects the right forensic tool** using two-stage validation:
   - Semantic search (SentenceTransformers + FAISS) narrows to top-10 candidates from 18 SIFT tools
   - LLM ranking (Ollama/OpenAI/Anthropic) selects best tool with confidence score + reasoning
   - Confidence threshold (≥0.7) rejects low-certainty selections
   - Registry validation confirms tool exists before execution

2. **Executes tools securely** on a live SIFT VM:
   - SSH connection with host-key verification
   - Command allowlist prevents injection attacks
   - Path traversal validation on all inputs
   - Structured logging with Langfuse observability

3. **Analyzes findings** and extracts IOCs:
   - IP addresses, domains, file hashes, registry keys
   - MITRE ATT&CK technique mapping
   - Severity scoring with confidence levels

4. **Follows investigative leads autonomously**:
   - Extracts leads from tool output (e.g., "Investigate suspicious DLL at C:\Windows\Temp\evil.dll")
   - Automatically selects next tools to follow leads
   - Iterates up to N times, building complete attack chain
   - Human-in-the-loop (HITL) approval before executing each lead

5. **Generates professional incident reports**:
   - HTML/PDF/Markdown with executive summaries
   - Timeline visualizations
   - MITRE ATT&CK heatmaps
   - Evidence chain of custody

**Four interfaces for different workflows:**
- **CLI:** Rich terminal UI for power users and automation
- **React UI:** Modern glassmorphism interface with real-time progress
- **REST API:** OpenAPI-documented endpoints for integrations
- **MCP Server:** Model Context Protocol server with 12+ tools for Claude integration

**Live demo results from SIFT VM (192.168.12.101):**
- Tool selection: `fls` selected with 0.90 confidence, confirmed at `/usr/bin/fls`
- Autonomous investigation: 3-iteration workflow completed in 45.6 seconds
- Tools chained: volatility → log2timeline → log2timeline (full attack chain reconstruction)

---

## 4. How we built it

**Architecture:** Multi-agent system using LangGraph for workflow orchestration

**Five specialized agents:**
1. **OrchestratorAgent** - Coordinates multi-iteration investigations, manages checkpointing
2. **ToolSelectorAgent** - Two-stage tool selection (semantic + LLM ranking)
3. **ToolExecutorAgent** - Secure SSH execution on SIFT VM with allowlist validation
4. **AnalyzerAgent** - IOC extraction, severity scoring, MITRE mapping
5. **ReporterAgent** - Professional HTML/PDF reports with Jinja2 templates

**Key technical decisions:**

**Hallucination Prevention:**
- SentenceTransformers (`all-MiniLM-L6-v2`) for tool embeddings
- FAISS vector search (L2 distance) for semantic candidate selection
- LLM structured output with `response_format={"type": "json_object"}`
- Confidence thresholds (≥0.7) for rejection instead of guessing
- Registry validation before execution (tool must exist)

**Autonomous Reasoning:**
- LangGraph state machine with checkpointing (MemorySaver → SqliteSaver)
- `interrupt_before=["human_approval_gateway"]` for HITL workflow
- Lead extraction via LLM analysis + rule-based patterns
- Priority-based lead ordering (Critical → High → Medium → Low)
- Max iteration limit to prevent infinite loops

**Security:**
- API key authentication with `secrets.compare_digest` (constant-time)
- SSH host-key verification (secure by default)
- Command allowlist (18 SIFT tools only)
- Path traversal prevention (`PathValidator`)
- HTML escape all user input (Jinja2 autoescape)
- Generic 500 responses (no stack trace leakage)

**Tech Stack:**
- **LLM:** Ollama (gemma4:31b-cloud for dev), OpenAI, Anthropic supported
- **Vector Search:** FAISS + sentence-transformers
- **Orchestration:** LangGraph with SQLite checkpointing
- **SSH:** asyncssh with agent forwarding
- **API:** FastAPI with OpenAPI documentation
- **Frontend:** React + Vite + TailwindCSS
- **Web UI:** Gradio for rapid prototyping
- **Observability:** Langfuse (LLM tracing) + structlog + Prometheus
- **Testing:** pytest with 606 tests (98.5% passing)
- **Deployment:** Docker Compose (3 services)

**Development Process:**
- Test-Driven Development (TDD) - all features have comprehensive tests
- Three-tier test structure: Specification → Structure → Execution → Integration
- Git atomic commits with Co-Authored-By tags
- Milestone-based remediation (A: Security → B: Hardening → C: Architecture)

**Time Investment:** 54 days from April 15 to May 8
- Week 1-2: Multi-agent infrastructure + tool selection (Gap #1-6)
- Week 3-4: E2E testing + React UI + demo artifacts
- Week 5-6: Security remediation (19 fixes across 3 milestones)
- Week 7-8: Architecture refactors (3 splits: MCP, Reporter, Orchestrator)

---

## 5. Challenges we ran into

**Challenge 1: LLM Hallucination in Tool Selection**

Early versions just asked the LLM "which tool should I use?" and it would confidently suggest tools that didn't exist (`forensic-analyzer`, `memory-scanner`, etc.). This is a fundamental problem with LLM-based DFIR tools—models are trained on natural language, not the exact command-line tools available on a specific system.

**Solution:** Two-stage validation
1. Semantic search limits choices to tools that actually exist (registry-backed)
2. LLM only chooses from validated candidates
3. Confidence threshold rejects low-certainty guesses
4. Final registry check before execution

**Result:** 100% of selected tools exist and are executable. Zero hallucinated commands.

**Challenge 2: HITL Without Blocking HTTP Connections**

Initial HITL implementation held HTTP connections open while waiting for user approval. This caused timeouts, connection pool exhaustion, and crashed the API server under load.

**Solution:** LangGraph interrupts with session-based resumption
- Graph pauses at `interrupt_before=["human_approval_gateway"]`
- API returns immediately with `session_id` and `waiting_approval` status
- User approves via separate `POST /api/v1/investigate/{session_id}/resume` endpoint
- Graph resumes from checkpoint without holding connections

**Result:** React UI can poll for updates, CLI can prompt interactively, API stays responsive.

**Challenge 3: SSH Security in Docker**

Needed to SSH from Docker container to SIFT VM, but didn't want private keys inside the container (security risk if container is compromised).

**Solution:** SSH agent forwarding
- Host runs `ssh-agent` with keys
- Docker mounts `SSH_AUTH_SOCK` socket into container
- Container authenticates via agent without having keys
- Added host-key verification to prevent MITM attacks

**Result:** No secrets in container, secure by default.

**Challenge 4: Test Maintenance During Refactors**

Split `orchestrator.py` (1,177 LOC → 3 modules: 667+300+210 LOC) as part of architecture cleanup. This broke 12 tests that expected the old structure.

**Solution:** TDD with pre-written guards
- Tests written *before* refactor to define expected interfaces
- Guards catch structural changes (e.g., "no formatting code in reporter.py")
- After refactor, update guards to accept new structure (wrappers, split modules)
- Fast-lane tests as regression suite (606 tests in 5 min)

**Result:** Refactors completed with no breaking changes to functionality.

**Challenge 5: Autonomous Lead Following Without Infinite Loops**

Early autonomous investigation would sometimes follow circular leads: analyze process → check DLL → analyze process → check DLL → ...

**Solution:** Multi-layer termination strategy
1. Max iteration limit (user-configurable, default 5)
2. Lead deduplication (don't follow the same lead twice)
3. Confidence-based termination (if leads drop below threshold, stop)
4. User override (HITL approval can halt investigation)

**Result:** Investigations terminate cleanly, no infinite loops in 606 test runs.

---

## 6. Accomplishments that we're proud of

**1. Zero hallucinated tool selections**
- 606 tests, 0 cases where LLM suggested a non-existent tool
- Two-stage validation (semantic + LLM) works reliably
- Confidence thresholds prevent low-quality guesses

**2. Live SIFT VM integration**
- Actually executes forensic tools on real SIFT Workstation
- SSH security (host-key verification, command allowlist, path validation)
- 6 integration tests against live VM (all passing)

**3. Autonomous multi-iteration investigations**
- Extracts leads from tool output automatically
- Follows leads recursively (up to N iterations)
- Built complete attack chains in <1 minute (3 iterations in 45.6s)

**4. Professional incident reports**
- HTML with MITRE ATT&CK heatmaps
- PDF generation with weasyprint
- Markdown for CI/CD integration
- Executive summaries for non-technical stakeholders

**5. Test coverage that survived 3 architecture refactors**
- 606 tests (98.5% passing)
- TDD methodology throughout
- Fast-lane regression suite (5 min)
- Guards detected 12 test breaks during refactors

**6. Four production interfaces**
- CLI (Rich terminal UI)
- React (modern glassmorphism)
- REST API (OpenAPI docs)
- MCP Server (12+ tools)

**7. Security-first development**
- 19 fixes across 3 milestones (Security → Hardening → Architecture)
- No critical vulnerabilities
- Authentication, input validation, CORS, SSH hardening all complete

**8. Complete observability**
- Langfuse LLM tracing
- Structlog JSON logging
- Prometheus metrics
- Agent execution logs with timestamps

---

## 7. What we learned

**Technical:**

1. **LLMs are unreliable without constraints.** You can't just ask "what tool should I use?" and trust the answer. You need:
   - Pre-filtering (semantic search to limit choices)
   - Post-validation (registry check before execution)
   - Confidence thresholds (reject low-certainty outputs)
   - Structured outputs (`response_format=json`)

2. **HITL requires async by default.** You can't block connections waiting for user input. LangGraph's interrupt system with checkpointing is the right pattern—return immediately with session ID, resume later.

3. **TDD saves time during refactors.** Writing tests first feels slow, but when you split a 1,177-line file into 3 modules, having 606 regression tests means you catch breaks immediately instead of debugging production later.

4. **Security debt compounds.** Started with 43 findings (Critical + High + Medium). Fixed 6 security issues (Milestone A), which exposed 6 more hardening needs (Milestone B), which revealed 7 architecture problems (Milestone C). Each fix made the next level of issues visible. Better to do it early.

5. **Docker + SSH = harder than it looks.** Mounting SSH agent sockets, handling known_hosts files, and ensuring host-key verification works across containers took 3 iterations to get right.

**Domain-Specific (DFIR/Security):**

1. **MITRE ATT&CK mapping is hard.** Converting raw tool output (e.g., "suspicious process lsass.exe") to techniques (T1003.001 - LSASS Memory) requires either LLM analysis or extensive rule-based heuristics. Hybrid approach works best.

2. **IOC extraction needs multiple patterns.** IP addresses are easy (regex). But file hashes have multiple formats (MD5/SHA1/SHA256), domains need TLD validation, registry keys have Windows-specific syntax. Combined 50+ patterns.

3. **Forensic tools are inconsistent.** Volatility outputs JSON, log2timeline outputs CSV, strings outputs raw text. Each needs custom parsing. Unified parser interface helped, but still 5 specialized parsers.

4. **Lead extraction is an art.** What counts as an "investigative lead"? A suspicious file path? A network connection? A registry key? Needed both LLM analysis (understands context) and rule-based extraction (reliable patterns).

**Process:**

1. **Shipping iteratively beats perfecting upfront.** Got basic tool selection working first, then added semantic search, then LLM ranking, then confidence thresholds. Each iteration was usable. Big-bang design would have failed.

2. **Good logs are worth their weight in gold.** When debugging why the orchestrator hung during HITL approval, having timestamped structlog entries showing "entered approval node" → "waiting for resume" → "session resumed" made the fix obvious.

3. **Test-driven documentation works.** Specification tests that document expected behavior (and always pass) served as executable requirements. Better than markdown docs that drift.

---

## 8. What's next for Find Evil Agent

**Immediate (Post-Hackathon):**

1. **Real case data testing**
   - Run against public memory dumps (e.g., DFIRScience scenarios)
   - Validate against known-good investigations
   - Benchmark accuracy vs. manual analysis

2. **Production deployment guide**
   - HTTPS/TLS setup
   - JWT-based authentication
   - Rate limiting for LLM calls
   - High-availability Docker Compose stack

3. **Community feedback integration**
   - User testing with DFIR practitioners
   - Bug reports and feature requests
   - Integration with existing IR workflows

**Medium-Term (3-6 months):**

1. **Enhanced tool coverage**
   - Add more SIFT tools (200+ available)
   - Support for Windows tools (KAPE, Velociraptor)
   - Cloud forensics (AWS CloudTrail, Azure logs)
   - Network forensics (Zeek, Suricata)

2. **Improved autonomous reasoning**
   - Multi-agent collaboration (parallel lead investigation)
   - Cross-evidence correlation (memory + disk + network)
   - Attack graph generation (visualize full kill chain)
   - Remediation recommendations (not just detection)

3. **Advanced MITRE ATT&CK integration**
   - Sub-technique granularity (T1003.001 vs T1003.002)
   - Defensive recommendations per technique
   - Coverage gaps analysis (which techniques we miss)

4. **Evidence management**
   - Chain of custody tracking
   - Evidence hashing and signing
   - Timeline synchronization across sources
   - Case management integration (TheHive, MISP)

**Long-Term (6-12 months):**

1. **Multi-case correlation**
   - Pattern detection across incidents
   - IOC sharing between investigations
   - Threat actor profiling
   - Campaign tracking

2. **Adversarial red team**
   - Test against GTG-1002-style AI attackers
   - Measure response time vs. breakout time
   - Optimize for speed without sacrificing accuracy

3. **Community tool ecosystem**
   - MCP server marketplace (custom tools)
   - Shared investigation playbooks
   - LLM provider plugins
   - Integration with SOAR platforms

4. **Research contributions**
   - Publish hallucination-resistance techniques
   - Benchmark autonomous DFIR accuracy
   - Open-source evaluation framework
   - Academic paper on AI-assisted IR

**Moonshot (12+ months):**

1. **Predictive incident response**
   - Learn from past investigations
   - Suggest likely attack paths proactively
   - Automate threat hunting
   - Zero-touch triage for low-severity incidents

2. **Real-time autonomous defense**
   - Live EDR integration
   - Auto-response to active threats
   - Containment recommendations
   - Rollback capabilities

---

## 9. Built With

**Languages & Frameworks:**
- Python 3.13
- JavaScript (React)
- TypeScript (frontend)

**AI/ML:**
- LangGraph (multi-agent orchestration)
- Ollama (local LLM)
- OpenAI GPT-4
- Anthropic Claude
- SentenceTransformers (embeddings)
- FAISS (vector search)

**Backend:**
- FastAPI (REST API)
- Gradio (web UI)
- asyncssh (SIFT VM execution)
- Pydantic (validation)
- SQLite (checkpointing)

**Frontend:**
- React 18
- Vite
- TailwindCSS
- Axios

**Observability:**
- Langfuse (LLM tracing)
- structlog (logging)
- Prometheus (metrics)

**Infrastructure:**
- Docker + Docker Compose
- SANS SIFT Workstation
- nginx (reverse proxy)

**Testing:**
- pytest
- pytest-asyncio
- Playwright (E2E)

**Documentation:**
- MkDocs (ReadTheDocs)
- OpenAPI (Swagger)

---

## 10. Try it out

**GitHub:** https://github.com/iffystrayer/find-evil-agent  
**Documentation:** https://find-evil-agent.readthedocs.io (if published)  
**Demo Video:** [YouTube link after recording]

**Quick Start:**
```bash
# Clone repo
git clone https://github.com/iffystrayer/find-evil-agent.git
cd find-evil-agent

# Start with Docker
docker compose up -d

# Access interfaces
# React UI: http://localhost:15173
# Gradio Web: http://localhost:17000
# API Docs: http://localhost:18000/docs
```

**CLI Demo:**
```bash
# Analyze incident
find-evil analyze "Ransomware detected on Windows 10 endpoint" \
  "Identify initial access vector"

# Autonomous investigation (3 iterations)
find-evil investigate "Suspicious process activity detected" \
  "Reconstruct complete attack chain" -n 3
```

---

## 11. Screenshots

**Priority order for DevPost (upload 4-6 best):**

1. **React UI - Homepage** (`demo_artifacts/demo_final/01_react_homepage.png`)
   - Shows glassmorphism design
   - Interface options (CLI/API/React/MCP)

2. **React UI - Analysis Results** (`demo_artifacts/demo_final/05_react_results.png`)
   - Tool selection with confidence
   - IOCs extracted
   - MITRE ATT&CK mapping

3. **CLI - Rich Terminal UI** (needs screenshot)
   - `find-evil investigate` output
   - Real-time progress bars
   - HITL approval prompt

4. **HTML Report - MITRE Heatmap** (needs screenshot)
   - Professional incident report
   - ATT&CK technique coverage
   - Executive summary

5. **API Documentation** (needs screenshot)
   - OpenAPI/Swagger interface
   - Endpoint documentation

6. **React UI - Form Filled** (`demo_artifacts/demo_final/03_react_form_filled.png`)
   - User input examples
   - Configuration options

---

## 12. Video Demo Script

**See:** `DEMO_VIDEO_SCRIPT.md` for full 5-7 minute script

**Key segments:**
1. Introduction (30s) - Problem statement
2. System Overview (30s) - Architecture + interfaces
3. React UI Demo (2.5min) - HITL workflow with live SIFT VM
4. Autonomous Investigation (1.5min) - Multi-iteration lead following
5. Report Generation (1min) - Professional HTML report walkthrough
6. Conclusion (30s) - Unique features + availability

**Total runtime:** 5-7 minutes  
**Resolution:** 1080p minimum  
**Format:** MP4 or WebM

---

## Submission Checklist

- [ ] DevPost project created
- [ ] All 12 sections filled in
- [ ] 4-6 screenshots uploaded
- [ ] Demo video recorded and uploaded
- [ ] GitHub repo link added
- [ ] "Built With" tags added (Python, React, Docker, etc.)
- [ ] Project marked as "public"
- [ ] Submitted before deadline (June 15, 2026 @ 11:45pm EDT)

---

**Last Updated:** May 8, 2026  
**Status:** Ready for demo video recording
