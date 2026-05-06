# Find Evil Agent — Code Review (Canonical)

**Last reviewed:** 2026-05-06
**Review scope:** Critical + High + Medium for an internal-LAN forensic tool
**Authority:** This document supersedes all prior review reports. The four
legacy reviews (April 24 / May 5 reconciliations) live under
[`docs/archive/code-reviews/`](docs/archive/code-reviews/) for audit-trail
purposes — do not act on them.

---

## Executive summary

Three milestones of remediation, scoped to harden the obvious blockers
(auth, path traversal, SSH MITM, command-validation bypass, runtime
NameError) and pay down the critical debt (dead modules, unescaped HTML,
blocking I/O in async paths, weak input validation).

| Milestone | Status | Coverage |
|---|---|---|
| **A — Hard Security Fixes** | ✅ COMPLETE (6/6) | Path traversal, SSH host keys, allowlist commands, API key auth, SSH agent forwarding, latent NameError |
| **B — Hardening & Hygiene** | ✅ COMPLETE (6/6) | Sanitized 500s, HTML escape, async file I/O, CORS+bounds, UUID session IDs, dead-code purge |
| **C — Architecture Cleanup** | ⏳ PENDING (0/6) | Memory bound, LLM schema dedup, monster-file split, magic-numbers→settings, bytes guard, API/evidence test coverage |

**Test baseline (post-B6):** 498 passed, 0 failed, 10 documented xfails.
The xfails are pre-existing AsyncMock/weasyprint/.env-leak issues
documented in [`docs/archive/code-reviews/CODE_REVIEW_FINDINGS.md`](docs/archive/code-reviews/CODE_REVIEW_FINDINGS.md)
and should not be confused with regressions.

---

## Milestone A — Hard Security Fixes (DONE)

| ID | Commit | Fix |
|---|---|---|
| A1 | `19ef82c` | `PathValidator` on MCP `execute_tool` and API analyze handlers — rejects `../` etc. before any registry/SSH work |
| A2 | `4b0e306` | SSH host-key verification — secure-by-default, opt-out via `FEA_SSH_STRICT_HOST_KEY_CHECKING=false` |
| A3 | `45ace74` | Allowlist-based command validation — closes case/whitespace/path-prefix/unregistered-binary bypasses |
| A4 | `7fde9e8` | API-key auth on `/api/v1/*` — `X-API-Key` header, `secrets.compare_digest`, empty list = dev mode |
| A5 | `3363379` | Docker SSH agent-forwarding (no more private key in container) + `~/.ssh/known_hosts` mount for A2 |
| A6 | `f7c8d09` | Latent `NameError` fix in `api/server.py:323` resume handler |

**Deferred:** A4b — MCP HTTP-transport auth (FastMCP middleware story). Stdio
MCP is OS-user-authenticated, so this is a follow-up, not a blocker.

## Milestone B — Hardening & Hygiene (DONE)

| ID | Commit | Fix |
|---|---|---|
| B1 | `59b00b5` | Generic 500 responses + `logger.exception(...)` for tracebacks (no path/exception leakage to clients) |
| B2 | `b0b42e6` | HTML-escape every user-controlled value in `reporter.format_html` (incident description, exec summary, MITRE, IOC, findings, recommendations, graph error fallback) |
| B3 | `52df0b8` | `aiofiles` in async paths — 3 sites in `reporter.py` + 4 helpers in `evidence/manager.py` (`_save_evidence`, `load_evidence`, `list_evidence`, `add_custody_entry` are now async) |
| B4 | `e96919d` | Explicit CORS allow-lists (`GET/POST/OPTIONS`, `Content-Type/X-API-Key/Authorization`); Pydantic `min_length=5`/`max_length=10_000` + control-char rejection on `incident_description`/`analysis_goal` |
| B5 | `0a7d093` | `session_id: UUID` path parameter on `/api/v1/investigate/{session_id}/resume` — framework-boundary 422 instead of orchestrator 500 on junk input |
| B6 | (this commit) | Deleted dead modules: `graph/{__init__,workflow,checkpoint,conditions,state}.py`, `agents/{executor,memory}.py`, `mcp/client.py`, `agents/reporter.py.bak`. Archived 4 legacy review docs under `docs/archive/code-reviews/`. |

