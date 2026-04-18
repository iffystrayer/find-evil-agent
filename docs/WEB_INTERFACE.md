# 🌐 Find Evil Agent - Web Interface

**Interactive browser-based UI for incident response automation**

Built with [Gradio 6.0](https://gradio.app) for accessibility and ease of use.

---

## Quick Start

### Launch the Web UI

```bash
# Default (http://localhost:17000)
find-evil web

# Custom port
find-evil web --port 17001

# Create public share link (for demos)
find-evil web --share

# Debug mode
find-evil web --debug

# Alternative: Direct Python
python launch_web.py
```

**Access:** Open your browser to http://localhost:17000

---

## Three Tabs

### 1. 🎯 Single Analysis

**Purpose:** One-shot incident analysis with immediate results

**How to use:**
1. Enter **Incident Description** (e.g., "Ransomware detected on Windows endpoint")
2. Enter **Analysis Goal** (e.g., "Identify malicious processes and extract IOCs")
3. Choose **Report Format** (HTML or Markdown)
   - HTML includes interactive graph visualization
   - Markdown is plain text
4. Click **🚀 Analyze**
5. Watch real-time progress updates
6. View report preview inline
7. Download full report

**Example Input:**
```
Incident: Suspicious PowerShell execution detected in Event Logs
Goal: Identify command-line arguments and potential malicious activity
```

**Output:**
- Executive Summary (4 sections)
- MITRE ATT&CK Mapping (techniques across 5 tactics)
- IOC Tables (deduplicated IPs, domains, hashes, files, registry, processes)
- Chronological Timeline
- Findings by Severity (CRITICAL → INFO)
- Prioritized Recommendations (immediate → urgent → scheduled)
- Interactive Attack Graph (HTML only)
- Evidence Citations with confidence scores

---

### 2. 🔬 Investigative Mode

**Purpose:** Multi-iteration autonomous investigation that follows leads automatically

**How to use:**
1. Enter **Incident Description** (e.g., "Data exfiltration suspected")
2. Enter **Investigation Goal** (e.g., "Reconstruct complete attack chain")
3. Set **Max Iterations** (2-10, default: 3)
   - More iterations = deeper investigation
   - Recommended: 3-5 for most cases
4. Choose **Report Format** (HTML or Markdown)
5. Click **🔍 Investigate**
6. Watch the agent autonomously:
   - Extract leads from findings
   - Select appropriate tools
   - Follow the evidence trail
   - Build complete attack narrative
7. View comprehensive investigation report
8. Download full report

**Example Input:**
```
Incident: Unknown process consuming high CPU and network activity
Goal: Identify the process, trace its origin, and reconstruct the attack chain
Iterations: 3
```

**What Happens:**
- **Iteration 1:** Initial tool selection → findings → lead extraction
- **Iteration 2:** Follow lead with new tool → more findings → new leads
- **Iteration 3:** Continue investigation → synthesis → complete chain

**Output:** Same as Single Analysis, plus:
- Investigation chain summary
- All leads followed with reasoning
- Cross-iteration timeline
- Complete attack reconstruction

---

### 3. ℹ️ About

**Content:**
- Project overview and mission
- Two unique differentiators (hallucination prevention + autonomous reasoning)
- Architecture (5 specialized agents)
- Professional reporting features
- MITRE ATT&CK coverage (11 techniques)
- Three interfaces strategy
- Performance vs Valhuntir benchmark
- Developer information

**Perfect for:** Understanding the project, demo presentations, judge reviews

---

## Features

### Real-Time Progress Tracking
- Gradio Progress component shows current step
- Status updates during analysis
- Live feedback on tool selection and execution

### Report Preview
- **HTML Reports:** Rendered inline with full styling
- **Markdown Reports:** Formatted as preformatted text
- **Interactive Elements:** Click graph nodes, zoom, pan (HTML only)

### Download Reports
- Automatic file download after analysis
- Named with timestamp for easy organization
- Stored in `reports/` directory

### Responsive Design
- Works on desktop, tablet, mobile
- Touch-friendly controls
- Adaptive layout

### Error Handling
- Clear error messages
- Validation on required fields
- Graceful degradation on failures

---

## Use Cases

### For Entry-Level Users
- No command-line knowledge required
- Point-and-click interface
- Visual feedback and progress

### For Management
- Professional report presentation
- Easy to demonstrate capabilities
- Share public link for remote viewing (`--share`)

### For Demos and Presentations
- Clean, modern interface
- Real-time progress is engaging
- Interactive graph visualization

### For Hackathon Judges
- Accessible without technical setup
- Shows all features in one place
- About tab explains innovations

---

## Architecture

### Frontend (Gradio Blocks)
- `gr.Textbox` for incident/goal inputs
- `gr.Slider` for iteration control
- `gr.Dropdown` for format selection
- `gr.Button` for actions
- `gr.HTML` for report preview
- `gr.File` for downloads
- `gr.Progress` for real-time updates

### Backend Integration
- `OrchestratorAgent` for analysis workflow
- `ReporterAgent` for professional reports
- Async execution with `asyncio`
- Error handling with try/except

### Port Configuration
- Default: 17000 (5-digit as per CLAUDE.md)
- Configurable via `--port` flag
- Range: 10000-99999 (5-digit only)

---

## Comparison: Three Interfaces

| Feature | CLI | Web UI | REST API |
|---------|-----|--------|----------|
| **Target Users** | Power users, automation | Everyone, entry-level | Developers, integrations |
| **Input Method** | Command-line arguments | Forms and buttons | HTTP JSON requests |
| **Output** | Rich terminal UI, files | Browser preview + download | JSON responses |
| **Real-time Updates** | Terminal spinners | Progress bars | Polling/webhooks |
| **Graph Visualization** | File only | Inline preview | File/URL only |
| **Setup Required** | Terminal access | Web browser | HTTP client |
| **Best For** | Scripting, CI/CD | Demos, stakeholders | App integration |

**Strategy:** Offer all three to appeal to wider audience in hackathon

---

## Technical Details

### Dependencies
- `gradio>=5.0.0` (web framework)
- `asyncio` (async execution)
- `pathlib` (file handling)
- `datetime` (timestamping)

### Performance
- **Analysis:** 60-90 seconds (same as CLI)
- **Report Generation:** < 2 seconds (MD/HTML)
- **Page Load:** < 1 second
- **Concurrent Users:** Supports multiple via Gradio queue

### Security
- Runs on localhost by default (0.0.0.0)
- Share link is optional (`--share`)
- No authentication (local use only)
- Input validation on incident/goal fields

### Browser Compatibility
- Chrome/Edge (recommended)
- Firefox
- Safari
- Mobile browsers (responsive)

---

## Troubleshooting

### Port Already in Use
```bash
# Use different port
find-evil web --port 17001
```

### Gradio Not Installed
```bash
# Install dependencies
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Can't Access from Other Machines
```bash
# Bind to all interfaces
find-evil web --host 0.0.0.0

# Or create public share link
find-evil web --share
```

### Analysis Not Starting
- Check SIFT VM is accessible (192.168.12.101:22)
- Check Ollama is running (192.168.12.124:11434)
- Enable debug mode: `find-evil web --debug`

### Report Preview Not Showing
- HTML reports render inline automatically
- Markdown reports show as preformatted text
- Check browser console for JavaScript errors

---

## Development

### Modify the Interface

Edit `src/find_evil_agent/web/gradio_app.py`:
- `create_app()` - UI layout and components
- `analyze_incident()` - Backend logic
- `launch_app()` - Server configuration

### Add New Tabs

```python
with gr.Tab("New Feature"):
    gr.Markdown("Content here...")
    # Add components
```

### Customize Styling

Gradio 6.0 uses `theme` and `css` in `launch()`:
```python
demo.launch(
    theme=gr.themes.Soft(),
    css="custom styles here"
)
```

---

## Production Deployment

### For Public Deployment

**Not Recommended:** This is a hackathon demo tool, not production software.

**If you must:**
1. Add authentication (Gradio Enterprise or reverse proxy)
2. Use HTTPS (nginx/Caddy reverse proxy)
3. Rate limiting (prevent abuse)
4. Input sanitization (prevent injection)
5. Error logging (Sentry, etc.)
6. Session management (track concurrent users)

**Better Approach:** Use REST API with proper authentication

---

## Why Web UI?

### Hackathon Strategy
- **Wider Appeal:** Something for every user type
- **Accessibility:** No terminal knowledge required
- **Demo Impact:** Visual and interactive
- **Judge Engagement:** Easy to try during presentation

### Competitive Advantage
- **Valhuntir:** No web UI, command-line only
- **Find Evil:** Three interfaces (CLI + Web + API)
- **Result:** More accessible, broader user base

### Time Investment
- **Estimated:** 4-6 hours (from memory)
- **Actual:** ~4 hours (implementation + testing + docs)
- **Worth It:** Yes - high impact for time spent

---

## Examples

### Ransomware Analysis
```
Incident: Ransomware detected encrypting files on Windows server
Goal: Identify the ransomware family and initial infection vector
Format: HTML
```

**Expected Output:**
- T1486 (Data Encrypted for Impact)
- Process chain from initial access
- File IOCs (encrypted files, ransom notes)
- Network IOCs (C2 servers)
- Timeline of encryption activity

### Data Breach Investigation
```
Incident: Unauthorized data access detected in database logs
Goal: Reconstruct the complete attack chain from initial access to data exfiltration
Iterations: 5
Format: HTML
```

**Expected Output:**
- Multi-stage attack reconstruction
- Initial compromise vector
- Privilege escalation path
- Lateral movement timeline
- Data exfiltration methods
- Complete MITRE ATT&CK chain

---

## Next Steps

After launching the web UI:
1. Try the example scenarios above
2. Screenshot the interface for documentation
3. Record a demo video showing real-time analysis
4. Add screenshots to README and DevPost submission
5. Test on different browsers and devices
6. Get feedback from non-technical users

---

**Built for the FIND EVIL! Hackathon**  
*Making DFIR automation accessible to everyone*
