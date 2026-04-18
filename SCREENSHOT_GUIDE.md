# Screenshot Capture Guide

**Status:** Web UI running at http://localhost:17000  
**Browser:** Default macOS browser opened  
**Purpose:** Capture screenshots for documentation and DevPost submission

## Screenshot Sequence

### 1. Main Interface (Empty State)
**File:** `docs/images/web_ui/01_main_interface.png`

**What to capture:**
- Full browser window showing all three tabs
- Single Analysis tab selected (default)
- Empty input fields with placeholder text
- Format dropdown showing options
- Clean, professional Gradio Soft theme
- "Analyze Incident" button visible

**macOS Command:**
```bash
# Cmd+Shift+4, then Space, click browser window
# Or use screencapture command:
screencapture -w docs/images/web_ui/01_main_interface.png
```

---

### 2. Single Analysis - Input Filled
**File:** `docs/images/web_ui/02_input_filled.png`

**What to fill:**
- Incident: "Ransomware detected encrypting files on Windows server. Multiple files have .encrypted extension."
- Goal: "Identify malicious processes, extraction points, and IOCs for containment"
- Format: HTML

**Capture:** Full form with all inputs filled, before clicking "Analyze Incident"

---

### 3. Single Analysis - In Progress
**File:** `docs/images/web_ui/03_in_progress.png`

**What to capture:**
- Active progress bar
- Status message: "Analyzing incident..."
- Loading indicator
- Professional loading UI

**Action:** Click "Analyze Incident" then quickly capture during processing

---

### 4. Single Analysis - Report Preview
**File:** `docs/images/web_ui/04_report_preview.png`

**What to capture:**
- Complete HTML report rendered in preview area
- Executive summary visible
- MITRE ATT&CK mapping section
- IOC tables
- Interactive graph at top
- Download button visible

**Note:** This is the most important screenshot showing complete functionality

---

### 5. Interactive Graph - Overview
**File:** `docs/images/web_ui/05_graph_overview.png`

**What to capture:**
- Full graph visualization with D3.js
- Multiple nodes with different colors (red, orange, yellow, blue, gray)
- Different node shapes (circles, squares, triangles, diamonds)
- Entry points highlighted
- Critical path edges (thick red lines)
- Legend showing color/shape meanings
- Zoom controls

**Zoom level:** Fit to show complete attack chain

---

### 6. Interactive Graph - Node Selected
**File:** `docs/images/web_ui/06_graph_interaction.png`

**What to capture:**
- One node clicked/selected (highlighted)
- Connected nodes/edges highlighted
- Tooltip showing node details (label, type, severity, occurrences)
- Shows interactivity

**Action:** Click a critical node (red circle) and capture tooltip

---

### 7. Interactive Graph - Zoomed In
**File:** `docs/images/web_ui/07_graph_zoomed.png`

**What to capture:**
- Zoomed in view showing node details
- Node labels clearly visible
- Edge labels visible
- Shows zoom capability

**Action:** Zoom in 2-3x and capture

---

### 8. Investigative Mode Tab
**File:** `docs/images/web_ui/08_investigative_mode.png`

**What to capture:**
- Investigative Mode tab selected
- Incident input field
- Investigation goal input
- Iteration slider (set to 3)
- Format dropdown
- "Start Investigation" button

**What to fill:**
- Incident: "Suspicious PowerShell execution detected in Windows event logs. Base64-encoded command observed."
- Goal: "Reconstruct complete attack chain from initial access to impact"
- Iterations: 3
- Format: HTML

---

### 9. Investigative Mode - Multi-Iteration Progress
**File:** `docs/images/web_ui/09_multi_iteration_progress.png`

**What to capture:**
- Progress indicator showing iteration count
- Status messages: "Iteration 1 of 3...", "Following leads...", etc.
- Multiple status updates visible
- Shows autonomous investigation in action

**Action:** Click "Start Investigation" and capture during iteration 2

---

### 10. Investigative Mode - Complete Report
**File:** `docs/images/web_ui/10_investigation_complete.png`

