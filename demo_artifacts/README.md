# Demo Artifacts 🎬

**Purpose:** Complete demo materials for hackathon submission

**Status:** Ready for DevPost submission

---

## 🎯 NEW: Playwright Automation (RECOMMENDED!)

**Fully automated demo recording with E2E testing**

```bash
./quick-start.sh
```

**What it does:**
- ✅ Records full 1080p video walkthrough
- ✅ Auto-captures screenshots at key moments
- ✅ Tests all interfaces (React + Gradio + MCP)
- ✅ Generates professional HTML report
- ✅ Repeatable and consistent

**Time:** 5-7 minutes automated vs 30-60 minutes manual

**See:** [PLAYWRIGHT_AUTOMATION.md](./PLAYWRIGHT_AUTOMATION.md) for details

---

## 📁 Contents

### Documentation

1. **DEMO_WALKTHROUGH.md** - Comprehensive written walkthrough
   - Project overview
   - Interface demonstrations (CLI, React, Gradio, MCP)
   - Technical architecture
   - Performance metrics
   - Competitive analysis
   - **19,000+ words** of detailed documentation

2. **SCREENSHOT_GUIDE.md** - Step-by-step screenshot capture
   - 12 screenshots needed
   - Exact commands to run
   - Terminal/browser setup
   - Quick capture script
   - Annotation tips

3. **ANIMATED_GIF_GUIDE.md** - Animated GIF creation
   - Tool recommendations (LICEcap, Gifski)
   - 5 GIFs to create
   - Recording best practices
   - Optimization techniques
   - File size targets

4. **README.md** (this file) - Quick reference guide

### Captured Data

- `api_config.json` - Backend API configuration response
- `cli_output.txt` - Sample CLI execution output
- `mcp_server_info.json` - MCP server capabilities

---

## 🚀 Quick Start

### Option 1: Screenshots Only (Recommended)

**Time: 30 minutes**

1. Start all services:
   ```bash
   # Terminal 1: Backend
   uvicorn find_evil_agent.api.server:app --port 18000
   
   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

2. Follow screenshot guide:
   ```bash
   open SCREENSHOT_GUIDE.md
   ```

3. Capture 12 screenshots using macOS Screenshot Tool (Cmd+Shift+5)

4. Upload best 4-6 to DevPost

---

### Option 2: Full Demo Package (Screenshots + GIFs)

**Time: 60-90 minutes**

1. Install tools:
   ```bash
   brew install --cask licecap
   brew install gifski gifsicle
   ```

2. Start services (same as above)

3. Capture screenshots first (30 min)

4. Record animated GIFs (30-45 min):
   ```bash
   open ANIMATED_GIF_GUIDE.md
   ```

5. Optimize GIFs:
   ```bash
   gifsicle -O3 --colors 256 input.gif -o output.gif
   ```

---

### Option 3: Written Walkthrough Only

**Time: 5 minutes**

1. Use existing walkthrough:
   ```bash
   open DEMO_WALKTHROUGH.md
   ```

2. Copy relevant sections to DevPost submission

3. Reference the comprehensive documentation

---

## 📸 Screenshot Checklist

Priority screenshots for DevPost:

- [ ] **01** - React UI Homepage (glassmorphism design) ⭐ MUST HAVE
- [ ] **04** - React UI Results (IOCs + timeline) ⭐ MUST HAVE
- [ ] **05** - CLI Help Output
- [ ] **07** - HTML Report Output ⭐ MUST HAVE
- [ ] **08** - Gradio Model Selector ⭐ MUST HAVE
- [ ] **10** - MCP Tools List ⭐ MUST HAVE
- [ ] **12** - Test Results Summary

**Minimum:** 5 marked with ⭐ (best 5 for gallery)  
**Recommended:** All 12 (comprehensive documentation)

---

## 🎬 Animated GIF Checklist

Optional but highly engaging:

- [ ] React UI Workflow (form fill → analysis → results)
- [ ] CLI Analysis Flow (command → execution → report)
- [ ] Model Selector Demo (provider switching)
- [ ] Glassmorphism Tour (UI visual showcase)
- [ ] Real-time Analysis (loading states)

**Target:** 2-3 GIFs minimum for README  
**File size:** < 5 MB each

---

## 📊 What's Included

### Comprehensive Documentation ✅

**DEMO_WALKTHROUGH.md** provides:
- Complete project overview
- All 3 interfaces demonstrated
- Technical deep-dive
- Performance benchmarks
- Competitive analysis
- Quick start guide for judges
- 19,000+ words

### Screenshot Guide ✅

**SCREENSHOT_GUIDE.md** provides:
- Step-by-step instructions for 12 screenshots
- Exact terminal commands
- Browser setup (zoom, URLs)
- Naming conventions
- Quality tips
- Quick capture script

### GIF Guide ✅

**ANIMATED_GIF_GUIDE.md** provides:
- Tool recommendations
- 5 GIF scenarios
- Recording techniques
- Optimization methods
- File size targets
- Best practices

### Sample Data ✅

Already captured:
- API configuration response
- CLI execution output
- MCP server capabilities

---

## 🎯 DevPost Submission Workflow

### 1. Prepare Materials (30-90 min)

**Minimum (30 min):**
- ✅ Use DEMO_WALKTHROUGH.md as submission text
- ✅ Capture 5 priority screenshots
- ✅ Upload screenshots to DevPost gallery

**Recommended (60 min):**
- ✅ Capture all 12 screenshots
- ✅ Create 2-3 animated GIFs
- ✅ Annotate screenshots (arrows, labels)

**Comprehensive (90 min):**
- ✅ All screenshots + GIFs
- ✅ Record 5-7 minute demo video
- ✅ Upload to YouTube
- ✅ Link in DevPost submission

### 2. DevPost Submission Fields

**Project Name:**
```
Find Evil Agent - Autonomous AI Incident Response
```

**Tagline:**
```
Hallucination-resistant AI agent for SANS SIFT forensic investigations - 20-100x faster than manual analysis
```

**Description:**
```
Copy sections from DEMO_WALKTHROUGH.md:
- Overview
- Key Features
- Competitive Advantages
- Technical Highlights
```

**Demo Video URL:**
```
[YouTube link if recorded]
OR
Link to animated GIF showcase
```

**Gallery Images:**
```
Upload 5-12 screenshots in order:
1. React UI Homepage
2. React UI Results
3. HTML Report
4. Gradio Model Selector
5. MCP Tools List
[+ 7 more if available]
```

**Built With:**
```
- Python 3.12
- React 18
- FastAPI
- LangChain
- Ollama / OpenAI / Anthropic
- TailwindCSS
- Framer Motion
- Gradio
- Model Context Protocol (MCP)
```

**Try It Out:**
```
https://github.com/[username]/find-evil-agent
```

### 3. README Enhancement

Update project README with demo artifacts:

```markdown
# Find Evil Agent

