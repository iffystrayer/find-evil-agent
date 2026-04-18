# Demo Video Script - Find Evil Agent

**Duration:** 2-3 minutes  
**Format:** Screen recording with voiceover  
**Resolution:** 1920x1080 or 4K  
**Tool:** macOS screen recording (Cmd+Shift+5) or QuickTime

---

## Pre-Recording Checklist

- [ ] Close unnecessary applications and browser tabs
- [ ] Enable "Do Not Disturb" mode (disable notifications)
- [ ] Clear browser cache and history
- [ ] Set browser zoom to 100%
- [ ] Prepare terminal with clean prompt
- [ ] Verify infrastructure is running:
  - [ ] Ollama: http://192.168.12.124:11434
  - [ ] SIFT VM: 192.168.12.101:22
  - [ ] Web UI: http://localhost:17000
- [ ] Test microphone audio quality
- [ ] Position windows for screen recording
- [ ] Have demo scenarios ready to copy/paste

---

## Recording Setup

**Screen Layout:**
- Terminal: Left half of screen (for CLI demo)
- Browser: Right half initially, then full screen
- Keep mouse movements smooth and deliberate
- Use spotlight/highlight cursor (macOS: System Preferences > Accessibility > Display > Cursor)

**Audio:**
- Speak clearly and at moderate pace
- Pause between sections
- Emphasize key features: "hallucination prevention" and "autonomous investigation"

---

## Video Structure

### SECTION 1: Introduction (0:00 - 0:15)

**Visual:** Title slide or main README.md on screen

**Voiceover:**
```
"Find Evil Agent is an autonomous AI incident response system 
for SANS SIFT Workstation. It provides three interfaces designed 
for everyone: CLI for power users, Web UI for entry-level analysts, 
and REST API for developers."
```

**On-screen text:**
- "Find Evil Agent"
- "Autonomous AI Incident Response"
- "3 Interfaces for Everyone"

---

### SECTION 2: CLI Demo (0:15 - 0:45)

**Visual:** Terminal window, split-screen with browser

**Actions:**
1. Show terminal prompt
2. Type command (or paste):
   ```bash
   find-evil analyze \
     "Ransomware detected encrypting files on Windows server" \
     "Identify malicious processes and IOCs" \
     -o report.html
   ```
3. Show Rich terminal UI with progress bars
4. Wait for completion message
5. Show "Report saved to report.html" message

**Voiceover:**
```
"Power users can use the command-line interface. Here, we're analyzing 
a ransomware incident. Find Evil Agent automatically selects the right 
forensic tools, executes them on the SIFT workstation, and generates a 
professional incident response report in under 90 seconds."
```

**Timing:** 30 seconds total

---

### SECTION 3: CLI Report (0:45 - 1:00)

**Visual:** Browser opens report.html, scroll through report

**Actions:**
1. `open report.html` in terminal
2. Browser opens showing professional HTML report
3. Scroll through:
   - Executive Summary
   - MITRE ATT&CK mapping
   - IOC tables
   - Interactive graph (show briefly)

**Voiceover:**
```
"The report includes an executive summary, MITRE ATT&CK technique 
mapping, IOC tables, and an interactive attack chain visualization."
```

**Timing:** 15 seconds

---

### SECTION 4: Web UI Launch (1:00 - 1:15)

**Visual:** Terminal switches to full screen, then browser

**Actions:**
1. Show terminal
2. Type: `find-evil web`
3. Show output: "Running on local URL: http://127.0.0.1:17000"
4. Browser opens to web UI
5. Show clean, professional Gradio interface

**Voiceover:**
```
"For entry-level analysts, we provide a web interface. Simply launch 
the web UI and access it from any browser."
```

**Timing:** 15 seconds

---

### SECTION 5: Single Analysis Demo (1:15 - 1:45)

**Visual:** Browser full screen, showing Single Analysis tab

**Actions:**
1. Click on "Incident Description" field
2. Paste/type: "Ransomware detected encrypting files on Windows server. Multiple files have .encrypted extension."
3. Click on "Analysis Goal" field
4. Type: "Identify malicious processes and IOCs for containment"
5. Ensure "HTML" is selected in format dropdown
6. Click "Analyze Incident" button
7. Show real-time progress bar
8. Show status updates: "Selecting tools...", "Executing analysis...", "Generating report..."