## Milestone C — Architecture Cleanup (PENDING)

| ID | Plan | Owning files |
|---|---|---|
| C1 | Memory bound + persistent checkpointer | `agents/orchestrator.py:26` (`_global_memory_saver`) |
| C2 | Extract LLM schema utilities into `llm/schema_utils.py` | `llm/providers/{openai,ollama}.py` |
| C3 | Split monsters: `mcp/server.py` (1,144 LOC), `agents/reporter.py` (1,117), `agents/orchestrator.py` (1,172) | as listed |
| C4 | Magic numbers → settings (`confidence_threshold`, `MAX_RETRIES`, `top_k`, `DEFAULT_TIMEOUT`) | `config/settings.py` + call sites |
| C5 | Bytes guard in analyzer | `agents/analyzer.py:277` |
| C6 | Backend test coverage for `api/server.py`, `evidence/manager.py`, `llm/factory.py` | `tests/api/`, `tests/integration/` |

The B2 Jinja2 migration was deliberately deferred to **C3** — template
extraction lands naturally during the reporter split, so doing both at
once would have made B2 a 1,100-line refactor instead of an atomic
security commit.

---

## Acknowledged debt (out of scope for this cycle)

- F14 type-hint style migration (defer to a single ruff-driven sweep)
- F15 frontend Error Boundary + Zustand + frontend tests (separate
  frontend phase; backend hardening first)
- F16 test directory consolidation (low value vs. risk of breaking imports)
- F6 prompt-injection sanitization (delimiters added opportunistically
  when touching the analyzer; no dedicated phase)
- Documentation IP scrubbing (sweep when next touching `docs/`)

---

## Operational verification

Per repo TDD policy, every change in A/B lands tests-first.

```bash
# Fast lane (~7 min)
uv run pytest -m "not integration and not requires_sift_vm"
# Expected: 498 passed, 0 failed, 10 xfailed

# Live SIFT VM regression smoke (P0.2)
FEA_SIFT_VM_AVAILABLE=1 SIFT_VM_PORT=22 SIFT_SSH_KEY_PATH=~/.ssh/sift_vm_key \
  uv run pytest -m requires_sift_vm
# Expected: 6 passed (covers A1+A2+A3+A5 end-to-end)
```

End-to-end manual checks:

1. **Path-traversal blocked:** `curl -X POST .../api/v1/analyze -H "X-API-Key: $KEY" -d '{"evidence_paths":["../../etc/passwd"], ...}'` → 400, not 500/200
2. **Auth enforced:** unauthenticated request → 401
3. **MCP path validation:** `execute_tool(tool_name="strings", evidence_path="../../etc/passwd")` rejected before any SSH call
4. **HTML escape:** report with IOC `<img src=x onerror=alert(1)>` → resulting HTML contains `&lt;img …&gt;`
5. **SSH host-key check:** spoofed host fingerprint rejected with `HostKeyNotVerifiable`
6. **Concurrent investigations:** two parallel `/investigate` calls — both progress without event-loop blocking (B3 verified)
7. **Session-id validation:** `POST /api/v1/investigate/not-a-uuid/resume` → 422

---

## How to extend this document

When a new review pass discovers issues:

1. Add findings to a dedicated section here, **not** to a new top-level
   `*_REVIEW*.md` file (the proliferation of those is what motivated this
   reconciliation).
2. If the new pass replaces this one, move this file to
   `docs/archive/code-reviews/CODE_REVIEW_<YYYY-MM-DD>.md` and write a
   new canonical `CODE_REVIEW.md`.
3. Reference the archive in the new doc so the audit trail stays linked.
