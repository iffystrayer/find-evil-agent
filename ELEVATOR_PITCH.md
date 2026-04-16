# Find Evil Agent — Elevator Pitch

We're building an AI agent that does forensic investigations autonomously. You tell it "there's ransomware on this endpoint" and it picks the right SIFT tool, runs it, reads the output, finds leads, and follows them — all by itself. Three investigation steps in 45 seconds instead of an hour of manual work.

The key trick: it *can't* hallucinate tool names because we use vector search to constrain the LLM to only real tools, with a confidence threshold that rejects anything it's not sure about.

It's for the FIND EVIL hackathon — $22k prize pool, deadline June 15, and we have a working prototype that needs MCP integration and real evidence handling to be competitive.
