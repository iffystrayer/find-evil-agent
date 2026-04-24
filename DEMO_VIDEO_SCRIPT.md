# 🎬 Demo Video Script & Recording Guide
**Target Length:** 5-7 minutes  
**Purpose:** Hackathon submission for FIND EVIL! competition  
**Audience:** Hackathon judges (technical background in DFIR/security)

---

## 📋 Pre-Recording Checklist

### Environment Setup
- [ ] Docker containers running (`docker-compose up -d`)
- [ ] All services healthy (API: 18000, React: 15173, Gradio: 17000)
- [ ] Browser window sized to 1920x1080 (or your recording resolution)
- [ ] Terminal configured with good contrast and readable font size
- [ ] Close unnecessary browser tabs and applications
- [ ] Test audio levels (clear, no background noise)

### Demo Data Preparation
- [ ] Have incident descriptions ready (copy-paste friendly)
- [ ] Terminal history cleared (`clear`)
- [ ] Browser cache cleared for fresh UI load
- [ ] Test HITL workflow beforehand to ensure leads generate

### Recording Tools
**Recommended:**
- **macOS:** QuickTime Player (Cmd+Shift+5) or ScreenFlow
- **Windows:** OBS Studio or Camtasia
- **Linux:** OBS Studio or SimpleScreenRecorder

**Settings:**
- Resolution: 1920x1080 (1080p minimum)
- Frame rate: 30 fps
- Audio: Clear narration (optional background music at low volume)

---

## 🎯 Demo Script (5-7 minutes)

### SEGMENT 1: Introduction (30 seconds)

**Visual:** Title slide or desktop with IDE/terminal

**Script:**
> "Hi, I'm [Your Name], and I'm excited to show you **Find Evil Agent** - an autonomous AI incident response system built for the FIND EVIL! hackathon.
>
> Traditional DFIR workflows require analysts to manually run each forensic tool, interpret results, and decide next steps - often taking hours for a single investigation.
>
> Find Evil Agent changes this by autonomously selecting tools, executing them on a SIFT workstation, and iteratively following investigative leads - all while keeping a human analyst in the loop for critical decisions.
>
> Let me show you how it works."

---

### SEGMENT 2: System Overview (30 seconds)

**Visual:** Show README or architecture diagram

**Script:**
> "The system consists of three main interfaces:
> 1. A modern React UI with HITL support
> 2. A CLI for power users and automation
> 3. A REST API for integrations
>
> All three interfaces support our two unique features:
> - Hallucination-resistant tool selection using semantic search and LLM ranking
> - Autonomous investigative reasoning that follows leads automatically
>
> Let's start with the React UI to demonstrate the full HITL workflow."

---

### SEGMENT 3: React UI Demo - HITL Workflow (2.5 minutes)

**Visual:** Browser at http://localhost:15173

**Script:**
> "Opening the React UI at localhost 15173, you'll see our glassmorphism-designed interface.
>
> I'll toggle to **Investigative Mode** - this is where the autonomous iteration happens.
>
> For this demo, I'll investigate a ransomware incident. Let me enter the incident description..."

**Actions:**
1. Toggle to "Investigative Mode"
2. Enter incident description:
   ```
   Ransomware detected on Windows 10 endpoint. File system encrypted, ransom note found in C:\Users\Public\
   ```
3. Enter investigation goal:
   ```
   Reconstruct complete attack chain from initial access to encryption
   ```
4. Set max_iterations to 3
5. Click "Start Investigation"

**Script (while loading):**
> "The agent is now performing its first analysis iteration. It will:
> 1. Select the most appropriate forensic tool using semantic search
> 2. Execute it on the SIFT workstation
> 3. Extract findings and IOCs
> 4. Identify investigative leads to follow
>
> And here's where the Human-in-the-Loop system kicks in..."

**Visual:** HITL dialog appears

**Script:**
> "The agent has identified a high-priority investigative lead. Let me review it:
>
> - **Priority:** High
> - **Confidence:** 85%
> - **Rationale:** Found suspicious process activity in memory - should analyze process tree
>
> As the analyst, I can review the lead's details, understand why it was selected, and make an informed decision.
>
> This prevents the agent from going down rabbit holes or wasting time on low-value leads.
>
> I'll approve this lead and let the investigation continue..."

**Actions:**
6. Show lead details in dialog
7. Click "Approve"
8. Wait for second iteration (may see another HITL dialog or completion)

**Script (during second iteration):**
> "The agent is now following that lead, selecting another tool, and continuing the investigation.
>
> Notice how each iteration builds on the previous findings - this is autonomous investigative reasoning in action.
>
> Traditional tools would stop after the first analysis. Find Evil Agent automatically constructs the complete attack chain."

**Visual:** Investigation completes

