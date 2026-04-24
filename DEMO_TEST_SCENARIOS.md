# 🧪 Demo Test Scenarios

**Purpose:** Reliable incident descriptions for demo recordings  
**Tested:** These scenarios consistently trigger HITL leads  
**Updated:** April 24, 2026

---

## 📋 Quick Reference

| Scenario | Mode | Expected HITL Leads | Demo Time |
|----------|------|---------------------|-----------|
| Ransomware Investigation | Investigative | 2-3 leads | 60-90s |
| Network Intrusion | Investigative | 2-3 leads | 60-90s |
| Data Exfiltration | Investigative | 1-2 leads | 45-60s |
| Malware Analysis | Single | None (baseline) | 30-45s |
| APT Investigation | Investigative | 3+ leads | 90-120s |

---

## 🎯 Recommended for Demo Video

### Scenario 1: Ransomware Investigation (BEST FOR DEMO)

**Why This One:**
- ✅ Reliably generates 2-3 HITL leads
- ✅ Shows clear progression (file → memory → network)
- ✅ Familiar to all security professionals
- ✅ Demonstrates both unique features well
- ✅ Completes in ~60 seconds

**Incident Description:**
```
Ransomware detected on Windows 10 endpoint. File system encrypted, ransom note found in C:\Users\Public\README_TO_DECRYPT.txt
```

**Investigation Goal:**
```
Reconstruct complete attack chain from initial access to encryption
```

**Settings:**
- Mode: Investigative
- Max Iterations: 3
- Provider: ollama (fastest for demo)
- Model: llama3.2 or gemma4:31b-cloud

**Expected Lead Progression:**
1. **First HITL:** Analyze ransom note file for IOCs
   - Priority: High
   - Confidence: ~85%
   - Tool: `strings` or `grep`
   
2. **Second HITL:** Search memory for encryption process
   - Priority: High  
   - Confidence: ~80%
   - Tool: `volatility` or `ps`

3. **Third HITL (optional):** Check network connections for C2
   - Priority: Medium
   - Confidence: ~75%
   - Tool: `netstat` or log analysis

**Demo Script:**
> "Let's investigate this ransomware incident. I'll set max iterations to 3 and start the investigation... The agent is analyzing the initial incident... And here's our first HITL lead - it wants to analyze the ransom note for IOCs with 85% confidence. I'll approve... The investigation continues, now looking at memory... Another lead appears - checking for the encryption process. I'll approve this too... And we're done! Complete attack chain in 60 seconds with 2 human approvals."

---

### Scenario 2: Network Intrusion (ALTERNATIVE)

**Incident Description:**
```
Suspicious network traffic detected from internal host 192.168.1.50 to unknown external IP 203.0.113.42 on port 443
```

**Investigation Goal:**
```
Identify compromised host, determine scope of intrusion, find initial access vector
```

**Settings:**
- Mode: Investigative
- Max Iterations: 3

**Expected Leads:**
1. Analyze network logs for connection timeline
2. Check process list on source host
3. Search for lateral movement indicators

**Demo Time:** ~60-75 seconds

---

### Scenario 3: Data Exfiltration (QUICK DEMO)

**Incident Description:**
```
Large data transfer detected to cloud storage service. 500GB uploaded from finance department workstation
```

**Investigation Goal:**
```
Identify exfiltrated files, determine if authorized or malicious
```

**Settings:**
- Mode: Investigative
- Max Iterations: 2

**Expected Leads:**
1. Check file access logs
2. Analyze uploaded file metadata

**Demo Time:** ~45-60 seconds

---

## 🔧 Single Analysis Baseline (No HITL)

Use this to show the difference between single and investigative modes:

**Incident Description:**
```
Suspicious file /tmp/malware.exe detected by antivirus
```

**Analysis Goal:**
```
Determine if file is malicious
```

**Settings:**
- Mode: Single Analysis
- No max iterations (runs once)

**Expected:**
- No HITL dialog (completes immediately)
- Basic analysis with findings
- Shows contrast with investigative mode

**Demo Time:** ~30 seconds

---

## 🚀 Advanced Scenario (If Extra Time)

### APT Investigation (Shows Full Capability)

**Incident Description:**
```
Advanced persistent threat detected. Indicators of compromise include: suspicious scheduled task, encoded PowerShell in registry, outbound connections to known APT infrastructure
```

**Investigation Goal:**
```
Full attack chain reconstruction from initial compromise to current persistence mechanisms
```

**Settings:**
- Mode: Investigative
- Max Iterations: 5
- Provider: anthropic or openai (for best lead extraction)

**Expected:**
- 3-5 HITL leads
- Complex investigation chain
- Multiple tool types (registry, process, network)

**Demo Time:** 90-120 seconds

**Warning:** Longer, use only if you have 7+ minutes for full demo

---

## 📊 CLI Demo Commands

### Quick Analyze (30 seconds)

```bash
uv run find-evil analyze \
  "Suspicious network traffic to unknown IP 203.0.113.42" \
  "Identify potential C2 communication" \
  -o /tmp/analysis.md -v
```

### Investigate with HITL (CLI prompts for approval)

```bash
uv run find-evil investigate \
  "Ransomware detected on endpoint" \
  "Reconstruct attack chain" \
  -n 3 -v
```

**Expected:**
- Shows iteration progress in terminal
- Prompts: "Approve this lead? (y/n)"
- User types 'y' to continue
- Professional Rich UI output

---

## 🌐 API Demo Commands

### Single Analysis

