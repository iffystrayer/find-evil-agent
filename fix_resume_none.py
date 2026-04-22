import re

with open("src/find_evil_agent/agents/orchestrator.py", "r") as f:
    text = f.read()

text = text.replace(
"""                session_id=session_id,
                incident_description=result_state.incident_description,
                analysis_goal=result_state.analysis_goal,""",
"""                session_id=session_id,
                incident_description=result_state.incident_description or incident_description,
                analysis_goal=result_state.analysis_goal or analysis_goal,"""
)

with open("src/find_evil_agent/agents/orchestrator.py", "w") as f:
    f.write(text)

print("Patch applied for missing incident_description during resume")