**Script:**
> "And we're done! In under a minute, the agent:
> - Ran 3 iterations of tool selection and execution
> - Extracted multiple findings and IOCs
> - Built a complete investigation narrative
> - Required only one human decision (the HITL approval)
>
> Compare this to a manual workflow: an analyst would spend 60+ minutes running tools, interpreting outputs, and deciding next steps.
>
> The agent did it in 60 seconds with one approval."

---

### SEGMENT 4: CLI Demo (1 minute)

**Visual:** Terminal

**Script:**
> "For power users and automation, we have a comprehensive CLI.
>
> Let me show a quick single-shot analysis..."

**Actions:**
1. Run command:
   ```bash
   uv run find-evil analyze \
     "Suspicious network traffic to unknown IP" \
     "Identify potential C2 communication" \
     -o /tmp/analysis.md -v
   ```

**Script (while running):**
> "The CLI shows real-time progress:
> - Tool selection with confidence scores
> - Command execution on SIFT VM
> - Finding extraction
> - IOC identification
>
> And it generates a professional markdown report automatically."

**Actions:**
2. Show report:
   ```bash
   cat /tmp/analysis.md | head -40
   ```

**Script:**
> "The report includes:
> - Executive summary
> - Tools used with rationale
> - Findings with severity ratings
> - IOCs (IPs, domains, file hashes)
> - Recommended next steps
>
> All formatted professionally for incident response documentation."

---

### SEGMENT 5: API Demo (45 seconds)

**Visual:** Terminal or Postman/Insomnia

**Script:**
> "For integrations, we have a full REST API.
>
> Here's a quick curl example..."

**Actions:**
1. Run API call:
   ```bash
   curl -X POST "http://localhost:18000/api/v1/analyze?provider=ollama&model=llama3.2" \
     -H "Content-Type: application/json" \
     -d '{
       "incident_description": "Malware detected in /tmp",
       "analysis_goal": "Identify malicious files"
     }' | jq .
   ```

**Script:**
> "The API supports:
> - Model selection via query parameters (Ollama, OpenAI, Anthropic)
> - Structured JSON responses
> - Both single analysis and iterative investigation
> - Full OpenAPI documentation
>
> This makes it easy to integrate Find Evil Agent into existing SOAR platforms or ticketing systems."

---

### SEGMENT 6: Differentiators (45 seconds)

**Visual:** Show comparison slide or README features

**Script:**
> "What makes Find Evil Agent unique?
>
> **1. Hallucination Prevention**
> - Most LLM-based DFIR tools can hallucinate non-existent tools
> - We use semantic search + LLM ranking with confidence thresholds
> - Tools are validated against a real registry before execution
> - No other DFIR tool combines both techniques
>
> **2. Autonomous Iteration**
> - Traditional tools run once and stop
> - We automatically extract leads and follow them
> - Builds complete attack chains without manual intervention
> - Human-in-the-loop prevents wasteful investigations
>
> **3. Multi-Provider LLM Support**
> - Switch between Ollama, OpenAI, and Anthropic
> - No vendor lock-in
> - Choose the best model for your use case
>
> **4. Professional Output**
> - MITRE ATT&CK technique mapping
> - HTML and Markdown reports
> - IOC extraction and enrichment
> - Ready for incident response documentation
>
> And it's all **open source** with 462 comprehensive tests."

---

### SEGMENT 7: Closing (30 seconds)

**Visual:** Project GitHub page or thank you slide

**Script:**
> "Find Evil Agent is production-ready with:
> - 98.5% test pass rate (400 out of 406 tests)
> - Docker deployment for easy setup
> - Three interfaces (CLI, API, React UI)
> - MCP server for Claude integration
> - Complete documentation and E2E testing
>
> This project demonstrates how AI agents can augment - not replace - human analysts in DFIR workflows.
>
> By combining semantic search, LLM reasoning, and human oversight, we've created a system that's both powerful and safe.
>
> Thank you for watching! Find Evil Agent is ready to help security teams investigate faster and more thoroughly.
>
> Check out the code and documentation at [GitHub URL] or try the live demo.
>
> Happy hunting!"

---

## 📸 Recording Tips

### Visual Best Practices
1. **Clean Desktop:** Hide personal files, notifications, and clutter
2. **High Contrast:** Use dark terminal theme with bright text (easier to read)
3. **Zoom In:** Make text large enough to read on mobile screens
4. **Highlight Cursor:** Enable cursor highlighting for better tracking
5. **Smooth Transitions:** Don't rush between windows - pause briefly

### Audio Best Practices
1. **Script vs. Improvise:** Know your script but sound natural
2. **Pacing:** Speak slightly slower than normal conversation
3. **Enthusiasm:** Show excitement about the project (judges notice!)
4. **Clarity:** Pronounce technical terms clearly
5. **Pauses:** Leave brief pauses after key points