**Voiceover:**
```
"Let's analyze the same ransomware incident through the web interface. 
We simply describe the incident and our analysis goal. The system 
handles everything automatically with real-time progress tracking."
```

**Timing:** 30 seconds (may need to speed up progress bar in editing)

---

### SECTION 6: Interactive Report (1:45 - 2:15)

**Visual:** Report preview displayed in browser

**Actions:**
1. Report appears in preview area
2. Scroll to interactive graph
3. Zoom in on graph
4. Click a node (shows highlighting)
5. Hover over node (shows tooltip with details)
6. Drag node to reposition
7. Show critical path (red edges)
8. Pan around graph
9. Zoom back out

**Voiceover:**
```
"The report preview shows up instantly with an interactive attack chain 
graph. You can click nodes to highlight connections, zoom and pan to 
explore the attack, and see the critical path in red. Each node shows 
detailed information including severity, type, and occurrence count."
```

**Timing:** 30 seconds

---

### SECTION 7: Investigative Mode (2:15 - 2:45)

**Visual:** Switch to Investigative Mode tab

**Actions:**
1. Click "Investigative Mode" tab
2. Paste incident: "Suspicious PowerShell execution detected in Windows event logs. Base64-encoded command observed."
3. Type goal: "Reconstruct complete attack chain"
4. Set iteration slider to 3
5. Select "HTML" format
6. Click "Start Investigation"
7. Show multi-iteration progress:
   - "Iteration 1 of 3: Analyzing initial evidence..."
   - "Following leads: Found PowerShell download cradle"
   - "Iteration 2 of 3: Investigating network connections..."
   - "Following leads: C2 communication detected"
   - "Iteration 3 of 3: Reconstructing full attack chain..."
8. Show completed investigation report (preview)

**Voiceover:**
```
"Investigative Mode demonstrates our autonomous reasoning capability. 
The system automatically follows leads across multiple iterations, 
reconstructing the complete attack chain from initial PowerShell 
execution through C2 communication and data exfiltration. This is one 
of our two unique features: autonomous investigative reasoning."
```

**Timing:** 30 seconds

---

### SECTION 8: About & Features (2:45 - 3:00)

**Visual:** Click "About" tab, scroll through features

**Actions:**
1. Click "About" tab
2. Scroll through:
   - Two unique features section
   - Hallucination prevention explanation
   - Autonomous investigation explanation
   - Architecture overview
   - MITRE ATT&CK coverage table (11 techniques)
   - Three interfaces comparison table

**Voiceover:**
```
"Find Evil Agent provides two unique innovations: hallucination-resistant 
tool selection through two-stage validation, and autonomous investigative 
reasoning that follows leads like a real analyst. The system covers 11 
MITRE ATT&CK techniques across 5 tactics and has been tested with 265 
comprehensive tests achieving 94% success rate."
```

**Timing:** 15 seconds

---

### SECTION 9: Closing (3:00 - 3:15)

**Visual:** Split screen showing CLI, Web UI, and API docs

**Actions:**
1. Show terminal with CLI command
2. Show browser with web UI
3. Show API documentation (FastAPI OpenAPI docs)
4. Return to project README or main screen

**Voiceover:**
```
"Find Evil Agent delivers professional incident response reports in 60 to 90 
seconds, with three interfaces for power users, entry-level analysts, and 
developers. It's production-ready, open source, and built for the SANS 
SIFT Workstation ecosystem. Thank you for watching."
```

**On-screen text:**
- "3 Interfaces"
- "60-90 Second Analysis"
- "Production Ready"
- "Open Source"
- GitHub URL: github.com/iffystrayer/find-evil-agent

**Timing:** 15 seconds

---

## Post-Recording

### Editing Checklist

- [ ] Trim dead air at beginning and end
- [ ] Speed up slow sections (progress bars) to 1.5x-2x
- [ ] Ensure audio is clear and synced
- [ ] Add title card at beginning (optional)
- [ ] Add closing card with GitHub link (optional)
- [ ] Export to MP4 format (H.264, 1080p or 4K)
- [ ] Check file size (target: <100MB for upload)

### File Naming

```
find_evil_agent_demo_v1.mp4
```

### Upload Locations

