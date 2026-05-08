# Demo Video Production Plan

**Date:** May 8, 2026  
**Target:** 5-7 minute comprehensive demo for DevPost submission  
**Deadline:** June 15, 2026 (37 days remaining)

---

## Current Status Assessment

### Existing Videos ⚠️
- **demo_final/demo_recording.webm** - 19.8 seconds (TOO SHORT)
- **Multiple Playwright test recordings** - 2.8s to 19.8s each

**Verdict:** Need to record comprehensive 5-7 minute demo

---

## Option 1: Playwright Automation (RECOMMENDED) ✅

**Advantages:**
- ✅ Automated, repeatable recording
- ✅ Consistent quality (1080p)
- ✅ Tests work as recording sessions
- ✅ Professional screenshot capture
- ✅ No manual coordination errors

**Process:**
```bash
cd demo_artifacts
./quick-start.sh
```

**What it records:**
1. React UI homepage and interface tour
2. Analysis form filling and submission
3. Real-time progress indicators
4. Results display with IOCs
5. MITRE ATT&CK mapping
6. Report generation

**Time:** ~10-15 minutes to run, produces ready-to-use video

**Limitations:**
- No live narration (add voiceover in post)
- Fixed script (predetermined interactions)
- May need multiple takes for best quality

---

## Option 2: Manual Screen Recording

**Advantages:**
- ✅ Full control over narrative
- ✅ Live narration possible
- ✅ Can demonstrate unexpected scenarios
- ✅ More "human" feel

**Tools:**
- **macOS:** QuickTime (Cmd+Shift+5), ScreenFlow, or Camtasia
- **Cross-platform:** OBS Studio

**Process:**
1. Prepare script (DEMO_VIDEO_SCRIPT.md exists)
2. Set up services (docker compose up)
3. Clear browser cache, terminal history
4. Record 1080p @ 30fps
5. Follow script segments (7 sections)
6. Edit in post-production

**Time:** 45-60 minutes recording + 30-60 minutes editing

**Limitations:**
- Manual coordination required
- Higher chance of errors/retakes
- More time-intensive

---

## Option 3: Hybrid Approach (BEST QUALITY)

**Process:**
1. **Use Playwright for B-roll** (interface screenshots, automated interactions)
2. **Manual recording for narrative** (talking head, explanations)
3. **Combine in video editor** (iMovie, DaVinci Resolve, Premiere)

**Benefits:**
- Professional automation + human context
- Best of both worlds
- Flexibility in editing

**Time:** 30 minutes Playwright + 30 minutes manual + 60 minutes editing = 2 hours total

---

## Recommended Approach: Option 1 (Playwright) + Voiceover

### Step 1: Generate Playwright Recording (15 minutes)
```bash
cd demo_artifacts
./quick-start.sh
# Outputs: demo_final/demo_recording.webm
```

### Step 2: Extract Key Segments (using ffmpeg)
```bash
# Segment 1: Homepage (0-20s)
ffmpeg -i demo_recording.webm -ss 0 -t 20 -c copy segment1_homepage.webm

# Segment 2: Form Filling (20-60s)
ffmpeg -i demo_recording.webm -ss 20 -t 40 -c copy segment2_form.webm

# Segment 3: Analysis Running (60-180s)
ffmpeg -i demo_recording.webm -ss 60 -t 120 -c copy segment3_analysis.webm

# Segment 4: Results (180-300s)
ffmpeg -i demo_recording.webm -ss 180 -t 120 -c copy segment4_results.webm

# Segment 5: Report (300-360s)
ffmpeg -i demo_recording.webm -ss 300 -t 60 -c copy segment5_report.webm
```

### Step 3: Record Voiceover (30 minutes)
**Use script from DEMO_VIDEO_SCRIPT.md:**
- Introduction (30s)
- System Overview (30s)
- React UI Demo (2.5min)
- Autonomous Investigation (1.5min)
- Report Generation (1min)
- Conclusion (30s)

**Tools:**
- Audacity (free) or GarageBand (macOS)
- USB microphone or AirPods (decent quality)
- Quiet room, minimal background noise

