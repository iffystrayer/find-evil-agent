# Find Evil Agent - User Guide

Welcome to the **Find Evil Agent**! This guide focuses on how DFIR analysts interact with the Autonomous Incident Response Agent, specifically detailing the cutting-edge **Human-in-the-Loop (HITL)** forensics feature. 

This guide covers usage across all three interfaces: the CLI, the Gradio Web interface, and the REST API.

---

## 🛑 What is the Human-in-The-Loop (HITL) Gateway?

A core philosophy of the "Find Evil" Agent is **Chain-of-Custody and Forensic Accountability**. The agent is immensely powerful, capable of autonomously building investigative leads and selecting DFIR tools to follow them natively on back-end SIFT workstations.

However, true DFIR requires an analyst to remain in the loop at critical execution junctures. The **HITL Gateway** solves this by physically pausing the underlying LangGraph AI state loop before the agent executes *any* autonomous execution paths. 

The machine evaluates the forensic environment and decides on a "Next Action" lead (for instance, reading a `/tmp` payload). The execution is *frozen* and handed directly to you—the human analyst—for cryptographic approval or rejection.

---

## 1. Web Application (Gradio)

The web UI is deployed via Gradio and offers a highly stylized, accessible mouse-driven experience for investigators without CLI needs.

### Quick Start
To launch the Web UI:
```bash
docker-compose up -d  # The recommended way
# OR manually
python launch_web.py --port 17000
```
Navigate to `http://localhost:17000`.

### Performing an Autonomous Investigation
1. Navigate to the **🔬 Investigative Mode** tab.
2. Provide an **Incident Description** and an overall **Investigation Goal** for the LLM to contextually trace against.
3. Select your maximum LLM iteration budget via the slider (Default: 3).
4. Click **🔍 Investigate**.

### Using the HITL Approval UI Overlay
When the backend agent generates its first intelligent forensic lead, it halts execution. In the Web UI:
- The **Status** bar will update from "Running..." to "Waiting for Human Approval."
- The **🛑 Analyst Approval Required** gateway UI dynamically appears natively on the interface.
- You can review the LLM's suggested actions.
- Click **✅ Sign & Approve** to resume the execution chain into the backend VM, or **❌ Reject & Halt** to conclude the session and generate the final forensic HTML report.

---

## 2. Command-Line Interface (CLI)

Designed for automation and power-users, the CLI leverages the dynamic `Rich` UI library to draw beautiful, terminal-native tracking applications.

### Quick Start
To trigger an investigation natively:
```bash
find-evil investigate "Provide Incident Briefing" "Analysis Goals" --max-iterations 3
```

### Navigating the HITL Shell Block
During execution, the CLI automatically hooks into the underlying state Checkpointer. When the LangGraph state requests an operator, the CLI will cleanly disrupt its standard progress loop and project:

```text
🛑 Human-In-The-Loop (HITL) Approval Required
Analyst Override Needed: The agent wants to natively follow a lead.
Target (process): Identify if tcpdump was executed...
Cryptographically sign and approve this execution path? [y/n]:
```
Typing `y` signals the application state to dynamically inject your approval natively into the API handler, and the CLI execution seamlessly reverts to the processing view to build the next iteration block.

---

## 3. High-Performance REST API

For SOC orchestration tools (like SOAR playbooks), the REST API provides robust programmatic access. Wait-blocked investigations emit stateless JSON checkpoints to cleanly decouple execution logic.

### Quick Start
Ensure the server is running (`uvicorn find_evil_agent.api.server:app --port 18000`).

Dispatch the initial investigation array via a POST request:
```bash
curl -X POST http://localhost:18000/api/v1/investigate \
  -H "Content-Type: application/json" \
  -d '{
        "incident_description": "Data exfiltration detected", 
        "analysis_goal": "Reconstruct attack graph", 
        "max_iterations": 2
      }'
```

The payload response will hit completion when either it concludes all iterations, or strikes the gateway limit, returning:
```json
{
  "success": true,
  "session_id": "8d195fe7-1c32-4fcd-a3ba-36f008fb05d6",
  "stopping_reason": "Waiting for Human Approval",
  ...
}
```

### Resuming via Checkpointer ID
Extract the distinct `session_id` from the initial return, and push an operator-approved injection back through the asynchronous endpoints via `/resume`:

```bash
curl -X POST http://localhost:18000/api/v1/investigate/8d195fe7-1c32-4fcd-a3ba-36f008fb05d6/resume \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```
This enables decoupled applications (like Slack Bots or Microsoft Teams webhooks) to safely inject "Proceed" authorizations dynamically!

---

## General DFIR Tips
- The `max_iterations` logic prevents the LLM from executing infinite run-time loops and billing overhead. Keep it below 5 for standard trace captures.
- **Fail Fast:** If the AI begins chasing dead-ends inside its log analysis reasoning loop, use the HITL interface to manually "**Reject**" the trace. This outputs the forensics payload securely without spending additional GPU inference time.
