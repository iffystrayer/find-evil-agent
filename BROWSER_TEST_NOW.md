# 🧪 Browser Testing - DO THIS NOW

**Web UI URL:** http://localhost:17000  
**Status:** ✅ Fixed and running  
**Time Needed:** 10-15 minutes for full test

---

## TEST 1: Single Analysis (5 minutes)

### Step 1: Navigate to Single Analysis Tab

1. Browser should already be open to http://localhost:17000
2. You should see three tabs: "🎯 Single Analysis", "🔬 Investigative Mode", "ℹ️ About"
3. "Single Analysis" tab should be active (selected)

---

### Step 2: Fill In Test Scenario

**Copy and paste these values:**

**Incident Description:**
```
Ransomware detected encrypting files on Windows server. Multiple files have .encrypted extension. Server performance degraded significantly.
```

**Analysis Goal:**
```
Identify malicious processes, extract IOCs, and determine encryption method
```

**Report Format:** Select "html" from dropdown

---

### Step 3: Start Analysis

1. Click the "🚀 Analyze" button
2. Watch for progress bar to appear
3. **EXPECTED:** You should see status updates like:
   - "Initializing orchestrator..."
   - "Running single analysis..."
   - "Generating professional report..."
   - "Complete!"

**⏱️ TIME:** 60-90 seconds

---

### Step 4: Verify Results

After completion, check:

✅ **Report Preview:**
- HTML report displays in preview area below
- Report has sections: Executive Summary, MITRE ATT&CK, IOC Tables, Timeline
- Interactive graph visible at top of report (with colored nodes)

✅ **Status Output:**
- Shows Session ID
- Shows findings count
- Shows duration
- Lists report features

✅ **Download File:**
- Download button/link appears
- Shows filename with timestamp (e.g., `find_evil_report_20260417_123456.html`)

---

### Step 5: Test Graph Interaction

In the report preview, find the interactive graph and test:

1. **Zoom:** Scroll mouse wheel over graph
2. **Click Node:** Click any colored circle/shape
   - EXPECTED: Node highlights, connected nodes/edges highlight
3. **Hover Node:** Move mouse over node without clicking
   - EXPECTED: Tooltip appears with node details
4. **Drag Node:** Click and drag a node
   - EXPECTED: Node moves, edges follow
5. **Pan:** Click and drag background
   - EXPECTED: Entire graph moves

---

### 📸 SCREENSHOTS FOR TEST 1

Capture these 4 screenshots using **Cmd+Shift+4** (select area):

1. **Empty form** - Before clicking Analyze
2. **Progress bar active** - During analysis (be quick!)
3. **Complete report** - Full report preview with graph
4. **Graph interaction** - Node selected or tooltip visible

**Save to:** `docs/images/web_ui/`

---

## TEST 2: Investigative Mode (10 minutes)

⚠️ **WARNING:** This will take 3-5 minutes to complete (3 iterations)

### Step 1: Navigate to Investigative Mode Tab

1. Click "🔬 Investigative Mode" tab
2. Form should be similar to Single Analysis but with iteration slider

---

### Step 2: Fill In Test Scenario

**Copy and paste:**

**Incident Description:**
```
Suspicious PowerShell execution detected in Windows event logs. Base64-encoded command observed. User reported unusual system behavior.
```

**Investigation Goal:**
```
Reconstruct complete attack chain from initial access to impact
```

**Max Iterations:** Set slider to **3**

**Report Format:** Select "html"

---

### Step 3: Start Investigation

1. Click "🔍 Investigate" button
2. Watch for multi-iteration progress updates
3. **EXPECTED STATUS MESSAGES:**
   - "Starting investigation (3 iterations)..."
   - "Iteration 1 of 3..."
   - "Following leads..."
   - "Iteration 2 of 3..."
   - "Iteration 3 of 3..."
   - "Complete!"

**⏱️ TIME:** 3-5 minutes (be patient!)

---

### Step 4: Verify Investigation Results

After completion, check:

✅ **Investigation Report:**
- Multiple iterations visible in timeline
- Comprehensive findings from all iterations
- Critical path spans multiple stages
- More findings than single analysis

✅ **Status Output:**
- Shows iteration count (3 iterations)
- Shows total findings from all iterations
- Shows longer duration

---

### 📸 SCREENSHOTS FOR TEST 2

Capture these 3 screenshots:

5. **Investigative mode form** - Filled, before clicking Investigate
6. **Multi-iteration progress** - During iteration 2 or 3 (status updates visible)
7. **Complete investigation** - Full multi-iteration report

