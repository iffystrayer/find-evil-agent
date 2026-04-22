import sys

with open("src/find_evil_agent/agents/orchestrator.py", "r") as f:
    lines = f.readlines()

output = []
for line in lines:
    output.append(line)

with open("src/find_evil_agent/agents/orchestrator.py", "w") as f:
    for line in output:
        f.write(line)
        
print("Wrote orchestrator.py")