1. **YouTube:** (unlisted or public)
   - Title: "Find Evil Agent - Autonomous AI Incident Response Demo"
   - Description: Include GitHub link and feature highlights
   - Tags: DFIR, incident response, AI, automation, SANS, SIFT

2. **Vimeo:** (backup)

3. **DevPost:** Upload directly to hackathon submission

4. **GitHub:** Consider adding to releases or embedding in README

---

## Alternative: Shorter Version (60 seconds)

If 3 minutes is too long, create a condensed version:

**0:00-0:10:** Introduction + CLI demo (fast)  
**0:10-0:30:** Web UI single analysis with graph interaction  
**0:30-0:50:** Investigative mode showing autonomous iteration  
**0:50-1:00:** Closing with three interfaces showcase

---

## Recording Commands

**macOS Screen Recording:**
```bash
# Start recording (Cmd+Shift+5)
# Select "Record Entire Screen" or "Record Selected Portion"
# Click "Options" to enable microphone
# Click "Record"
```

**Via Terminal (no audio):**
```bash
# Record screen to video file
screencapture -v docs/videos/demo_raw.mov

# Or use FFmpeg for screen + audio
ffmpeg -f avfoundation -i "1:0" -framerate 30 -video_size 1920x1080 \
  -t 180 docs/videos/demo_raw.mp4
```

**QuickTime Player:**
1. File > New Screen Recording
2. Click dropdown next to record button
3. Select microphone
4. Click record button
5. Stop recording when done

---

## Audio Script Only (for reference)

```
INTRO (15s):
Find Evil Agent is an autonomous AI incident response system for SANS 
SIFT Workstation. It provides three interfaces designed for everyone: 
CLI for power users, Web UI for entry-level analysts, and REST API for 
developers.

CLI DEMO (30s):
Power users can use the command-line interface. Here, we're analyzing a 
ransomware incident. Find Evil Agent automatically selects the right 
forensic tools, executes them on the SIFT workstation, and generates a 
professional incident response report in under 90 seconds.

CLI REPORT (15s):
The report includes an executive summary, MITRE ATT&CK technique mapping, 
IOC tables, and an interactive attack chain visualization.

WEB LAUNCH (15s):
For entry-level analysts, we provide a web interface. Simply launch the 
web UI and access it from any browser.

SINGLE ANALYSIS (30s):
Let's analyze the same ransomware incident through the web interface. We 
simply describe the incident and our analysis goal. The system handles 
everything automatically with real-time progress tracking.

INTERACTIVE REPORT (30s):
The report preview shows up instantly with an interactive attack chain 
graph. You can click nodes to highlight connections, zoom and pan to 
explore the attack, and see the critical path in red. Each node shows 
detailed information including severity, type, and occurrence count.

INVESTIGATIVE MODE (30s):
Investigative Mode demonstrates our autonomous reasoning capability. The 
system automatically follows leads across multiple iterations, 
reconstructing the complete attack chain from initial PowerShell execution 
through C2 communication and data exfiltration. This is one of our two 
unique features: autonomous investigative reasoning.

ABOUT (15s):
Find Evil Agent provides two unique innovations: hallucination-resistant 
tool selection through two-stage validation, and autonomous investigative 
reasoning that follows leads like a real analyst. The system covers 11 
MITRE ATT&CK techniques across 5 tactics and has been tested with 265 
comprehensive tests achieving 94% success rate.

CLOSING (15s):
Find Evil Agent delivers professional incident response reports in 60 to 
90 seconds, with three interfaces for power users, entry-level analysts, 
and developers. It's production-ready, open source, and built for the 
SANS SIFT Workstation ecosystem. Thank you for watching.
```

---

**Total Video Length:** 3:00-3:15  
**Upload to:** docs/videos/demo.mp4

---

## Success Criteria

- [ ] Video is 2-3 minutes long
- [ ] Audio is clear and professional
- [ ] All three interfaces demonstrated
- [ ] Two unique features highlighted
- [ ] Interactive graph shown in detail
- [ ] Investigative mode shows autonomous iteration
- [ ] Professional appearance throughout
- [ ] No errors or failed operations shown
- [ ] File size appropriate for upload (<100MB)
- [ ] GitHub link visible at end

---

**Ready to record! All materials prepared.**
