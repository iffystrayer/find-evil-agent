# 🚀 Playwright Demo - Quick Start

**Status:** ✅ Ready to run  
**Time to Demo:** 5-7 minutes  
**Services:** ✅ Running

---

## Run Demo NOW

```bash
./quick-start.sh
```

**That's it!** The script will:
1. ✅ Check all dependencies
2. ✅ Verify services are running
3. ✅ Guide you through recording options
4. ✅ Capture 1080p video + screenshots
5. ✅ Generate professional report

---

## What You Get

After running, you'll have:

### 📹 Video Recording
- **Location:** `test-results/*/video.webm`
- **Quality:** 1080p (1920x1080)
- **Duration:** ~5-7 minutes
- **Format:** WebM (convert to MP4/GIF as needed)

### 📸 Screenshots (Auto-captured)
- **Location:** `screenshots/`
- **Count:** 6-12 images
- **Format:** PNG (high quality)
- **Naming:** Sequential (01-12)

**Screenshots include:**
- 01_react_homepage.png - Glassmorphism UI
- 02_react_ui_elements.png - UI features highlighted
- 03_react_form_filled.png - Analysis form completed
- 04_react_loading.png - LLM processing
- 05_react_results.png - Analysis results
- 06_gradio_homepage.png - Gradio interface

### 📊 Test Report
- **Location:** `playwright-report/index.html`
- **View:** `npm run show-report`
- **Includes:** Test results, timings, screenshots

---

## Manual Commands

If you prefer manual control:

```bash
# Install dependencies
npm install
npx playwright install chromium

# Record demo (full walkthrough)
npm run record-demo

# Quick test (no video)
npm test -- --project=fast-testing

# Debug mode
npm run test:debug

# View report
npm run show-report
```

---

## Services Required

The script checks automatically, but if needed:

### ✅ Backend API (Port 18000)
```bash
cd ~/code/find-evil-agent
docker-compose up
```

### ✅ React UI (Port 15173)
```bash
cd ~/code/find-evil-agent/frontend
npm run dev
```

### ⚠️ Gradio UI (Port 17001) - Optional
```bash
cd ~/code/find-evil-agent
uv run find-evil web --port 17001
```

---

## After Recording

### 1. View Results

```bash
# Open screenshots folder
open screenshots/

# View test report
npm run show-report

# Find video
ls -lh test-results/*/video.webm
```

### 2. Convert Video to MP4 (Optional)

```bash
# Using ffmpeg
ffmpeg -i test-results/*/video.webm \
  -c:v libx264 -crf 23 -preset medium \
  demo_video.mp4
```

### 3. Convert to GIF (Optional)

```bash
# High quality (using gifski)
ffmpeg -i test-results/*/video.webm \
  -vf "fps=10,scale=1280:-1" \
  -f image2 frames/%04d.png

gifski -o demo.gif --quality 90 --fps 10 frames/*.png
rm -rf frames

# Or simple (larger file)
ffmpeg -i test-results/*/video.webm \
  -vf "fps=10,scale=800:-1:flags=lanczos" \
  -loop 0 demo.gif
```

### 4. Upload to DevPost

- Screenshots: `screenshots/*.png` (upload 5-12)
- Video: Upload to YouTube, link in DevPost
- GIF: Add to project README

---

## Troubleshooting

### Services Not Running?

```bash
# Check React UI
curl http://localhost:15173

# Check Backend
curl http://localhost:18000/health

# If not running, start them (see Services Required section)
```

### Browser Doesn't Open?

```bash
# Reinstall Playwright browsers
npx playwright install --force chromium
```

### Form Fields Not Found?

Update selectors in `tests/demo.spec.ts` if React UI changed.

---

## Need Help?

- **Full Guide:** [PLAYWRIGHT_AUTOMATION.md](./PLAYWRIGHT_AUTOMATION.md)
- **Manual Approach:** [SCREENSHOT_GUIDE.md](./SCREENSHOT_GUIDE.md)
- **Demo Script:** [DEMO_WALKTHROUGH.md](./DEMO_WALKTHROUGH.md)

---

**Ready? Run it now:**

```bash
./quick-start.sh
```

🎬 **Happy recording!**
