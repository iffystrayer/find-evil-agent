# Screenshot Capture Guide 📸

**Purpose:** Capture professional screenshots for hackathon submission

**Location:** Save all screenshots to `demo_artifacts/screenshots/`

---

## Setup

```bash
# Create screenshots directory
mkdir -p demo_artifacts/screenshots

# Start services
cd frontend && npm run dev &
cd .. && uvicorn find_evil_agent.api.server:app --port 18000 &
```

---

## Screenshot Checklist

### 1. React UI - Homepage (PRIORITY)

**Preparation:**
```bash
# Open in browser
open http://localhost:15173

# Zoom to 150% (Cmd+Plus 3 times)
```

**Capture:**
- Full browser window including URL bar
- Shows: Glassmorphism effects, sandbox status, BentoGrid layout

**Save as:** `01_react_ui_homepage.png`

**macOS Command:**
```bash
# Cmd+Shift+4, then Spacebar, click browser window
# OR use built-in screenshot tool (Cmd+Shift+5)
```

---

### 2. React UI - Analysis Form Filled

**Preparation:**
1. Fill in form:
   - Incident: "Ransomware detected encrypting files on Windows 10 endpoint"
   - Goal: "Identify malicious process and extract IOCs"
2. DON'T submit yet

**Capture:** Form with data, before clicking "Start Analysis"

**Save as:** `02_react_ui_form_filled.png`

---

### 3. React UI - Loading State

**Preparation:**
1. Click "Start Analysis"
2. QUICKLY capture during loading animation

**Capture:** Loading spinner/progress indicator

**Save as:** `03_react_ui_loading.png`

---

### 4. React UI - Results Display

**Wait for:** Analysis to complete

**Capture:** Full results with:
- IOCs extracted
- Timeline data
- MITRE ATT&CK mapping

**Save as:** `04_react_ui_results.png`

---

### 5. CLI - Help Command

**Terminal Setup:**
- Font size: 18pt (View → Bigger or Cmd+Plus)
- Theme: High contrast (for readability)
- Clear history: `clear`

**Run:**
```bash
uv run find-evil --help
```

**Capture:** Terminal window showing help output

**Save as:** `05_cli_help.png`

---

### 6. CLI - Analysis Command

**Run:**
```bash
uv run find-evil analyze \
  "Suspicious PowerShell process detected" \
  "Identify persistence mechanisms"
```

**Capture:** Mid-execution showing progress

**Save as:** `06_cli_analysis.png`

---

### 7. HTML Report (CLI Output)

**Open generated report:**
```bash
open /tmp/demo_report.html
```

**Zoom:** 125% in browser

**Capture:** Professional HTML report showing:
- Executive summary
- IOC table
- MITRE ATT&CK matrix
- Timeline

**Save as:** `07_html_report.png`

---

### 8. Gradio UI - Model Selector

**Start Gradio:**
```bash
uv run find-evil web --port 17001
```

**Open:** http://localhost:17001

**Preparation:**
1. Click provider dropdown
2. Show available options (Ollama, OpenAI, Anthropic)

**Capture:** Dropdowns visible

**Save as:** `08_gradio_model_selector.png`

---

### 9. Gradio UI - Analysis Interface

**Fill in:**
- Incident: "Malware sample detected in downloads folder"
- Goal: "Analyze behavior and extract IOCs"

**Capture:** Complete interface with form

**Save as:** `09_gradio_interface.png`

---

### 10. MCP Server Output

**Terminal:**
```bash
uv run python -c "
from find_evil_agent.mcp.server import list_tools
import json
tools = list_tools()
print(json.dumps(tools[:4], indent=2))  # Show first 4 tools
"
```

**Capture:** Terminal showing JSON output of tools

**Save as:** `10_mcp_tools_output.png`

---

### 11. API Response (Backend)

**Terminal:**
```bash
curl -s http://localhost:18000/api/v1/config | jq .
```

**Capture:** JSON configuration response

**Save as:** `11_api_config_response.png`

---

### 12. Test Results Summary

**Terminal:**
```bash
# Show recent test run summary
uv run pytest tests/ --tb=no -v | tail -50
```

**Capture:** Test summary showing 243/243 passing

**Save as:** `12_test_results.png`

---

## Quick Screenshot Script

**Automated capture (macOS):**