**Save to:** `docs/images/web_ui/`

---

## TEST 3: About Tab (2 minutes)

### Step 1: Navigate to About Tab

1. Click "ℹ️ About" tab
2. Scroll through all content

---

### Step 2: Verify Content

Check that all sections are present:

✅ **Two Unique Differentiators:**
- Hallucination-Resistant Tool Selection (4-stage validation)
- Autonomous Investigative Reasoning

✅ **Architecture Table:**
- 5 agents listed (Orchestrator, ToolSelector, ToolExecutor, Analyzer, Reporter)
- All marked as "✅ Operational"

✅ **Professional Reporting Features:**
- List of report components
- Output formats (MD/HTML/PDF)

✅ **MITRE ATT&CK Coverage:**
- Table showing 11 techniques across 5 tactics
- Tactics: Execution, Defense Evasion, Persistence, etc.

✅ **Three Interfaces:**
- REST API, CLI, Web UI listed

✅ **Performance vs Valhuntir:**
- Comparison table
- Shows Find Evil advantages

✅ **Developer Info:**
- Name: Ifiok Moses
- Email: greattkiffy@gmail.com
- GitHub link

---

### 📸 SCREENSHOTS FOR TEST 3

Capture these 2 screenshots:

8. **About tab - top section** - Two unique features and architecture
9. **About tab - MITRE table** - Scroll to show MITRE ATT&CK coverage

**Save to:** `docs/images/web_ui/`

---

## 📋 QUICK CHECKLIST

After completing all tests:

- [ ] Test 1: Single Analysis completed successfully
- [ ] Test 1: Report preview displayed with graph
- [ ] Test 1: Graph is interactive (click/zoom/drag works)
- [ ] Test 1: 4 screenshots captured
- [ ] Test 2: Investigative mode completed (3 iterations)
- [ ] Test 2: Multi-iteration report displayed
- [ ] Test 2: 3 screenshots captured
- [ ] Test 3: About tab content verified
- [ ] Test 3: 2 screenshots captured
- [ ] **Total: 9 screenshots captured**

---

## 🚨 IF SOMETHING FAILS

### Error Messages in Browser

If you see error messages in the web UI:

1. Check browser console (Cmd+Option+J in Chrome)
2. Look for JavaScript errors
3. Check web UI logs:
   ```bash
   tail -50 /tmp/web_ui_fixed.log
   ```

### Analysis Times Out

If analysis takes longer than 3 minutes:

1. Check Ollama is running:
   ```bash
   curl -s http://192.168.12.124:11434/api/tags | head
   ```

2. Check SIFT VM is accessible:
   ```bash
   nc -zv 192.168.12.101 22
   ```

### Graph Doesn't Render

If graph doesn't appear in report:

1. Check report format is "html" (not markdown)
2. Check browser console for JavaScript errors
3. Try opening downloaded report file directly

### Need to Restart Web UI

```bash
# Stop
pkill -f "find-evil web"

# Start
source .venv/bin/activate
find-evil web --port 17000

# Wait 5 seconds, then refresh browser
```

---

## 🎯 AFTER TESTING

Once all tests pass and screenshots are captured:

1. **Review screenshots** - Make sure they're clear and high-quality
2. **Organize screenshots** - Rename with numbers (01_empty_form.png, etc.)
3. **Test CLI** - Run CLI demo commands from TESTING_GUIDE.md
4. **Prepare for video** - Set up screen recording software

---

## 📸 Screenshot Commands

**Select area:**
```bash
Cmd + Shift + 4
(then drag to select area)
```

**Capture window:**
```bash
Cmd + Shift + 4, then Space
(then click window)
```

**Capture full screen:**
```bash
Cmd + Shift + 3
```

Screenshots save to Desktop by default. Move them to:
```bash
mkdir -p docs/images/web_ui
mv ~/Desktop/Screen*.png docs/images/web_ui/
```

---

## ✅ SUCCESS!

If all tests pass:
- ✅ Web UI is fully functional
- ✅ Single analysis works end-to-end
- ✅ Investigative mode works with multiple iterations
- ✅ Reports generate with interactive graphs
- ✅ About tab shows complete information
- ✅ 9 screenshots captured for documentation

**Next:** Record demo video following DEMO_VIDEO_SCRIPT.md

---

**Current Time:** You should start testing NOW while web UI is running!

**Estimated Time:** 15-20 minutes total for all three tests + screenshots
