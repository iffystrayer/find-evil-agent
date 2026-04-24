# Animated GIF Guide 🎬

**Purpose:** Create engaging animated GIFs for README and social media

**Tools:** LICEcap (free, lightweight) or Gifski (high quality)

---

## Setup Tools

### Option 1: LICEcap (Recommended - Easy)

```bash
# Install via Homebrew
brew install --cask licecap

# Launch
open /Applications/LICEcap.app
```

**Pros:**
- Simple interface
- Real-time recording
- Small file size
- Free

**Cons:**
- Lower quality than Gifski
- No post-processing

---

### Option 2: Gifski (Recommended - Quality)

```bash
# Install command-line tool
brew install gifski

# Install GUI (optional)
brew install --cask gifski
```

**Pros:**
- Highest quality GIFs
- Better compression
- Can convert from video

**Cons:**
- Two-step process (record video first)
- Slightly more complex

---

## GIF Recording Checklist

### 1. React UI - Homepage to Analysis

**Duration:** 10-15 seconds

**Steps:**
1. Start on homepage (http://localhost:15173)
2. Fill in form:
   - Type: "Ransomware detected"
   - Type: "Identify malicious process"
3. Click "Start Analysis"
4. Show loading animation
5. Display results (first few lines)

**Using LICEcap:**
```
1. Launch LICEcap
2. Position recording frame over browser window
3. Click "Record"
4. Save as: react_ui_workflow.gif
5. Perform steps above
6. Click "Stop"
```

**Using Gifski (from video):**
```bash
# 1. Record screen video (QuickTime: File → New Screen Recording)
# 2. Save as react_demo.mov
# 3. Convert to GIF
gifski --quality 90 --fps 15 react_demo.mov -o react_ui_workflow.gif
```

**Save as:** `react_ui_workflow.gif`  
**Target size:** < 5 MB

---

### 2. CLI Analysis - Complete Flow

**Duration:** 15-20 seconds

**Steps:**
1. Clear terminal: `clear`
2. Show command: `uv run find-evil analyze "incident" "goal"`
3. Press ENTER
4. Show progress indicators
5. Show completion message
6. Show report path

**Terminal Setup:**
- Font: 18pt (large for readability)
- Size: 80x24 (standard)
- Theme: High contrast

**Recording:**
```
1. Position LICEcap over terminal
2. Start recording
3. Execute command
4. Wait for completion
5. Stop recording
```

**Save as:** `cli_analysis_flow.gif`  
**Target size:** < 3 MB

---

### 3. Model Selector - Provider Switch

**Duration:** 8-10 seconds

**Steps:**
1. Show Gradio UI (http://localhost:17001)
2. Click Provider dropdown
3. Hover over options (Ollama, OpenAI, Anthropic)
4. Select OpenAI
5. Show Model dropdown update
6. Hover over GPT models

**Save as:** `model_selector_demo.gif`  
**Target size:** < 2 MB

---

### 4. Glassmorphism UI - Visual Tour

**Duration:** 12-15 seconds

**Steps:**
1. Start at top (sandbox status indicator)
2. Slowly scroll down showing:
   - BentoGrid layout
   - Glassmorphism cards
   - Audit trail section
   - Analysis form
3. Pause briefly on each section
4. Return to top

**Recording Tip:**
- Slow, smooth scrolling
- Pause 1-2 seconds per section
- Show frosted glass effects

**Save as:** `glassmorphism_tour.gif`  
**Target size:** < 4 MB

---

### 5. Real-Time Analysis - Loading States

**Duration:** 8-10 seconds

**Steps:**
1. Form already filled
2. Click "Start Analysis"
3. Show loading spinner
4. Show progress updates
5. Show first result appearing

**Save as:** `realtime_analysis.gif`  
**Target size:** < 3 MB

---

## GIF Optimization

### Reduce File Size

**Method 1: Reduce FPS**
```bash
# Lower frame rate (10-15 fps is usually fine)
gifski --fps 10 input.mov -o output.gif
```

**Method 2: Reduce Dimensions**
```bash
# Scale to 80% size
gifski --quality 90 --width 1200 input.mov -o output.gif
```

**Method 3: Reduce Quality**
```bash
# Lower quality slightly (80-90 still looks good)
gifski --quality 80 input.mov -o output.gif
```

**Method 4: Use gifsicle**
```bash
# Install
brew install gifsicle

# Optimize
gifsicle -O3 --colors 256 input.gif -o output.gif
```

---

## Target File Sizes

| GIF | Max Size | Recommended FPS | Recommended Quality |
|-----|----------|-----------------|---------------------|
| React UI Workflow | 5 MB | 15 | 90 |
| CLI Analysis | 3 MB | 12 | 85 |
| Model Selector | 2 MB | 15 | 90 |
| Glassmorphism Tour | 4 MB | 15 | 90 |
| Real-time Analysis | 3 MB | 15 | 90 |

**GitHub README limit:** 10 MB per file (stay well under)

---

## Advanced: From Video

### Record High-Quality Video First

**QuickTime:**
```
File → New Screen Recording
Options → Show Mouse Clicks
Start Recording → Perform demo → Stop
Save as: demo_video.mov
```

**OBS Studio (for advanced):**
```bash
# Install
brew install --cask obs

# Record at 1080p, 30fps
# Export as MP4
```

### Convert to GIF

**Gifski (highest quality):**
```bash
gifski --quality 95 --fps 15 demo_video.mov -o demo.gif
```

**FFmpeg (more control):**
```bash
# Install
brew install ffmpeg

# Convert with palette for better quality
ffmpeg -i input.mov -vf "fps=15,scale=1200:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" output.gif
```

---

## Quick Recording Script

```bash
#!/bin/bash
# save as: record_gifs.sh

echo "🎬 Animated GIF Recording Guide"
echo "================================"
echo ""

read -p "1. Record React UI workflow (10-15s) - Press ENTER when ready"
echo "   → Start LICEcap, record http://localhost:15173 demo"
echo "   → Save as: react_ui_workflow.gif"
echo ""

read -p "2. Record CLI analysis (15-20s) - Press ENTER when ready"
echo "   → Clear terminal, font 18pt"
echo "   → Record: find-evil analyze command"
echo "   → Save as: cli_analysis_flow.gif"
echo ""

read -p "3. Record model selector (8-10s) - Press ENTER when ready"
echo "   → Open http://localhost:17001"
echo "   → Record: Provider dropdown interaction"
echo "   → Save as: model_selector_demo.gif"
echo ""

read -p "4. Record glassmorphism tour (12-15s) - Press ENTER when ready"
echo "   → Slow scroll of React UI"
echo "   → Save as: glassmorphism_tour.gif"
echo ""

read -p "5. Record real-time analysis (8-10s) - Press ENTER when ready"
echo "   → Click Start Analysis, show loading"
echo "   → Save as: realtime_analysis.gif"
echo ""

echo "✅ All GIFs recorded!"
echo ""
echo "📊 Check file sizes:"
ls -lh demo_artifacts/*.gif 2>/dev/null

echo ""
echo "🔧 Optimize if needed:"
echo "  gifsicle -O3 --colors 256 input.gif -o output.gif"
```

---

## Usage in README

### Example Markdown

```markdown
# Find Evil Agent

![React UI Demo](demo_artifacts/react_ui_workflow.gif)

## Features

### CLI Interface
![CLI Analysis](demo_artifacts/cli_analysis_flow.gif)

### Multi-LLM Support
![Model Selector](demo_artifacts/model_selector_demo.gif)

### Modern Glassmorphism UI
![UI Tour](demo_artifacts/glassmorphism_tour.gif)
```

---

## Best Practices

### Recording

- ✅ Clear, uncluttered screen
- ✅ Large fonts (16-18pt)
- ✅ Slow, deliberate movements
- ✅ Pause briefly to show results
- ✅ Keep under 20 seconds each

### Optimization

- ✅ Use 10-15 FPS (smooth enough, smaller files)
- ✅ Reduce dimensions if needed (1200px width is usually fine)
- ✅ Quality 80-90 (good balance)
- ✅ Optimize with gifsicle after creation

### Accessibility

- ✅ Include text description in README
- ✅ Add alt text: `![Description](path.gif)`
- ✅ Provide screenshot alternative
- ✅ Link to video for longer demos

---

## Troubleshooting

### File Too Large

```bash
# Reduce FPS
gifski --fps 10 input.mov -o output.gif

# Reduce quality
gifski --quality 75 input.mov -o output.gif

# Reduce dimensions
gifski --width 1000 input.mov -o output.gif

# Optimize with gifsicle
gifsicle -O3 --colors 128 input.gif -o output.gif
```

### Choppy Animation

- Increase FPS (15-20)
- Record at higher frame rate
- Smooth mouse movements
- Avoid rapid scrolling

### Poor Quality

- Increase quality setting (90-95)
- Record at higher resolution
- Use Gifski instead of LICEcap
- Avoid excessive compression

---

## Checklist

- [ ] LICEcap or Gifski installed
- [ ] Services running (React, API, Gradio)
- [ ] Terminal font increased (18pt)
- [ ] Browser zoomed (125-150%)
- [ ] All 5 GIFs recorded
- [ ] File sizes optimized (< target)
- [ ] Quality verified (smooth playback)
- [ ] Saved to demo_artifacts/

**Ready for README and social media!** 🎉
