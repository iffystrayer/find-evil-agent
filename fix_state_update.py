import re

files_to_patch = [
    "src/find_evil_agent/api/server.py",
    "src/find_evil_agent/cli/main.py",
    "src/find_evil_agent/web/gradio_app.py"
]

for filepath in files_to_patch:
    with open(filepath, "r") as f:
        text = f.read()

    replacement = """            # Get current state to avoid overwriting nested dict
            current_state_info = orchestrator.iterative_workflow.get_state(config)
            current_state_dict = current_state_info.values.get("state", {})
            if hasattr(current_state_dict, "model_dump"):
                current_state_dict = current_state_dict.model_dump()
            elif hasattr(current_state_dict, "__dict__"):
                current_state_dict = vars(current_state_dict)
            current_state_dict["human_approved"] = request.approved if hasattr(request, "approved") else approved
            
            orchestrator.iterative_workflow.update_state(
                config,
                {"state": current_state_dict}
            )"""

    text = re.sub(
        r'orchestrator\.iterative_workflow\.update_state\(\s*config,\s*\{"state": \{"human_approved": [^}]+\}\}\s*\)',
        replacement,
        text
    )

    with open(filepath, "w") as f:
        f.write(text)

print("State updates patched")
