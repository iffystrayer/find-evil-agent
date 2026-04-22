import re

with open("src/find_evil_agent/agents/orchestrator.py", "r") as f:
    text = f.read()

# Make memory saver global
text = text.replace(
    "from langgraph.checkpoint.memory import MemorySaver",
    "from langgraph.checkpoint.memory import MemorySaver\n\n_global_memory_saver = MemorySaver()"
)

text = text.replace(
    "        memory = MemorySaver()\n        return workflow.compile(checkpointer=memory, interrupt_before=[\"human_approval_gateway\"])",
    "        return workflow.compile(checkpointer=_global_memory_saver, interrupt_before=[\"human_approval_gateway\"])"
)

with open("src/find_evil_agent/agents/orchestrator.py", "w") as f:
    f.write(text)

print("Global memory saver patched")
