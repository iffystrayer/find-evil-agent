import re

with open("src/find_evil_agent/agents/orchestrator.py", "r") as f:
    text = f.read()

replacement = """        state = state_dict["state"]
        if isinstance(state, dict):
            state = AgentState(**state)"""

text = text.replace('        state: AgentState = state_dict["state"]', replacement)

with open("src/find_evil_agent/agents/orchestrator.py", "w") as f:
    f.write(text)

print("dict patch applied")