![React UI Demo](demo_artifacts/react_ui_workflow.gif)

## Features

### 🎯 Autonomous Investigation
![CLI Demo](demo_artifacts/cli_analysis_flow.gif)

### 🎨 Modern Glassmorphism UI
![UI Tour](demo_artifacts/glassmorphism_tour.gif)

### 🔧 Multi-LLM Support
![Model Selector](demo_artifacts/model_selector_demo.gif)

## Screenshots

[Link to screenshot gallery]

## Full Demo

[Watch 5-minute demo video](youtube-link)
```

---

## 📈 Quality Checklist

### Screenshots

- [ ] All text is readable (16-18pt font)
- [ ] Browser zoom at 125-150%
- [ ] High contrast terminal theme
- [ ] No personal information visible
- [ ] Clean, uncluttered screens
- [ ] Consistent naming (01-12)
- [ ] PNG format (lossless)
- [ ] Minimum 1080p resolution

### Animated GIFs

- [ ] Smooth playback (15 fps minimum)
- [ ] File size < 5 MB each
- [ ] Quality 80-90%
- [ ] Slow, deliberate movements
- [ ] Duration 8-20 seconds
- [ ] No choppy frames
- [ ] Optimized with gifsicle

### Written Content

- [ ] No typos or grammatical errors
- [ ] Technical accuracy verified
- [ ] Clear, concise explanations
- [ ] Code examples tested
- [ ] Links functional
- [ ] Formatting consistent

---

## 🔧 Services Setup Reference

**Start all services:**

```bash
# Terminal 1: Backend API
cd ~/code/find-evil-agent
uvicorn find_evil_agent.api.server:app --host 0.0.0.0 --port 18000

# Terminal 2: React UI
cd ~/code/find-evil-agent/frontend
npm run dev

# Terminal 3: Gradio (optional)
cd ~/code/find-evil-agent
uv run find-evil web --port 17001
```

**Verify services:**

```bash
# Backend
curl http://localhost:18000/health

# React UI
curl http://localhost:15173

# Gradio
curl http://localhost:17001
```

**Stop services:**

```bash
# Find and kill processes
lsof -ti:18000 | xargs kill
lsof -ti:15173 | xargs kill
lsof -ti:17001 | xargs kill
```

---

## 📝 Notes

### File Organization

```
demo_artifacts/
├── README.md (this file)
├── DEMO_WALKTHROUGH.md (19,000+ words)
├── SCREENSHOT_GUIDE.md (detailed instructions)
├── ANIMATED_GIF_GUIDE.md (GIF creation)
├── api_config.json (sample data)
├── cli_output.txt (sample data)
├── mcp_server_info.json (sample data)
├── screenshots/ (create this)
│   ├── 01_react_ui_homepage.png
│   ├── 02_react_ui_form_filled.png
│   ├── ... (10 more)
└── gifs/ (create this)
    ├── react_ui_workflow.gif
    ├── cli_analysis_flow.gif
    └── ... (3 more)
```

### Git Tracking

```bash
# Don't commit large GIFs to git
echo "*.gif" >> .gitignore
echo "demo_artifacts/screenshots/*.png" >> .gitignore

# Only commit documentation
git add demo_artifacts/*.md
git add demo_artifacts/*.json
git add demo_artifacts/*.txt
git commit -m "docs: Add comprehensive demo artifacts"
```

---

## 🎉 Summary

**You have 3 options:**

1. **Quick (30 min):** Use walkthrough + 5 screenshots → DevPost
2. **Standard (60 min):** All screenshots + 2-3 GIFs → DevPost + README
3. **Complete (90 min):** Everything + demo video → Full submission

**All materials are ready.** Choose your path and execute!

---

## 📧 Next Steps

1. Choose your demo artifact option (Quick/Standard/Complete)
2. Follow the relevant guide (SCREENSHOT_GUIDE.md or ANIMATED_GIF_GUIDE.md)
3. Capture materials
4. Submit to DevPost
5. Update README with visuals

**Everything you need is in this directory.** 🚀

---

*Created: April 23, 2026*  
*Status: READY FOR SUBMISSION*  
*Test Coverage: 243/243 (100%)*  
*All 6 gaps: COMPLETE*
