# 🎙️ Demo Video Voiceover Script

**Target Length:** 5-7 minutes  
**Purpose:** Narration for Playwright-recorded video  
**Tone:** Professional, enthusiastic, clear

---

## SEGMENT 1: Introduction (30 seconds)

> "Hi, I'm Iffy Strayer, and I'm excited to show you **Find Evil Agent** - an autonomous AI incident response system built for the FIND EVIL! hackathon.
>
> Traditional DFIR workflows require analysts to manually run each forensic tool, interpret results, and decide next steps - often taking hours for a single investigation.
>
> Find Evil Agent changes this by autonomously selecting tools, executing them on a SIFT workstation, and iteratively following investigative leads - all while keeping a human analyst in the loop for critical decisions.
>
> Let me show you how it works."

---

## SEGMENT 2: System Overview (30 seconds)

> "The system consists of three main interfaces:
> 1. A modern React UI with HITL support
> 2. A CLI for power users and automation
> 3. A REST API for integrations
>
> All three interfaces support our two unique features:
> - Hallucination-resistant tool selection using semantic search and LLM ranking
> - Autonomous investigative reasoning that follows leads automatically
>
> Let's start with the React UI to demonstrate the full HITL workflow."

---

## SEGMENT 3: React UI Demo - HITL Workflow (2.5 minutes)

> "Opening the React UI at localhost 15173, you'll see our glassmorphism-designed interface.
>
> I'll toggle to **Investigative Mode** - this is where the autonomous iteration happens.
>
> For this demo, I'll investigate a ransomware incident. Let me enter the incident description...
>
> [PAUSE while form fills]
>
> The agent is now performing its first analysis iteration. It will:
> 1. Select the most appropriate forensic tool using semantic search
> 2. Execute it on the SIFT workstation
> 3. Extract findings and IOCs
> 4. Identify investigative leads to follow
>
> And here's where the Human-in-the-Loop system kicks in...
>
> [PAUSE for HITL dialog]
>
> The agent has identified a high-priority investigative lead. Let me review it:
>
> - **Priority:** High
> - **Confidence:** 85%
> - **Rationale:** Found suspicious process activity in memory - should analyze process tree
>
> As the analyst, I can review the lead's details, understand why it was selected, and make an informed decision.
>
> This prevents the agent from going down rabbit holes or wasting time on low-value leads.
>
> I'll approve this lead and let the investigation continue...
>
> [PAUSE for second iteration]
>
> The agent is now following that lead, selecting another tool, and continuing the investigation.
>
> Notice how each iteration builds on the previous findings - this is autonomous investigative reasoning in action.
>
> Traditional tools would stop after the first analysis. Find Evil Agent automatically constructs the complete attack chain.
>
> [PAUSE for completion]
>
> And we're done! In under a minute, the agent:
> - Ran 3 iterations of tool selection and execution
> - Extracted multiple findings and IOCs
> - Built a complete investigation narrative
> - Required only one human decision (the HITL approval)
>
> Compare this to a manual workflow: an analyst would spend 60+ minutes running tools, interpreting outputs, and deciding next steps.
>
> The agent did it in 60 seconds with one approval."

---

## SEGMENT 4: CLI Demo (1 minute)

> "For power users and automation, we have a comprehensive CLI.
>
> Let me show a quick single-shot analysis...
>
> [PAUSE while command runs]
>
> The CLI shows real-time progress:
> - Tool selection with confidence scores
> - Command execution on SIFT VM
> - Finding extraction
> - IOC identification
>
> And it generates a professional markdown report automatically.
>
> [PAUSE for report display]
>
> The report includes:
> - Executive summary
> - Tools used with rationale
> - Findings with severity ratings
> - IOCs (IPs, domains, file hashes)
> - Recommended next steps
>
> All formatted professionally for incident response documentation."

---

## SEGMENT 5: API Demo (45 seconds)

> "For integrations, we have a full REST API.
>
> Here's a quick curl example...
>
> [PAUSE while API call runs]
>
> The API supports:
> - Model selection via query parameters (Ollama, OpenAI, Anthropic)
> - Structured JSON responses
> - Both single analysis and iterative investigation
> - Full OpenAPI documentation
>
> This makes it easy to integrate Find Evil Agent into existing SOAR platforms or ticketing systems."

---

## SEGMENT 6: Differentiators (45 seconds)

> "What makes Find Evil Agent unique?
>
> **1. Hallucination Prevention**
> - Most LLM-based DFIR tools can hallucinate non-existent tools
> - We use semantic search + LLM ranking with confidence thresholds
> - Tools are validated against a real registry before execution
> - No other DFIR tool combines both techniques
>
> **2. Autonomous Iteration**
> - Traditional tools run once and stop
> - We automatically extract leads and follow them
> - Builds complete attack chains without manual intervention
> - Human-in-the-loop prevents wasteful investigations
>
> **3. Multi-Provider LLM Support**
> - Switch between Ollama, OpenAI, and Anthropic
> - No vendor lock-in
> - Choose the best model for your use case
>
> **4. Professional Output**
> - MITRE ATT&CK technique mapping
> - HTML and Markdown reports
> - IOC extraction and enrichment
> - Ready for incident response documentation
>
> And it's all **open source** with 606 comprehensive tests."

---

## SEGMENT 7: Closing (30 seconds)

> "Find Evil Agent is submission-ready with:
> - 98.4% test pass rate (606 out of 616 tests)
> - Docker deployment for easy setup
> - Three interfaces (CLI, API, React UI)
> - MCP server for Claude integration
> - Complete documentation and E2E testing
>
> This project demonstrates how AI agents can augment - not replace - human analysts in DFIR workflows.
>
> By combining semantic search, LLM reasoning, and human oversight, we've created a system that's both powerful and safe.
>
> Thank you for watching! Find Evil Agent is ready to help security teams investigate faster and more thoroughly.
>
> Check out the code and documentation at github.com/iffystrayer/find-evil-agent
>
> Happy hunting!"

---

## 🎙️ Recording Tips

### Audio Setup
- **Microphone:** USB mic or AirPods (decent quality)
- **Environment:** Quiet room, minimal background noise
- **Software:** Audacity (free), GarageBand (macOS), or Audition

### Recording Process
1. **Read through script 2-3 times** to familiarize
2. **Record in segments** (easier to fix mistakes)
3. **Speak slower than normal** conversation
4. **Be enthusiastic** - judges notice energy!
5. **Pause at [PAUSE]** markers to sync with video

### After Recording
1. **Normalize audio** (-3dB to -1dB)
2. **Remove clicks/pops** (noise reduction)
3. **Export as MP3 or WAV** (320kbps or higher)
4. **Sync with video** in iMovie/DaVinci Resolve

---

## ⏱️ Timing Guide

| Segment | Duration | Total |
|---------|----------|-------|
| 1. Introduction | 30s | 0:30 |
| 2. Overview | 30s | 1:00 |
| 3. React UI | 2m 30s | 3:30 |
| 4. CLI Demo | 1m | 4:30 |
| 5. API Demo | 45s | 5:15 |
| 6. Differentiators | 45s | 6:00 |
| 7. Closing | 30s | 6:30 |

**Total:** 6 minutes 30 seconds (perfect for 5-7 min target)

---

## 📝 Notes

- **[PAUSE]** markers indicate where video action happens (wait for UI to load, etc.)
- Adjust timing based on actual video length
- If running long, trim SEGMENT 5 (API demo) to 30 seconds
- If running short, expand SEGMENT 3 (main demo) with more detail

**When ready to record:** Use this script with the Playwright-generated video for professional results!