```bash
#!/bin/bash
# save as: capture_screenshots.sh

echo "📸 Screenshot Capture Assistant"
echo "================================"
echo ""
echo "This script will guide you through capturing screenshots."
echo "Press ENTER after each step to continue..."

read -p "1. Open http://localhost:15173 in browser, zoom 150%, press ENTER" 
echo "   → Take screenshot: Cmd+Shift+5 → Save as 01_react_ui_homepage.png"

read -p "2. Fill analysis form, DON'T submit, press ENTER"
echo "   → Take screenshot: Cmd+Shift+5 → Save as 02_react_ui_form_filled.png"

read -p "3. Click 'Start Analysis', QUICKLY capture loading, press ENTER"
echo "   → Take screenshot: Cmd+Shift+5 → Save as 03_react_ui_loading.png"

read -p "4. Wait for results to load, press ENTER"
echo "   → Take screenshot: Cmd+Shift+5 → Save as 04_react_ui_results.png"

read -p "5. Open terminal, run 'uv run find-evil --help', press ENTER"
echo "   → Take screenshot: Cmd+Shift+5 → Save as 05_cli_help.png"

read -p "6. Run CLI analysis command, press ENTER"
echo "   → Take screenshot: Cmd+Shift+5 → Save as 06_cli_analysis.png"

read -p "7. Open /tmp/demo_report.html in browser, press ENTER"
echo "   → Take screenshot: Cmd+Shift+5 → Save as 07_html_report.png"

read -p "8. Open http://localhost:17001, show dropdowns, press ENTER"
echo "   → Take screenshot: Cmd+Shift+5 → Save as 08_gradio_model_selector.png"

read -p "9. Fill Gradio form, press ENTER"
echo "   → Take screenshot: Cmd+Shift+5 → Save as 09_gradio_interface.png"

read -p "10. Run MCP tools command in terminal, press ENTER"
echo "    → Take screenshot: Cmd+Shift+5 → Save as 10_mcp_tools_output.png"

read -p "11. Run API config curl command, press ENTER"
echo "    → Take screenshot: Cmd+Shift+5 → Save as 11_api_config_response.png"

read -p "12. Run pytest summary command, press ENTER"
echo "    → Take screenshot: Cmd+Shift+5 → Save as 12_test_results.png"

echo ""
echo "✅ All screenshots captured!"
echo "📁 Move files to demo_artifacts/screenshots/"
```

---

## Screenshot Tips

### macOS

**Method 1: Built-in Screenshot Tool (RECOMMENDED)**
```bash
# Press: Cmd+Shift+5
# Select: Capture Selected Window or Capture Selected Portion
# Options: Choose save location
# Click: Capture
```

**Method 2: Quick Window Capture**
```bash
# Press: Cmd+Shift+4
# Press: Spacebar (cursor becomes camera)
# Click: Window to capture
```

**Method 3: Command Line**
```bash
# Capture window by clicking
screencapture -W screenshot.png

# Capture after 5 second delay
screencapture -T 5 screenshot.png
```

### Image Quality

- **Format:** PNG (lossless)
- **Resolution:** At least 1920x1080
- **Browser zoom:** 125-150% for text readability
- **Terminal font:** 16-18pt minimum

### Editing

**Annotations (optional):**
- Use Preview.app → Tools → Annotate
- Add arrows pointing to key features
- Add text labels for clarity
- Red boxes for highlighting

**Cropping:**
- Remove unnecessary browser chrome
- Keep URL bar visible for React/Gradio screenshots
- Crop terminal screenshots to relevant content

---

## After Capturing

### Organization

```bash
# Move to organized directory
mv ~/Desktop/0*.png demo_artifacts/screenshots/

# Verify all 12 screenshots
ls -l demo_artifacts/screenshots/
```

### Compression (if needed)

```bash
# Install optipng (optional)
brew install optipng

# Compress without quality loss
optipng demo_artifacts/screenshots/*.png
```

### Upload to DevPost

1. Select best 4-6 screenshots showing:
   - React UI homepage (glassmorphism)
   - CLI in action
   - HTML report output
   - Gradio model selector
   - MCP tools list

2. Upload in this order for gallery

---

## Checklist

- [ ] All 12 screenshots captured
- [ ] Files named correctly (01-12)
- [ ] Image quality verified (readable text)
- [ ] Moved to demo_artifacts/screenshots/
- [ ] Selected best 4-6 for DevPost
- [ ] Annotations added (optional)

**Ready for hackathon submission!** 🎉
