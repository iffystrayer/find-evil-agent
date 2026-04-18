# Find Evil Agent - Demo Scenarios

**Purpose:** Test scenarios for web UI demonstration and demo video recording

## Scenario 1: Ransomware Analysis (Single Analysis Mode)

**Tab:** Single Analysis  
**Format:** HTML

**Incident Description:**
```
Ransomware detected encrypting files on Windows server. Multiple files have .encrypted extension. Server performance degraded significantly.
```

**Analysis Goal:**
```
Identify malicious processes, extraction points, and IOCs for containment
```

**Expected Output:**
- Professional HTML report with MITRE ATT&CK mapping
- IOC tables (processes, files, network connections)
- Executive summary with severity assessment
- Interactive graph showing attack chain
- Recommendations for containment

**Test Validates:**
- Single analysis workflow
- Report generation and preview
- Graph visualization
- Download functionality

---

## Scenario 2: PowerShell Attack Chain (Investigative Mode)

**Tab:** Investigative Mode  
**Iterations:** 3  
**Format:** HTML

**Incident Description:**
```
Suspicious PowerShell execution detected in Windows event logs. Base64-encoded command observed. User reported unusual system behavior.
```

**Investigation Goal:**
```
Reconstruct complete attack chain from initial access to impact
```

**Expected Output:**
- Multi-iteration investigation report
- Complete attack timeline
- Entry points and lateral movement paths
- MITRE techniques across execution, persistence, and C2 phases
- Critical path visualization in graph
- Prioritized recommendations by urgency

**Test Validates:**
- Investigative mode (multiple iterations)
- Autonomous lead following
- Real-time progress tracking
- Comprehensive timeline generation
- Critical path identification

---

## Scenario 3: Data Breach Investigation (Investigative Mode)

**Tab:** Investigative Mode  
**Iterations:** 4  
**Format:** HTML

**Incident Description:**
```
Data breach detected. Unauthorized access to customer database. Large data transfer observed to external IP. Credentials may be compromised.
```

**Investigation Goal:**
```
Identify initial access vector, credential theft method, and data exfiltration details
```

**Expected Output:**
- Complete breach reconstruction
- Credential access techniques (MITRE T1003)
- Network IOCs (external IPs, domains)
- Data exfiltration timeline
- Evidence citations with tool references
- Multi-stage recommendations (immediate, urgent, scheduled)

**Test Validates:**
- Complex multi-stage investigation
- Credential dumping detection
- Network forensics integration
- Evidence chain of custody
- Professional reporting for stakeholders

---

## Scenario 4: Memory Forensics (Single Analysis Mode)

**Tab:** Single Analysis  
**Format:** Markdown

**Incident Description:**
```
Memory dump collected from compromised system. Malware suspected but not identified by AV. Process injection indicators present.
```

**Analysis Goal:**
```
Analyze memory dump for malicious processes and injection techniques
```

**Expected Output:**
- Markdown report for documentation
- Process injection detection (MITRE T1055)
- Memory artifacts and IOCs
- Malware family identification
- Recommended next steps

**Test Validates:**
- Markdown output format
- Memory forensics tool selection
- Process injection detection
- MITRE mapping for defense evasion

---

## Screenshot Checklist

### Web UI Screenshots Needed

1. **Main Interface**
   - [ ] Landing page with three tabs visible
   - [ ] Clean, professional appearance
   - [ ] Gradio Soft theme visible

2. **Single Analysis Tab - Empty State**
   - [ ] Input fields visible
   - [ ] Format dropdown showing HTML/Markdown options
   - [ ] Clear placeholder text

3. **Single Analysis Tab - In Progress**
   - [ ] Progress bar active
   - [ ] Status messages updating
   - [ ] Professional loading UI

4. **Single Analysis Tab - Completed**
   - [ ] Report preview visible (HTML rendering)
   - [ ] Interactive graph displayed
   - [ ] Download button available

5. **Interactive Graph**
   - [ ] Node colors by severity (red, orange, yellow, blue, gray)
   - [ ] Node shapes by type (circle, square, triangle, diamond)
   - [ ] Entry points highlighted
   - [ ] Critical path visible
   - [ ] Zoom/pan controls

6. **Graph Interactions**
   - [ ] Click node to highlight connections
   - [ ] Hover tooltip with details
   - [ ] Drag node to reposition

7. **Investigative Mode Tab**
   - [ ] Iteration slider (2-10)
   - [ ] Multiple status updates during investigation
   - [ ] Multi-iteration progress tracking