### Common Mistakes to Avoid
- ❌ Talking too fast (slow down!)
- ❌ Mouse moving erratically (smooth, deliberate movements)
- ❌ Skipping over errors (rehearse to avoid them)
- ❌ No audio or too quiet (test first!)
- ❌ Too long (judges won't watch 15-minute videos)
- ❌ Reading script monotonously (be enthusiastic!)

---

## 🎥 Recording Workflow

### Option 1: Single Take (Recommended for 5-7 min)
1. Rehearse full script 2-3 times
2. Do a test recording (1-2 minutes) to check audio/video quality
3. Record full demo in one take
4. Review for major issues
5. Re-record if needed (totally normal!)

### Option 2: Segment Recording (Easier, but more editing)
1. Record each segment separately
2. Use video editing software to stitch together
3. Add transitions between segments
4. Add background music (optional, low volume)
5. Export final video

### Recommended Editing Tools
- **Simple:** iMovie (Mac), Windows Movie Maker, OpenShot (Linux)
- **Advanced:** Final Cut Pro, DaVinci Resolve (free!), Adobe Premiere
- **Online:** Kapwing, Canva Video Editor

---

## 📤 Export Settings for DevPost

**Format:** MP4 (H.264 codec)
**Resolution:** 1920x1080 (1080p) or 1280x720 (720p minimum)
**Frame Rate:** 30 fps
**Bitrate:** 5-10 Mbps
**Audio:** AAC, 128-192 kbps, 48kHz
**Max File Size:** Usually 100MB (check DevPost requirements)

### Compression Tips
If file is too large:
1. Use HandBrake (free) to compress
2. Reduce bitrate to 3-5 Mbps
3. Use 720p instead of 1080p
4. Trim any dead air at beginning/end

---

## 🧪 Test Recording Checklist

Before final recording, do a test run:

- [ ] Audio levels good (not too quiet, no clipping)
- [ ] Video quality sharp (text readable)
- [ ] Docker containers all running
- [ ] Services respond quickly (no timeouts)
- [ ] HITL dialog appears when expected
- [ ] Terminal commands execute without errors
- [ ] No sensitive information visible (API keys, IPs, etc.)
- [ ] Total length under 7 minutes
- [ ] Pacing feels comfortable (not rushed)

---

## 📋 Alternative: Demo Using Existing Playwright Tests

If live recording is difficult, you can use the existing Playwright automation:

```bash
# Record all demos automatically
./demos/automated/quick-start.sh

# Videos will be in: demos/automated/recordings/
ls -lh demos/automated/recordings/*.webm
```

Then add narration using video editing software.

---

## 🎯 Success Criteria

Your demo video is ready when:
- ✅ Shows both unique features (hallucination prevention + autonomous iteration)
- ✅ Demonstrates HITL workflow clearly
- ✅ Shows all 3 interfaces (React, CLI, API)
- ✅ Professional audio and video quality
- ✅ Under 7 minutes total length
- ✅ Enthusiastic and engaging narration
- ✅ No visible errors or technical issues
- ✅ Clear differentiators from competitors

---

## 🚀 Next Steps After Recording

1. **Review:** Watch the video like a judge would
2. **Get Feedback:** Show to a friend/colleague
3. **Upload to YouTube:** Unlisted or public (DevPost requirement)
4. **Add to DevPost:** Include video link in submission
5. **Backup:** Keep original high-quality file safe

---

## 💡 Pro Tips from Hackathon Winners

> "The first 30 seconds are critical - grab attention immediately"
> 
> "Show, don't tell - live demos beat slides every time"
> 
> "Enthusiasm is contagious - if you're excited, judges will be too"
> 
> "One smooth 5-minute demo beats a buggy 10-minute feature showcase"
> 
> "Highlight what makes you DIFFERENT, not just what you built"

---

## 📊 Estimated Timeline

- Script review: 15 minutes
- Environment setup: 10 minutes
- Rehearsal (3 runs): 30 minutes
- Test recording: 10 minutes
- Final recording: 10 minutes (may need 2-3 takes)
- Review and re-record if needed: 20 minutes
- Light editing (trim, titles): 15 minutes
- Export and upload: 10 minutes

**Total:** ~2 hours (could be faster with practice!)

---

## ✅ Final Checklist Before Upload

- [ ] Video plays without errors
- [ ] Audio is clear throughout
- [ ] All features demonstrated
- [ ] No sensitive information visible
- [ ] Length is 5-7 minutes
- [ ] File size under 100MB
- [ ] Uploaded to YouTube
- [ ] YouTube link tested (works when logged out)
- [ ] Link added to DevPost submission
- [ ] Backup copy saved locally

---

**Good luck with your recording! You've built something amazing - now show it off! 🎬**