```bash
curl -X POST "http://localhost:18000/api/v1/analyze?provider=ollama&model=llama3.2" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_description": "Malware detected in /tmp directory",
    "analysis_goal": "Identify malicious files and their origin"
  }' | jq .
```

### Investigative Mode (Returns session_id for HITL)

```bash
curl -X POST "http://localhost:18000/api/v1/investigate" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_description": "Data exfiltration detected",
    "analysis_goal": "Identify exfiltrated data",
    "max_iterations": 3
  }' | jq .
```

**Note:** HITL approval requires follow-up POST to `/investigate/{session_id}/resume`

---

## 🎬 Recording Tips Per Scenario

### For Ransomware Demo (Recommended)

**Timing:**
- 0:00-0:10 - Explain scenario and enter descriptions
- 0:10-0:25 - First iteration running
- 0:25-0:40 - First HITL appears, explain lead, approve
- 0:40-0:55 - Second iteration running
- 0:55-1:10 - Second HITL appears, explain, approve
- 1:10-1:20 - Final results display
- 1:20-1:30 - Highlight attack chain narrative

**Narration Focus:**
- Emphasize speed (60 seconds vs 60 minutes manual)
- Point out confidence scores in HITL
- Show how leads connect logically
- Highlight investigative reasoning

### For CLI Demo

**Timing:**
- 0:00-0:05 - Type command (show full command)
- 0:05-0:30 - Command runs (narrate what's happening)
- 0:30-0:40 - Show report output
- 0:40-0:50 - Scroll through key sections

**Narration Focus:**
- "Real-time progress updates"
- "Confidence scores shown inline"
- "Professional markdown report"
- "Ready for automation/scripts"

### For API Demo

**Timing:**
- 0:00-0:05 - Show curl command
- 0:05-0:10 - Execute request
- 0:10-0:30 - Show JSON response (piped through jq)
- 0:30-0:45 - Highlight key fields

**Narration Focus:**
- "Model selection via query params"
- "Structured JSON response"
- "Easy to integrate with SOAR"
- "Full OpenAPI documentation available"

---

## 🧪 Pre-Demo Testing Checklist

Test these scenarios before recording to ensure reliability:

### React UI Test
- [ ] Ransomware scenario generates 2+ leads
- [ ] HITL dialog displays correctly
- [ ] Approve button works
- [ ] Investigation completes successfully
- [ ] Results display with findings and IOCs
- [ ] No console errors (F12)

### CLI Test
- [ ] Analyze command completes
- [ ] Verbose output shows progress
- [ ] Report file created
- [ ] Report is readable markdown
- [ ] Investigate command prompts for approval
- [ ] Can approve/reject leads

### API Test
- [ ] Health endpoint returns 200
- [ ] Analyze endpoint returns JSON
- [ ] Response includes session_id
- [ ] Response includes findings array
- [ ] No 500 errors

### Performance Test
- [ ] Analysis completes in <60 seconds
- [ ] Investigation (3 iterations) completes in <90 seconds
- [ ] No timeouts or hanging requests
- [ ] LLM responses are reasonable (not garbage)

---

## 🐛 Troubleshooting Demo Issues

### HITL Not Triggering

**Symptom:** Investigation completes without showing HITL dialog

**Causes:**
1. LLM not generating leads (try different model)
2. Max iterations set to 1 (increase to 3+)
3. Investigation goal too simple (use more complex scenario)

**Fix:**
- Use ransomware scenario (most reliable)
- Set max_iterations to 3
- Use Ollama with gemma4:31b-cloud
- Check that `investigate` endpoint is used (not `analyze`)

### Investigation Too Fast

**Symptom:** HITL dialog appears and disappears immediately

**Causes:**
1. Auto-approval enabled somewhere
2. Frontend state management issue

**Fix:**
- Refresh browser (Ctrl+Shift+R)
- Check console for errors
- Restart Docker containers

### Investigation Too Slow

**Symptom:** Each iteration takes 2+ minutes

**Causes:**
1. LLM provider slow (OpenAI/Anthropic API latency)
2. SIFT VM network latency
3. Complex tool execution

**Fix:**
- Use Ollama (local, faster)
- Use simpler scenario
- Reduce max_iterations to 2

### No Results Display

**Symptom:** Investigation completes but no results shown

**Causes:**
1. Frontend state update issue
2. API response malformed

**Fix:**
- Check browser console for errors
- Check API logs: `docker logs find-evil-api`
- Restart frontend container

---

## 📝 Sample HITL Lead (For Reference)

When HITL dialog appears, you should see something like:

```
New Investigative Lead Discovered

Priority: High
Confidence: 85%

Rationale: Analysis of the ransom note file revealed potential 
Bitcoin wallet addresses and contact email. Should extract these 
IOCs and correlate with threat intelligence databases.

Recommended Tool: strings
Estimated Time: 15-20 seconds

[ Reject ]  [ Approve and Continue ]
```

**What to Say:**
> "Here's the HITL system in action. The agent has identified a high-priority lead with 85% confidence. It wants to extract IOCs from the ransom note using the 'strings' tool. I can see the rationale - there might be Bitcoin wallets or contact info. I'll approve this lead... and the investigation continues."

---

## ✅ Demo Success Criteria

Your demo scenario is working when:

- ✅ HITL dialog appears at predictable times
- ✅ Lead details are clear and sensible
- ✅ Approval button works smoothly
- ✅ Investigation continues after approval
- ✅ Final results are comprehensive
- ✅ Total time is reasonable (<2 minutes)
- ✅ No errors or crashes
- ✅ Professional appearance throughout

---

**Use Ransomware Scenario for safest demo recording!** 🎯
