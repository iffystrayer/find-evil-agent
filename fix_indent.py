import re

with open("src/find_evil_agent/agents/orchestrator.py", "r") as f:
    text = f.read()

text = text.replace(
"""        def check_leads(state_dict: dict[str, Any]) -> str:
            state = state_dict["state"]
        if isinstance(state, dict):
            state = AgentState(**state)
            if state.stopping_reason:
                return END""",

"""        def check_leads(state_dict: dict[str, Any]) -> str:
            state = state_dict["state"]
            if isinstance(state, dict):
                state = AgentState(**state)
            if state.stopping_reason:
                return END"""
)

with open("src/find_evil_agent/agents/orchestrator.py", "w") as f:
    f.write(text)

print("Indentation fixed")
