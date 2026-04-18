# Testing Guide - Find Evil Agent Demo Preparation

**Date:** April 17, 2026  
**Status:** ✅ Web UI fixed and running at http://localhost:17000  
**Purpose:** Test both CLI and Web UI for demo recording

---

## ✅ COMPLETED

1. **Web UI Backend Fixes** (Commit 7efb056)
   - Fixed orchestrator method calls
   - Fixed reporter method signatures
   - Web UI now fully functional

2. **Web UI Running**
   - Port: 17000
   - URL: http://localhost:17000
   - Browser opened automatically

---

## 🧪 TESTING SEQUENCE

### Part 1: Web UI Testing (30 minutes)

#### Test 1: Single Analysis Workflow

**Steps:**
1. Open http://localhost:17000 (should already be open)
2. Go to "Single Analysis" tab
3. Fill in:
   - **Incident:** `Ransomware detected encrypting files on Windows server. Multiple files have .encrypted extension.`
   - **Goal:** `Identify malicious processes, extract IOCs, and determine encryption method`
   - **Format:** HTML
4. Click "🚀 Analyze" button
5. Watch real-time progress bar
6. Wait for completion (60-90 seconds)

**Expected Results:**
- ✅ Progress bar updates with status messages
- ✅ Report preview appears in HTML format
- ✅ Interactive graph visible
- ✅ Download file available
- ✅ Status shows: Session ID, findings count, duration

**Screenshots to Capture:**
1. Empty form (before submission)
2. Progress bar active (during analysis)
3. Complete report with graph (after analysis)
4. Graph interaction (click/zoom/drag nodes)

---

#### Test 2: Investigative Mode Workflow

**Steps:**
1. Click "Investigative Mode" tab
2. Fill in:
   - **Incident:** `Suspicious PowerShell execution detected in Windows event logs. Base64-encoded command observed.`
   - **Goal:** `Reconstruct complete attack chain from initial access to impact`
   - **Iterations:** 3
   - **Format:** HTML
3. Click "🔍 Investigate" button
4. Watch multi-iteration progress
5. Wait for completion (3-5 minutes for 3 iterations)

**Expected Results:**
- ✅ Progress updates for each iteration
- ✅ "Following leads..." messages
- ✅ Complete investigation report
- ✅ Timeline showing all iterations
- ✅ Critical path in graph

**Screenshots to Capture:**
1. Investigative mode form filled
2. Multi-iteration progress (iteration 2 of 3)
3. Complete investigation report
4. Timeline section showing iterations

---

#### Test 3: About Tab Review

**Steps:**
1. Click "About" tab
2. Scroll through all content
3. Verify completeness

**Expected Content:**
- ✅ Two unique features explained
- ✅ Architecture table (5 agents)
- ✅ Professional reporting features
- ✅ MITRE ATT&CK coverage (11 techniques)
- ✅ Three interfaces comparison
- ✅ Performance vs Valhuntir table
- ✅ Developer info and GitHub link

**Screenshots to Capture:**
1. About tab - features section
2. MITRE ATT&CK table
3. Performance comparison table

---

### Part 2: CLI Testing (15 minutes)

The CLI is fully functional and can be recorded separately or alongside Web UI.

#### CLI Test 1: Single Analysis

```bash
# Activate environment
source .venv/bin/activate

# Run analysis
find-evil analyze \
  "Ransomware detected encrypting files on Windows server" \
  "Identify malicious processes and IOCs" \
  -o reports/cli_ransomware.html

# View report
open reports/cli_ransomware.html
```

**Expected:**
- Rich terminal UI with progress
- Report saved message
- HTML report opens in browser
- Interactive graph visible

**Record This:**
- Terminal recording (asciinema or screen capture)
- Report in browser

---

#### CLI Test 2: Investigative Mode

```bash
find-evil investigate \
  "Suspicious PowerShell execution detected in event logs" \
  "Reconstruct complete attack chain" \
  -n 3 \
  -o reports/cli_investigation.html

# View report
open reports/cli_investigation.html
```

**Expected:**
- Multi-iteration progress in terminal
- Complete investigation report
- Timeline spanning 3 iterations

---

### Part 3: Graph Interaction Testing (10 minutes)

For any HTML report (CLI or Web UI generated):

**Test Actions:**
1. **Zoom:** Scroll to zoom in/out on graph
2. **Pan:** Click and drag background to pan
3. **Select Node:** Click any node to highlight connections
4. **Hover:** Hover over node to see tooltip
5. **Drag Node:** Click and drag node to reposition
6. **Critical Path:** Verify thick red edges show critical path
7. **Entry Points:** Verify highlighted entry point nodes
8. **Legend:** Check color/shape legend is visible

**Screenshots Needed:**
- Graph overview (full view)
- Graph zoomed in (showing details)
- Node selected (showing highlighting)
- Tooltip visible (showing node details)

---

## 📸 SCREENSHOT CHECKLIST

### Web UI (9 screenshots minimum)