8. **About Tab**
   - [ ] Two unique features explained
   - [ ] Architecture diagram/description
   - [ ] MITRE ATT&CK coverage table
   - [ ] Three interfaces comparison

9. **Download Functionality**
   - [ ] Downloaded file with timestamp
   - [ ] File opens correctly in browser

10. **Mobile Responsive** (Optional)
    - [ ] Mobile view (iPhone/iPad simulator)
    - [ ] Touch-friendly controls

---

## Demo Video Script (2-3 minutes)

### Introduction (15 seconds)
"Find Evil Agent provides three interfaces for everyone: CLI for power users, Web UI for entry-level analysts, and REST API for developers."

### CLI Demo (30 seconds)
```bash
# Terminal window
find-evil analyze "Ransomware detected encrypting files" \
  "Identify malicious processes and IOCs" \
  -o report.html
```
- Show Rich terminal UI with progress
- Show report generated message
- Open report.html in browser

### Web UI Demo (60 seconds)
```bash
# Launch web UI
find-evil web
```
- Browser opens to localhost:17000
- Navigate to Single Analysis tab
- Fill in Scenario 1 (Ransomware)
- Click "Analyze Incident"
- Show real-time progress bar
- Show report preview with interactive graph
- Click graph node, drag to reposition
- Zoom in/out demonstration
- Click download button

### Investigative Mode Demo (45 seconds)
- Switch to Investigative Mode tab
- Fill in Scenario 2 (PowerShell)
- Set iterations to 3
- Click "Start Investigation"
- Show multi-iteration status updates
- Highlight autonomous lead following
- Show complete investigation report
- Show critical path in graph

### About Tab (15 seconds)
- Switch to About tab
- Scroll through features
- Show MITRE ATT&CK coverage
- Show three interfaces comparison

### Closing (15 seconds)
"Find Evil Agent delivers professional incident response reports in 60-90 seconds, with hallucination prevention and autonomous investigation. Ready for production."

---

## Technical Testing Checklist

### Before Demo Recording

- [ ] Verify Ollama is running (http://192.168.12.124:11434)
- [ ] Verify SIFT VM is accessible (192.168.12.101:22)
- [ ] Verify Langfuse is enabled
- [ ] Clear browser cache
- [ ] Close unnecessary browser tabs
- [ ] Test audio recording quality
- [ ] Test screen resolution (1920x1080 or 4K)
- [ ] Prepare terminal with clean prompt
- [ ] Create dedicated reports/ directory for demo outputs
- [ ] Test network connectivity (no lag during demo)

### During Demo

- [ ] Use Cmd+Shift+5 for macOS screen recording
- [ ] Record in 1920x1080 or higher
- [ ] Enable microphone for narration
- [ ] Disable notifications (Do Not Disturb mode)
- [ ] Use Chrome/Firefox for web UI (consistent rendering)
- [ ] Keep mouse movements smooth and deliberate
- [ ] Pause appropriately between actions

### After Demo

- [ ] Export video to MP4 format
- [ ] Check video quality and audio sync
- [ ] Trim any dead air or mistakes
- [ ] Add title card (optional)
- [ ] Export screenshots as PNG (1920x1080)
- [ ] Organize in docs/images/ directory

---

## Success Criteria

**Web UI Validation:**
- ✅ All three tabs load without errors
- ✅ Analysis completes in 60-90 seconds
- ✅ Reports display correctly in preview
- ✅ Interactive graph renders with D3.js
- ✅ Download provides timestamped file
- ✅ Error messages are clear and helpful
- ✅ Responsive design works on different screen sizes

**Demo Video Quality:**
- ✅ Clear audio narration
- ✅ Smooth screen recording (no lag)
- ✅ All features demonstrated
- ✅ 2-3 minute duration
- ✅ Professional presentation
- ✅ Highlights two unique features

**Screenshots Quality:**
- ✅ High resolution (1920x1080+)
- ✅ Clean UI with no personal info
- ✅ Professional appearance
- ✅ All key features visible
- ✅ Consistent lighting/theme

---

## File Locations

**Demo Outputs:**
- Screenshots: `/Users/ifiokmoses/code/find-evil-agent/docs/images/`
- Demo video: `/Users/ifiokmoses/code/find-evil-agent/docs/videos/demo.mp4`
- Test reports: `/Users/ifiokmoses/code/find-evil-agent/reports/demo_*`

**Launch Commands:**
```bash
# Activate environment
source .venv/bin/activate

# Launch web UI
find-evil web

# Launch with custom port
find-evil web --port 17001

# Launch with public share link
find-evil web --share
```
