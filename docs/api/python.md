# Python API Reference

Programmatic usage of Find Evil Agent in Python applications.

## Installation

```bash
pip install -e .
# or with uv
uv pip install -e .
```

## Basic Usage

### Single Analysis

```python
from find_evil_agent.agents.orchestrator import OrchestratorAgent
from find_evil_agent.config import Config

# Initialize
config = Config.from_env()
orchestrator = OrchestratorAgent(config)

# Run analysis
result = orchestrator.analyze(
    incident_description="Suspicious network traffic to 185.220.101.42",
    analysis_goal="Identify malicious processes and C2 communication"
)

# Access results
print(f"Tool selected: {result.tool_selected}")
print(f"Confidence: {result.confidence}")
print(f"IOCs found: {len(result.iocs)}")
print(result.report_markdown)
```

### Multi-Iteration Investigation

```python
# Autonomous investigation
result = orchestrator.investigate(
    incident_description="Ransomware detected on Windows 10 endpoint",
    analysis_goal="Complete attack chain analysis",
    max_iterations=5
)

# Review iterations
for i, iteration in enumerate(result.iterations, 1):
    print(f"Iteration {i}: {iteration.tool} ({iteration.duration:.1f}s)")
    print(f"  Leads found: {iteration.leads_found}")

print(f"\nTotal IOCs: {len(result.all_iocs)}")
print(f"Total duration: {result.total_duration:.1f}s")
```

## Core Classes

### OrchestratorAgent

Main entry point for analysis workflows.

```python
from find_evil_agent.agents.orchestrator import OrchestratorAgent

orchestrator = OrchestratorAgent(
    config=config,
    tool_selector=tool_selector,  # Optional
    tool_executor=tool_executor,  # Optional
    analyzer=analyzer            # Optional
)

# Single analysis
result = orchestrator.analyze(
    incident_description: str,
    analysis_goal: str,
    confidence_threshold: float = 0.7,
    timeout: int = 60
)

# Investigation
result = orchestrator.investigate(
    incident_description: str,
    analysis_goal: str,
    max_iterations: int = 3,
    stop_on_no_leads: bool = False
)
```

### ToolSelectorAgent

Two-stage tool selection with semantic search and LLM ranking.

```python
from find_evil_agent.agents.tool_selector import ToolSelectorAgent
from find_evil_agent.tools.registry import ToolRegistry

registry = ToolRegistry()
selector = ToolSelectorAgent(llm_provider=llm, registry=registry)

# Select best tool
selection = selector.select_tool(
    incident_description="Malware in /tmp directory",
    analysis_goal="List suspicious files",
    confidence_threshold=0.7
)

print(f"Tool: {selection.tool_name}")
print(f"Confidence: {selection.confidence}")
print(f"Reasoning: {selection.reasoning}")
```

### ToolExecutorAgent

SSH-based execution on SIFT VM.

```python
from find_evil_agent.agents.executor import ToolExecutorAgent

executor = ToolExecutorAgent(
    ssh_host="192.168.12.101",
    ssh_user="sansforensics",
    ssh_key_path="~/.ssh/sift_vm"
)

# Execute command
result = executor.execute_tool(
    tool_name="strings",
    command="strings /evidence/malware.exe",
    timeout=60
)

print(f"Exit code: {result.exit_code}")
print(f"Output: {result.output}")
print(f"Duration: {result.duration}s")
```

### AnalyzerAgent

IOC extraction and severity assessment.

```python
from find_evil_agent.agents.analyzer import AnalyzerAgent

analyzer = AnalyzerAgent(llm_provider=llm)

# Analyze tool output
analysis = analyzer.analyze_output(
    tool_output="Connection to 185.220.101.42:443 ESTABLISHED",
    incident_description="Suspicious network traffic",
    analysis_goal="Identify C2 servers"
)

for ioc in analysis.iocs:
    print(f"{ioc.type}: {ioc.value} ({ioc.severity})")

for finding in analysis.findings:
    print(f"- {finding}")
```

### ToolRegistry

SIFT tool catalog with semantic search.

```python
from find_evil_agent.tools.registry import ToolRegistry

registry = ToolRegistry()

# Search tools semantically
tools = registry.search(
    query="analyze network traffic",
    top_k=5
)

for tool, score in tools:
    print(f"{tool.name}: {score:.2f}")

# Get specific tool
tool = registry.get_tool("netstat")
print(tool.description)
print(tool.command_template)
```

## Configuration

### Config Class

```python
from find_evil_agent.config import Config

# From environment variables
config = Config.from_env()

# Manual configuration
config = Config(
    llm_provider="ollama",
    ollama_base_url="http://192.168.12.124:11434",
    sift_vm_host="192.168.12.101",
    min_confidence=0.7
)

# Access settings
print(config.llm_provider)
print(config.sift_vm_host)
```

## LLM Providers

### Factory Pattern

```python
from find_evil_agent.llm.factory import LLMFactory

# Create provider
llm = LLMFactory.create(
    provider="ollama",
    base_url="http://localhost:11434",
    model="llama3:8b",
    timeout=300
)

# Use provider
response = llm.chat([
    {"role": "user", "content": "Analyze this incident..."}
])
print(response.content)
```

### Custom Provider

```python
from find_evil_agent.llm.protocol import LLMProvider

class CustomLLM(LLMProvider):
    def chat(self, messages, **kwargs):
        # Your implementation
        return ChatResponse(content="...", model="custom")
    
    def available_models(self):
        return ["custom-model-v1"]

# Register
factory.register("custom", CustomLLM)
```

