import re

with open("src/find_evil_agent/agents/orchestrator.py", "r") as f:
    text = f.read()

# I will ensure result_state is converted to AgentState if it's a dict before formatting the output.
# The code is around: `result_state = final_state.get("state") if final_state else state_info.values.get("state")`
    
replacement = """            result_state = final_state.get("state") if final_state else state_info.values.get("state")
            if isinstance(result_state, dict):
                result_state = AgentState(**result_state)"""

text = text.replace('            result_state = final_state.get("state") if final_state else state_info.values.get("state")', replacement)

with open("src/find_evil_agent/agents/orchestrator.py", "w") as f:
    f.write(text)

print("Patch applied for process_iterative result_state isinstance")
