# Find Evil Agent - Demos

This directory contains demonstration scripts showcasing the unique capabilities of Find Evil Agent.

## Hackathon Demo

**File:** `hackathon_demo.py`

Demonstrates the two key features for the FIND EVIL! hackathon:

### Feature #1: Hallucination-Resistant Tool Selection
- Two-stage validation process
- Semantic search → LLM ranking → Confidence threshold → Registry validation
- Prevents LLM from selecting non-existent or inappropriate tools
- Shows confidence scores and selection reasoning

### Feature #2: Autonomous Investigative Reasoning  
- Automatically follows investigative leads
- Multi-iteration workflow without manual intervention
- Builds complete attack chains
- Shows investigation path and lead decisions

## Running the Demo

### Prerequisites
- SIFT VM accessible (configured in `.env`)
- Ollama running with model available
- Python environment activated

### Run
```bash
# Activate environment
source .venv/bin/activate

# Run demo
python demos/hackathon_demo.py
```

### What to Expect

The demo will:
1. Show configuration check
2. **Demo 1**: Run single analysis showing hallucination prevention
   - Displays semantic search results
   - Shows LLM selection with confidence score
   - Validates against tool registry
   - Explains why the tool was selected
   
3. **Demo 2**: Run autonomous investigation showing iterative reasoning
   - Automatically runs 2-3 iterations
   - Shows investigative leads discovered
   - Displays which leads were followed
   - Synthesizes complete investigation chain

### Sample Output

```
╭─────────────────────────────────────────────────────╮
│ Feature #1: Hallucination-Resistant                │
│ Tool Selection                                       │
╰─────────────────────────────────────────────────────╯

Scenario: User asks for file system analysis
Challenge: LLM might hallucinate non-existent tools

✓ Tool Selection Successful

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Stage              ┃ Result                      ┃ Status ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 1. Semantic Search │ Top-10 candidates (fls...)  │ ✓      │
│ 2. LLM Ranking     │ Selected: fls               │ ✓      │
│ 3. Confidence      │ Score: 0.87 (threshold≥0.7) │ ✓ PASS │
│ 4. Registry Valid. │ Tool exists: fls            │ ✓      │
└────────────────────┴─────────────────────────────┴────────┘

---

╭─────────────────────────────────────────────────────╮
│ Feature #2: Autonomous Investigative               │
│ Reasoning                                           │
╰─────────────────────────────────────────────────────╯

Iteration 1:
  Tool: strings
  Duration: 12.3s
  Findings: 2
  → Discovered 1 new lead(s):
     • [high] network: Analyze network connections...

Iteration 2:
  Tool: grep
  Duration: 8.7s
  Findings: 3
  → Followed lead: Analyze network connections
  → No further leads

Total Duration: 21.0s
Complete attack chain reconstructed in 2 iterations
```

## Notes

- Demo uses real SIFT VM connection
- Actual output depends on tool availability on SIFT VM
- Some tools (like volatility) may not be installed - demo handles gracefully
- Investigation depth limited to 3 iterations for demo speed

## Troubleshooting

**SIFT VM connection fails:**
- Check `.env` has correct `SIFT_VM_HOST` and `SIFT_VM_PORT`
- Verify SSH key is configured: `ssh sansforensics@<host>`

**LLM fails:**
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Verify model is pulled: `ollama list`

**No leads discovered:**
- Expected for some tool outputs (e.g., "tool not installed")
- Demo shows fallback behavior

---

**Last Updated:** April 10, 2026