## Report Generation

### ReporterAgent

```python
from find_evil_agent.agents.reporter import ReporterAgent

reporter = ReporterAgent()

# Generate markdown report
markdown = reporter.generate_markdown(
    incident="Ransomware detected",
    tool_selected="volatility",
    iocs=iocs,
    findings=findings
)

# Generate HTML report
html = reporter.generate_html(
    incident="Ransomware detected",
    tool_selected="volatility",
    iocs=iocs,
    findings=findings,
    include_graph=True
)

# Generate PDF (requires weasyprint)
pdf_bytes = reporter.generate_pdf(
    incident="Ransomware detected",
    tool_selected="volatility",
    iocs=iocs,
    findings=findings
)
```

## Async Usage

All SSH operations are async:

```python
import asyncio
from find_evil_agent.agents.executor import ToolExecutorAgent

async def main():
    executor = ToolExecutorAgent(...)
    
    # Execute tool
    result = await executor.execute_tool(
        tool_name="strings",
        command="strings /evidence/malware.exe"
    )
    
    print(result.output)

asyncio.run(main())
```

## Error Handling

```python
from find_evil_agent.exceptions import (
    ToolSelectionError,
    ToolExecutionError,
    SSHConnectionError
)

try:
    result = orchestrator.analyze(incident, goal)
except ToolSelectionError as e:
    print(f"Tool selection failed: {e}")
    print(f"Confidence: {e.confidence}")
except SSHConnectionError as e:
    print(f"Cannot connect to SIFT VM: {e}")
except ToolExecutionError as e:
    print(f"Tool execution failed: {e}")
    print(f"Exit code: {e.exit_code}")
```

## Testing

### Mocking for Tests

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_executor():
    executor = Mock(spec=ToolExecutorAgent)
    executor.execute_tool = AsyncMock(return_value=ExecutionResult(
        exit_code=0,
        output="test output",
        duration=0.1
    ))
    return executor

def test_analysis(mock_executor):
    orchestrator = OrchestratorAgent(executor=mock_executor)
    result = orchestrator.analyze("test", "test")
    assert result.success
```

## Advanced Usage

### Custom Tool Registry

```python
from find_evil_agent.tools.registry import ToolRegistry
from find_evil_agent.tools.models import Tool

registry = ToolRegistry()

# Add custom tool
registry.register_tool(
    name="custom_scanner",
    description="Custom malware scanner",
    command_template="custom_scanner {target}",
    category="analysis",
    input_schema={
        "target": {"type": "string", "description": "File to scan"}
    }
)
```

### Pipeline Integration

```python
from find_evil_agent.pipeline import AnalysisPipeline

# Build pipeline
pipeline = AnalysisPipeline()
pipeline.add_stage("select", tool_selector)
pipeline.add_stage("execute", tool_executor)
pipeline.add_stage("analyze", analyzer)
pipeline.add_stage("report", reporter)

# Run pipeline
result = pipeline.run(incident, goal)
```

### Observability

```python
from find_evil_agent.telemetry import init_telemetry

# Initialize telemetry
init_telemetry(
    langfuse_enabled=True,
    prometheus_enabled=True
)

# Telemetry is automatically captured
result = orchestrator.analyze(incident, goal)

# Check Langfuse dashboard for traces
```

## Type Hints

All classes use comprehensive type hints:

```python
from typing import List, Optional
from find_evil_agent.models import (
    AnalysisResult,
    InvestigationResult,
    IOC,
    Finding
)

def process_results(result: AnalysisResult) -> List[IOC]:
    return [ioc for ioc in result.iocs if ioc.severity == "HIGH"]
```

## Best Practices

1. **Use Config class** for centralized configuration
2. **Enable observability** in production
3. **Handle exceptions** appropriately
4. **Use async** for SSH operations
5. **Cache LLM instances** to avoid reinitialization
6. **Set timeouts** for all operations
7. **Validate inputs** before analysis

## Example Applications

### Batch Processing

```python
import asyncio
from pathlib import Path

async def batch_analyze(incidents_file: Path, output_dir: Path):
    orchestrator = OrchestratorAgent(Config.from_env())
    
    with open(incidents_file) as f:
        incidents = f.readlines()
    
    for i, incident in enumerate(incidents):
        result = orchestrator.analyze(
            incident_description=incident.strip(),
            analysis_goal="Comprehensive analysis"
        )
        
        # Save report
        report_path = output_dir / f"report_{i:03d}.md"
        report_path.write_text(result.report_markdown)
        
        print(f"Completed {i+1}/{len(incidents)}")

asyncio.run(batch_analyze(
    incidents_file=Path("incidents.txt"),
    output_dir=Path("reports")
))
```

### Web Service

```python
from fastapi import FastAPI
from find_evil_agent.agents.orchestrator import OrchestratorAgent

app = FastAPI()
orchestrator = OrchestratorAgent(Config.from_env())

@app.post("/analyze")
async def analyze(incident: str, goal: str):
    result = orchestrator.analyze(incident, goal)
    return {
        "tool": result.tool_selected,
        "confidence": result.confidence,
        "iocs": [ioc.dict() for ioc in result.iocs]
    }
```

## API Documentation

All classes have comprehensive docstrings:

```python
from find_evil_agent.agents.orchestrator import OrchestratorAgent

help(OrchestratorAgent)
help(OrchestratorAgent.analyze)
```

## Next Steps

- [REST API](rest.md) - HTTP API reference
- [CLI Reference](cli.md) - Command-line usage
- [Usage Guide](../usage.md) - Common workflows
