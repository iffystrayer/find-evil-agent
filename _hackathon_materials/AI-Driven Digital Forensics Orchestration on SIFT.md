
AI-Driven Digital Forensics Orchestration on SIFT



## AI-Driven Digital Forensics Orchestration on SIFT

As an AI, I cannot generate a video file (like an MP4) directly. However, I can provide a comprehensive **video script and storyboard** that you can use to record this demo yourself.

This script is designed for a 3-minute screen-capture tutorial suitable for sharing with your legal team or DFIR colleagues. It demonstrates the "Advanced Workflow" described in the sources, where Claude orchestrates Eric Zimmerman’s tools natively on SIFT.

**Video Title:** Automated Timeline Forensics with Claude Code & EZ Tools

**Target Audience:** Legal/DFIR Stakeholders **Environment:** SANS SIFT Workstation (Ubuntu 22.04)

\--------------------------------------------------------------------------------

**Phase 1: Setup & Context (0:00–0:45)**

| **Visual (Screen Capture)**                                  | **Audio / Narration Script**                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| **Scene:** Clean SIFT Terminal. <br>Type: `cat /etc/os-release` (shows Ubuntu 22.04). <br>Type: `dotnet --list-runtimes` (shows .NET 9). | "We are working in the SANS SIFT Workstation. Traditionally, creating timelines involves running complex manual commands. Today, we are using **Claude Code** to orchestrate Eric Zimmerman’s tools natively on Linux." |
| **Scene:** Show directory listing of evidence. <br>`ls -lh /cases/incident_01/` <br>Shows `$MFT`, `SYSTEM`, `SOFTWARE`, `Amcache.hve`. | "We have raw artifacts from a compromised host: the Master File Table, Registry hives, and Amcache. We need to answer: *When did the malware arrive, did it execute, and did it persist?*" |
| **Scene:** Launch Claude. <br>Type: `claude` <br>Show Claude initializing in the terminal. | "We launch Claude Code directly in the terminal. It acts as our forensic operator, capable of running tools and reading their output." |

\--------------------------------------------------------------------------------

**Phase 2: Parsing the Artifacts (0:45–1:30)**

| **Visual (Screen Capture)**                                  | **Audio / Narration Script**                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| **Scene:** User types into Claude: <br>*"Use MFTECmd to parse the $MFT file into a CSV. Then use RECmd to parse the SOFTWARE hive for Run keys."* | "Instead of remembering the syntax for `MFTECmd` or `RECmd`, we simply ask Claude to parse the files. Note that we are using the native .NET versions of these tools, which benchmarks show are about **22% faster** than running them via WINE." |
| **Scene:** Claude outputs the commands: <br>`dotnet MFTECmd.dll -f $MFT --csv ...` <br>`dotnet RECmd.dll -f SOFTWARE --csv ...` <br>**Action:** Claude asks *"Run these commands?"* User types `y`. | "Claude generates the correct syntax automatically, handling the output flags. It prompts us for permission before execution—a critical safety control to ensure we stay in the loop." |
| **Scene:** Fast forward slightly as the tools run. <br>Terminal shows: `Processed 124,000 file records...` | "The tools execute natively on SIFT, generating structured CSV data that Claude can now read and analyze." |

\--------------------------------------------------------------------------------

**Phase 3: The "Magic" – AI Correlation (1:30–2:30)**

| **Visual (Screen Capture)**                                  | **Audio / Narration Script**                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| **Scene:** User types prompt: <br>*"Analyze the MFT and Registry CSVs. Build a timeline for the suspicious file 'payload.dll'. Determine when it was created and if it has persistence."* | "This is the game-changer. We don't need to manually grep thousands of rows. We ask Claude to correlate the data across the different tool outputs." |
| **Scene:** Claude "thinking" (spinner). <br>Claude begins typing response. | "Claude scans the MFT for file creation timestamps and cross-references them with the Registry Run keys we just dumped." |
| **Scene:** Claude outputs a Markdown summary: <br>**Jan 10, 01:23:45** – `payload.dll` created in `C:\Temp` (Source: $MFT) <br>**Jan 10, 01:24:15** – Registry Run key added for `payload.dll` (Source: RECmd) | "Look at this result. Claude reconstructed the attack chain: it identified the file creation in the Temp folder and confirmed persistence was established exactly 30 seconds later. It connects the dots instantly." |

\--------------------------------------------------------------------------------

**Phase 4: Deep Dive & Verification (2:30–3:00)**

| **Visual (Screen Capture)**                                  | **Audio / Narration Script**                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| **Scene:** User types: <br>*"Did this file actually execute?"* | "We need to prove execution. We ask Claude to check the Evidence of Execution." |
| **Scene:** Claude responds: <br>*"I will parse the Amcache.hve to check for execution."* <br>Runs: `AmcacheParser.exe ...` | "Claude proactively decides to run `AmcacheParser`. It checks the output and confirms: **Yes, payload.dll was executed at 01:24:10**." |
| **Scene:** Final Summary on screen. <br>Show `CLAUDE.md` being updated with these findings. | "In under three minutes, we went from raw artifacts to a verified timeline of Drop, Execution, and Persistence, all using natural language on SIFT." |

\--------------------------------------------------------------------------------

**How to Record This Demo**

If you want to produce this video for your lawyers, follow these steps:

**Prepare the Environment:**Ensure `.NET 9` is installed on your SIFT VM.Download the EZ Tools (MFTECmd, RECmd, AmcacheParser) to `/opt/ez_tools`.Alias them in your shell so `mftecmd` works directly.**Stage the Data:**Place a sample `$MFT` and `SOFTWARE` hive in a folder. You can generate "fake" evidence by creating a file named `payload.dll` in a VM, adding a Run key, and acquiring the artifacts.**Recording Software:**Use **OBS Studio** (Open Broadcaster Software) which is free and runs well on Ubuntu/SIFT. Set it to record your terminal window.**Execute the Script:**Run through the commands in the script above. Don't worry about typing speed; you can speed up the video in post-production.**Crucial Tip:** When Claude asks for permission to run a command, pause for a second before typing "y" to emphasize the "Human-in-the-loop" safety aspect, which is important for legal justification.