**What to capture:**
- Complete multi-iteration investigation report
- Timeline showing all iterations
- Comprehensive findings section
- Critical path in graph spanning multiple stages
- Download button

---

### 11. About Tab
**File:** `docs/images/web_ui/11_about_tab.png`

**What to capture:**
- About tab selected
- Two unique features section
- Architecture description
- MITRE ATT&CK coverage table
- Three interfaces comparison

**Scroll position:** Top of About tab to show feature highlights

---

### 12. About Tab - MITRE Coverage
**File:** `docs/images/web_ui/12_mitre_coverage.png`

**What to capture:**
- MITRE ATT&CK techniques table
- 11 techniques across 5 tactics
- Professional formatting

**Scroll position:** MITRE section of About tab

---

### 13. Download Dialog
**File:** `docs/images/web_ui/13_download_dialog.png`

**What to capture:**
- Browser download dialog/notification
- Filename with timestamp
- Shows download functionality works

**Action:** Click download button and capture browser's download UI

---

### 14. Downloaded Report in Finder
**File:** `docs/images/web_ui/14_downloaded_file.png`

**What to capture:**
- Finder window showing downloaded file
- Filename with timestamp (e.g., `find_evil_report_20260417_183045.html`)
- File size visible
- Shows successful download

---

### 15. Downloaded Report Opened
**File:** `docs/images/web_ui/15_report_standalone.png`

**What to capture:**
- Downloaded HTML report opened in new browser tab
- Shows report works independently (not just in preview)
- Full professional formatting
- Interactive graph working in standalone file

---

## Optional Screenshots

### 16. Mobile View (if time permits)
**File:** `docs/images/web_ui/16_mobile_view.png`

**What to capture:**
- Browser in responsive/mobile view (Chrome DevTools)
- UI adapts to smaller screen
- Touch-friendly controls
- Shows responsive design

**Action:** Chrome DevTools → Toggle device toolbar → iPhone 14 Pro Max

---

### 17. Error Handling
**File:** `docs/images/web_ui/17_error_handling.png`

**What to capture:**
- Error message displayed clearly
- User-friendly error text
- No stack traces visible to end user

**Action:** Submit empty form or simulate error

---

## Screenshot Standards

**Resolution:** 1920x1080 or higher (Retina 3840x2160 preferred)  
**Format:** PNG (lossless)  
**Browser:** Chrome or Firefox for consistent rendering  
**Zoom:** 100% (default, no browser zoom)  
**Window size:** Full screen or large enough to show complete UI  
**Content:** No personal information visible  
**Quality:** High (not compressed)

## macOS Screenshot Commands

```bash
# Full screen
Cmd + Shift + 3

# Selected area
Cmd + Shift + 4

# Specific window
Cmd + Shift + 4, then Space, click window

# Via terminal (saves to specific path)
screencapture -w docs/images/web_ui/screenshot.png

# Timed screenshot (5 second delay)
screencapture -T 5 -w docs/images/web_ui/screenshot.png
```

## After Capturing

1. **Review all screenshots:**
   - [ ] Clear and professional
   - [ ] No personal info visible
   - [ ] High resolution
   - [ ] All key features shown

2. **Rename systematically:**
   - Use numeric prefixes (01_, 02_, etc.)
   - Descriptive names
   - Consistent format

3. **Optimize if needed:**
   ```bash
   # Optional: compress PNGs while maintaining quality
   pngquant --quality=80-100 docs/images/web_ui/*.png
   ```

4. **Update documentation:**
   - Add screenshots to README.md
   - Add screenshots to WEB_INTERFACE.md
   - Reference in DEMO_SCENARIOS.md

---

## Estimated Time

- Setup and positioning: 5 minutes
- Capture 15 screenshots: 20-25 minutes
- Review and rename: 5 minutes
- Update documentation: 10 minutes

**Total: 40-45 minutes**

---

## Next Steps After Screenshots

1. ✅ Screenshots captured
2. ⏳ Record demo video (60-90 min)
3. ⏳ Update README with screenshots
4. ⏳ DevPost submission preparation
5. ⏳ "Read the Docs" documentation

---

**Ready to capture! Web UI is live at http://localhost:17000**