### Step 4: Combine Video + Audio (iMovie/DaVinci Resolve) (30 minutes)
1. Import video segments
2. Import voiceover audio
3. Sync timing (video speed adjustments if needed)
4. Add transitions between segments
5. Export as MP4 (H.264, 1080p, 30fps)

**Total Time:** ~2 hours for professional quality

---

## Fast-Track Option: Use Existing Playwright + Screen Recording for Narration

### If time-constrained (1 hour total):

1. **Run Playwright automation** (15 min)
   ```bash
   cd demo_artifacts
   ./quick-start.sh
   ```

2. **Record separate narration video** (30 min)
   - Open DEMO_VIDEO_SCRIPT.md
   - Record yourself presenting slides or talking head
   - Follow 6-segment structure

3. **Quick edit** (15 min)
   - Picture-in-picture: Narration (small) + Demo (large)
   - Or split-screen layout
   - Basic transitions

**Result:** Acceptable quality in minimal time

---

## Production Checklist

### Pre-Recording
- [ ] Docker services running (docker compose ps)
- [ ] Services healthy (curl health endpoints)
- [ ] Browser cache cleared
- [ ] Terminal history cleared
- [ ] Test audio levels (if doing voiceover)
- [ ] DEMO_VIDEO_SCRIPT.md reviewed

### Recording
- [ ] Resolution: 1920x1080 minimum
- [ ] Frame rate: 30fps
- [ ] Audio: Clear narration (if included)
- [ ] Lighting: Good (if recording self)
- [ ] Background: Clean/professional (if recording self)

### Post-Production
- [ ] Video segments trimmed
- [ ] Audio synced
- [ ] Transitions added
- [ ] Title slide (optional)
- [ ] End card with GitHub link
- [ ] Exported as MP4 (H.264, 1080p, 30fps)
- [ ] File size < 500MB (DevPost limit)

### Content Verification
- [ ] Both unique features demonstrated
  - [ ] Hallucination-resistant tool selection
  - [ ] Autonomous investigative reasoning
- [ ] All 3 interfaces shown (CLI, React, API) or mentioned
- [ ] Live SIFT VM integration visible
- [ ] Professional report generation shown
- [ ] Clear narration/captions explaining what's happening

---

## Timeline Recommendation

**Today (May 8):** Decision + setup
- Choose approach (Playwright + voiceover recommended)
- Review DEMO_VIDEO_SCRIPT.md
- Test Playwright automation

**Tomorrow (May 9):** Recording
- Run Playwright automation
- Record voiceover following script
- Capture any manual segments needed

**Day 3 (May 10):** Editing + QA
- Combine video + audio in editor
- Add transitions and polish
- Export final MP4
- Watch full video for QA

**Day 4 (May 11):** Upload
- Upload to YouTube (unlisted or public)
- Add to DevPost submission
- Share with team/friends for feedback

**Buffer:** 34 days until deadline (plenty of time for revisions)

---

## Recommended Immediate Action

```bash
# 1. Test Playwright automation
cd demo_artifacts
./quick-start.sh

# 2. Review output
ls -lh demo_final/
file demo_final/demo_recording.webm
ffprobe demo_final/demo_recording.webm

# 3. If video looks good, proceed to voiceover
# 4. If issues, troubleshoot or switch to manual recording
```

---

## Fallback Plan

**If Playwright fails or quality is poor:**

1. **Manual screen recording** using QuickTime/OBS
2. Follow DEMO_VIDEO_SCRIPT.md step-by-step
3. Record in one take (5-7 minutes continuous)
4. Minimal editing (trim start/end)
5. Upload as-is (authentic > perfect)

**Time:** 1 hour total

---

## Success Criteria

✅ **Minimum Viable Demo:**
- 5-7 minutes runtime
- Shows both unique features
- Clear audio/video quality
- Uploaded before June 15

✅ **Ideal Demo:**
- Professional voiceover narration
- Smooth transitions between segments
- Live SIFT VM demonstration visible
- HTML report walkthrough included
- GitHub link in description
- Polished and engaging

---

**Decision Point:** Choose approach now and allocate 1-2 hours for production.

**Recommendation:** Playwright automation + post-recorded voiceover = best quality-to-effort ratio.