1. ✅ **Main interface** - Empty state, all three tabs visible
2. ✅ **Single analysis - Input filled** - Before clicking Analyze
3. ✅ **Single analysis - Progress** - During analysis
4. ✅ **Single analysis - Complete** - Report preview with graph
5. ✅ **Graph interaction** - Node selected/tooltip
6. ✅ **Investigative mode - Form** - Before clicking Investigate
7. ✅ **Investigative mode - Progress** - Multi-iteration status
8. ✅ **Investigative mode - Complete** - Full investigation report
9. ✅ **About tab** - Features and tables

### CLI (3 screenshots minimum)

10. ✅ **CLI terminal** - Running analysis command
11. ✅ **CLI terminal** - Investigative mode with iterations
12. ✅ **CLI report** - HTML report opened from CLI

### Total: 12 core screenshots

---

## 🎥 DEMO VIDEO RECORDING

Once testing is complete and working:

### Recording Setup

**Tools:**
- macOS: Cmd+Shift+5 (screen recording with audio)
- Alternative: QuickTime Player → File → New Screen Recording
- Terminal recording: asciinema (optional for CLI-only segment)

**Preparation:**
1. Close unnecessary windows
2. Enable Do Not Disturb mode
3. Clear browser cache/history
4. Position windows for recording
5. Test microphone audio
6. Prepare demo scenarios (copy/paste ready)

---

### Video Structure (3 minutes)

**Segment 1: Introduction (15s)**
- Show README or title screen
- Voiceover: "Find Evil Agent - Three interfaces for everyone"

**Segment 2: CLI Demo (45s)**
- Terminal: Run single analysis
- Show progress
- Open HTML report
- Show graph interaction

**Segment 3: Web UI Demo (90s)**
- Browser: Navigate to web UI
- Single Analysis workflow
- Show real-time progress
- Show report preview
- Graph interaction
- Quick Investigative Mode demo

**Segment 4: Features Highlight (20s)**
- About tab showing two unique features
- MITRE coverage
- Three interfaces

**Segment 5: Closing (10s)**
- Split screen: CLI, Web, API docs
- Voiceover: "Production-ready, open source"
- Show GitHub link

---

## 🐛 TROUBLESHOOTING

### If Web UI Fails

**Check logs:**
```bash
tail -50 /tmp/web_ui_fixed.log
```

**Verify infrastructure:**
```bash
# Ollama
curl -s http://192.168.12.124:11434/api/tags | head -5

# SIFT VM
nc -zv 192.168.12.101 22

# Configuration
find-evil config
```

**Restart web UI:**
```bash
pkill -f "find-evil web"
find-evil web --port 17000
```

---

### If Analysis Takes Too Long

**Normal Times:**
- Single analysis: 60-90 seconds
- 3 iterations: 3-5 minutes
- 5 iterations: 5-8 minutes

**If stuck:**
- Check Ollama is responding: `curl http://192.168.12.124:11434/api/tags`
- Check SIFT VM access: `nc -zv 192.168.12.101 22`
- Check logs: `tail -f /tmp/web_ui_fixed.log`

---

### If Graph Doesn't Render

**Check:**
1. Report format is HTML (not Markdown)
2. Browser JavaScript is enabled
3. D3.js library loaded (check browser console)
4. Graph data exists in HTML (search for `<script>` with graph data)

**Fallback:**
- Generate report via CLI
- Open in different browser (Chrome, Firefox, Safari)

---

## ✅ SUCCESS CRITERIA

### Web UI Working
- [ ] Single analysis completes successfully
- [ ] Report preview displays HTML correctly
- [ ] Interactive graph renders and responds
- [ ] Download file is created and accessible
- [ ] Investigative mode completes multiple iterations
- [ ] About tab shows all content
- [ ] No JavaScript errors in browser console
- [ ] Progress bars update in real-time

### CLI Working
- [ ] Commands execute without errors
- [ ] Reports generated successfully
- [ ] HTML reports open in browser
- [ ] Graphs are interactive

### Demo Ready
- [ ] All test scenarios working
- [ ] Screenshots captured (12 minimum)
- [ ] Demo script prepared
- [ ] Recording tools tested
- [ ] Audio quality verified
- [ ] Browser/terminal positioned for recording

---

## 📋 QUICK REFERENCE

**Web UI:** http://localhost:17000

**CLI Commands:**
```bash
# Single analysis
find-evil analyze "<incident>" "<goal>" -o report.html

# Investigation
find-evil investigate "<incident>" "<goal>" -n 3 -o investigation.html

# Config check
find-evil config

# Stop web UI
pkill -f "find-evil web"
```

**Test Scenarios:**
1. Ransomware analysis (single)
2. PowerShell investigation (iterative, 3 iterations)
3. About tab review

---

## 🚀 NEXT STEPS AFTER TESTING

Once all tests pass:

1. ✅ Capture all screenshots
2. ✅ Record demo video (3 min)
3. ✅ Review and edit video
4. ✅ Export to MP4
5. ✅ Prepare DevPost submission
6. ✅ Update README with screenshots
7. ✅ Create "Read the Docs" documentation (optional, 4-6 hours)

---

**Current Status:** Web UI fixed and ready for testing. CLI fully functional. Begin testing now!
