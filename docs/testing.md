# Testing

Find Evil Agent follows strict Test-Driven Development (TDD) methodology with 606+ tests covering all components.

## Test Philosophy

!!! quote "TDD Mandate"
    **ALL code is written tests-first, NO exceptions.**  
    Any code without tests is considered invalid and must be deleted.

### Core Principles

1. **Tests Define Requirements** - Tests are the specification
2. **Red-Green-Refactor** - Write failing test → Implement → Refactor
3. **Real Integrations** - No mocks in integration tests
4. **Comprehensive Coverage** - Unit + Integration + E2E

---

## Test Suite Overview

### Statistics (as of May 8, 2026)

```
Total Tests:     606
Passing:         606 (100%)
xfailed:         10 (expected failures)
Skipped:         20 (requires API keys)
Duration:        ~45 seconds (without integration tests)
Coverage:        95%+ (LOC)
```

### Test Distribution

| Category | Tests | Purpose |
|----------|-------|---------|
| **Unit Tests** | 420 | Component isolation testing |
| **Integration Tests** | 160 | Multi-component workflows |
| **E2E Tests** | 26 | Full system workflows |
| **Total** | 606 | Comprehensive coverage |

---

## Test Structure

### Directory Layout

```
tests/
├── unit/                       # Unit tests (isolated components)
│   ├── agents/                 # Agent-specific tests
│   │   ├── test_orchestrator.py
│   │   ├── test_tool_selector.py
│   │   ├── test_executor.py
│   │   ├── test_analyzer.py
│   │   └── test_reporter.py
│   ├── tools/                  # Tool infrastructure tests
│   │   ├── test_registry.py
│   │   └── test_validators.py
│   ├── llm/                    # LLM abstraction tests
│   │   ├── test_factory.py
│   │   ├── test_ollama.py
│   │   └── test_protocol.py
│   └── security/               # Security validation tests
│       └── test_validators.py
├── integration/                # Integration tests
│   ├── test_workflows.py
│   ├── test_api.py
│   ├── test_cli.py
│   └── test_mcp.py
├── e2e/                        # End-to-end tests
│   └── test_full_analysis.py
└── conftest.py                 # Shared fixtures
```

---

## Test Categories

### Unit Tests

**Purpose:** Test individual components in isolation

**Characteristics:**

- Fast (<1s per test)
- No external dependencies
- Focused on single functionality

**Example:**

```python
# tests/unit/agents/test_tool_selector.py
import pytest
from find_evil_agent.agents.tool_selector import ToolSelectorAgent

class TestToolSelectorAgent:
    """Unit tests for ToolSelectorAgent"""
    
    def test_selects_volatility_for_memory_analysis(self):
        """Should select volatility for memory dump analysis"""
        agent = ToolSelectorAgent(llm_provider="ollama")
        
        result = agent.select_tool(
            incident="Memory dump from compromised endpoint",
            goal="Analyze running processes and network connections"
        )
        
        assert result.tool_name == "volatility"
        assert result.confidence >= 0.7
        assert "memory" in result.reasoning.lower()
    
    def test_rejects_low_confidence_selection(self):
        """Should reject selections below 0.7 confidence threshold"""
        agent = ToolSelectorAgent(llm_provider="ollama")
        
        with pytest.raises(ValueError, match="Confidence below threshold"):
            agent.select_tool(
                incident="Vague incident description",
                goal="Do something"
            )
```

**Run Unit Tests:**

```bash
# All unit tests
pytest tests/unit/ -v

# Specific component
pytest tests/unit/agents/test_tool_selector.py -v

# With coverage
pytest tests/unit/ --cov=find_evil_agent --cov-report=html
```

---

### Integration Tests

**Purpose:** Test multi-component interactions with real dependencies

**Characteristics:**

- Slower (1-30s per test)
- Uses real LLM providers (Ollama)
- Tests actual workflows

**Example:**

```python
# tests/integration/test_workflows.py
import pytest
from find_evil_agent.agents.orchestrator import OrchestratorAgent

@pytest.mark.integration
class TestAnalysisWorkflow:
    """Integration tests for full analysis workflow"""
    
    def test_full_analysis_workflow_with_ollama(self):
        """Should complete full analysis workflow using Ollama"""
        orchestrator = OrchestratorAgent(
            llm_provider="ollama",
            llm_model="gemma2:27b"
        )
        
        result = orchestrator.analyze(
            incident="Suspicious PowerShell execution",
            goal="Extract command-line arguments"
        )
        
        # Verify all workflow steps completed
        assert result.tool_selection is not None
        assert result.execution_result is not None
        assert result.analysis_result is not None
        
        # Verify quality
        assert result.tool_selection.confidence >= 0.7
        assert result.execution_result.return_code == 0
        assert len(result.analysis_result.findings) > 0
    
    @pytest.mark.skipif(
        "OPENAI_API_KEY" not in os.environ,
        reason="OpenAI API key not set"
    )
    def test_analysis_with_openai(self):
        """Should work with OpenAI provider"""
        orchestrator = OrchestratorAgent(
            llm_provider="openai",
            llm_model="gpt-4"
        )
        
        result = orchestrator.analyze(
            incident="Ransomware detected",
            goal="Identify encryption mechanism"
        )
        
        assert result.analysis_result.severity in ["CRITICAL", "HIGH"]
```

**Run Integration Tests:**

```bash
# All integration tests (requires Ollama)
pytest tests/integration/ -v -m integration

# Skip integration tests
pytest tests/ -v -m "not integration"

# Run only OpenAI tests (requires API key)
export OPENAI_API_KEY=sk-...
pytest tests/integration/ -v -k "openai"
```

---

### E2E Tests

**Purpose:** Test complete user journeys from CLI/API to report generation

**Characteristics:**

- Slowest (30-90s per test)
- Uses real SIFT VM via SSH
- Tests actual forensic workflows

**Example:**

```python
# tests/e2e/test_full_analysis.py
import pytest
import subprocess

@pytest.mark.e2e
@pytest.mark.slow
class TestEndToEnd:
    """End-to-end tests with real SIFT VM"""
    
    def test_cli_analysis_end_to_end(self, tmp_path):
        """Should complete full CLI analysis workflow"""
        output_file = tmp_path / "report.md"
        
        # Run CLI command
        result = subprocess.run(
            [
                "find-evil", "analyze",
                "Suspicious file in /tmp directory",
                "List and analyze file metadata",
                "--output", str(output_file),
                "--verbose"
            ],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Verify exit code
        assert result.returncode == 0
        
        # Verify report generated
        assert output_file.exists()
        report_content = output_file.read_text()
        
        # Verify report structure
        assert "## Tool Selection" in report_content
        assert "## Execution Results" in report_content
        assert "## Findings" in report_content
        assert "## Indicators of Compromise" in report_content
    
    def test_api_investigation_end_to_end(self):
        """Should complete full API investigation workflow"""
        import requests
        
        response = requests.post(
            "http://localhost:18000/api/v1/investigate",
            json={
                "incident_description": "Unknown process high CPU",
                "analysis_goal": "Identify process origin",
                "max_iterations": 3
            },
            timeout=180
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "session_id" in data
        assert "iterations" in data
        assert data["iterations"] >= 2  # At least 2 iterations
        assert "findings" in data
        assert "iocs" in data
```

**Run E2E Tests:**

```bash
# All E2E tests (requires SIFT VM + Ollama)
pytest tests/e2e/ -v -m e2e

# With detailed output
pytest tests/e2e/ -v -s -m e2e

# Single E2E test
pytest tests/e2e/test_full_analysis.py::TestEndToEnd::test_cli_analysis_end_to_end -v
```

---

## TDD Test Structure

### Three-Tier Pattern

Every component follows this test structure:

```python
class TestComponentName:
    """Tests for ComponentName"""
    
    # Tier 1: Specification Tests (Always Passing)
    def test_component_requirements_specification(self):
        """Documents what this component does"""
        # Always passes - living documentation
        assert True
    
    # Tier 2: Structure Tests (Skip until implemented)
    @pytest.mark.skipif(not COMPONENT_AVAILABLE, reason="Not implemented")
    def test_component_inherits_from_base_agent(self):
        """Verifies component implements required interface"""
        from find_evil_agent.agents.component import ComponentAgent
        from find_evil_agent.agents.base import BaseAgent
        
        assert issubclass(ComponentAgent, BaseAgent)
    
    # Tier 3: Execution Tests (Skip until implemented)
    @pytest.mark.skipif(not COMPONENT_AVAILABLE, reason="Not implemented")
    def test_successful_execution_with_valid_input(self):
        """Tests core functionality"""
        agent = ComponentAgent()
        result = agent.run("valid input")
        
        assert result is not None
        assert result.success is True
```

### Conditional Imports

```python
# Pattern for TDD - component may not exist yet
try:
    from find_evil_agent.agents.new_component import NewComponent
    COMPONENT_AVAILABLE = True
except ImportError:
    COMPONENT_AVAILABLE = False
    
    # Placeholder for testing structure
    class NewComponent:
        pass

@pytest.fixture
def component_instance():
    """Create component instance for testing"""
    if not COMPONENT_AVAILABLE:
        pytest.skip("NewComponent not implemented yet")
    return NewComponent()
```

---

## Running Tests

### Quick Test Run (Recommended)

```bash
# Fast test run - excludes slow tests
uv run pytest tests/ \
  --ignore=tests/agents/test_command_builder.py \
  -k "not test_orchestrator" \
  -v

# Expected: 606 tests in ~45 seconds
```

### Full Test Suite

```bash
# All tests (including integration and E2E)
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ --cov=find_evil_agent --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Selective Test Execution

```bash
# By marker
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m "not slow"     # Skip slow tests

# By keyword
pytest -k "selector"     # All ToolSelector tests
pytest -k "orchestrator" # All Orchestrator tests

# By file
pytest tests/unit/agents/test_analyzer.py

# By test name
pytest tests/unit/agents/test_analyzer.py::TestAnalyzerAgent::test_extracts_ip_addresses
```

### Parallel Execution

```bash
# Install pytest-xdist
uv pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/ -n 4 -v

# Auto-detect CPU count
pytest tests/ -n auto -v
```

---

## Test Fixtures

### Common Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from uuid import uuid4

@pytest.fixture
def session_id():
    """Generate unique session ID"""
    return str(uuid4())

@pytest.fixture
def test_incident():
    """Standard test incident description"""
    return "Suspicious PowerShell execution on endpoint-042"

@pytest.fixture
def test_goal():
    """Standard test analysis goal"""
    return "Extract command-line arguments and identify malicious scripts"

@pytest.fixture
def ollama_agent():
    """ToolSelectorAgent configured for Ollama"""
    from find_evil_agent.agents.tool_selector import ToolSelectorAgent
    return ToolSelectorAgent(llm_provider="ollama", llm_model="gemma2:27b")

@pytest.fixture(scope="session")
def sift_vm_connection():
    """Shared SIFT VM SSH connection"""
    import asyncssh
    
    conn = asyncssh.connect(
        host=os.environ["SIFT_VM_HOST"],
        username=os.environ["SIFT_SSH_USER"],
        known_hosts=None  # For testing only
    )
    
    yield conn
    conn.close()
```

### Fixture Scopes

| Scope | Lifetime | Use Case |
|-------|----------|----------|
| `function` | Per test (default) | Isolated state |
| `class` | Per test class | Shared setup for class |
| `module` | Per test module | Expensive setup once |
| `session` | Entire test run | DB connections, etc. |

---

## Interpreting Test Results

### Success Output

```
============================= test session starts ==============================
collected 606 items

tests/unit/agents/test_analyzer.py::TestAnalyzerAgent::test_extracts_ip_addresses PASSED [ 0%]
tests/unit/agents/test_analyzer.py::TestAnalyzerAgent::test_extracts_file_paths PASSED [ 1%]
...
tests/e2e/test_full_analysis.py::TestEndToEnd::test_cli_analysis_end_to_end PASSED [100%]

===================== 606 passed, 20 skipped, 10 xfailed in 45.23s ============
```

### Failure Output

```
============================= test session starts ==============================
collected 606 items

tests/unit/agents/test_tool_selector.py::TestToolSelectorAgent::test_selects_volatility FAILED [ 2%]

====================================== FAILURES ========================================
_________________ TestToolSelectorAgent.test_selects_volatility __________________

    def test_selects_volatility_for_memory_analysis(self):
        agent = ToolSelectorAgent(llm_provider="ollama")
        
        result = agent.select_tool(
            incident="Memory dump from compromised endpoint",
            goal="Analyze running processes"
        )
        
>       assert result.tool_name == "volatility"
E       AssertionError: assert 'strings' == 'volatility'
E         - volatility
E         + strings

tests/unit/agents/test_tool_selector.py:45: AssertionError
============================= 1 failed, 605 passed in 48.32s =================
```

### xfail (Expected Failures)

```
tests/unit/reporters/test_pdf_reporter.py::test_pdf_generation XFAIL (requires wkhtmltopdf)
```

**Meaning:** Test is expected to fail (known issue), doesn't count as failure

**Common xfails:**

- PDF generation (requires `wkhtmltopdf`)
- Live LLM flakes (network transient issues)

### Skipped Tests

```
tests/integration/test_openai.py::test_analysis_with_gpt4 SKIPPED (OpenAI API key not set)
```

**Meaning:** Test was skipped due to missing requirement

**Common skips:**

- Missing API keys (OpenAI, Anthropic)
- Optional dependencies not installed
- Platform-specific tests (macOS-only, etc.)

---

## Test Coverage

### Generate Coverage Report

```bash
# HTML coverage report
pytest tests/ --cov=find_evil_agent --cov-report=html

# Open in browser
open htmlcov/index.html

# Terminal coverage report
pytest tests/ --cov=find_evil_agent --cov-report=term

# XML coverage (for CI)
pytest tests/ --cov=find_evil_agent --cov-report=xml
```

### Coverage Metrics

```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
find_evil_agent/agents/analyzer.py       156      8    95%
find_evil_agent/agents/executor.py       134      6    96%
find_evil_agent/agents/orchestrator.py   245     12    95%
find_evil_agent/agents/tool_selector.py  178      9    95%
find_evil_agent/tools/registry.py        123      7    94%
-----------------------------------------------------------
TOTAL                                   2847    142    95%
```

**Coverage Goals:**

- Overall: ≥95%
- Critical paths: 100%
- Security validators: 100%

---

## Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Set up Python
        run: uv python install 3.11
      
      - name: Install dependencies
        run: uv pip install -e ".[dev]"
      
      - name: Run unit tests
        run: uv run pytest tests/unit/ -v
      
      - name: Run integration tests
        run: uv run pytest tests/integration/ -v -m integration
      
      - name: Generate coverage
        run: uv run pytest tests/ --cov=find_evil_agent --cov-report=xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

---

## Debugging Tests

### Run Single Test with Output

```bash
# Show print statements and detailed output
pytest tests/unit/agents/test_analyzer.py::test_extracts_ips -v -s

# Drop into debugger on failure
pytest tests/unit/agents/test_analyzer.py --pdb

# Drop into debugger on first failure, then stop
pytest tests/ -x --pdb
```

### Logging During Tests

```python
import logging

def test_with_logging(caplog):
    """Example test with log capture"""
    caplog.set_level(logging.INFO)
    
    agent = ToolSelectorAgent()
    result = agent.select_tool(...)
    
    # Check logs
    assert "Tool selected: volatility" in caplog.text
```

### Performance Profiling

```bash
# Profile test execution
pytest tests/ --profile

# With svg flamegraph
pytest tests/ --profile-svg

# Slowest 10 tests
pytest tests/ --durations=10
```

---

## Test Best Practices

### ✅ Do

- Write tests BEFORE implementation
- Test one thing per test
- Use descriptive test names
- Use real integrations (no mocks for integration tests)
- Clean up resources in teardown
- Use fixtures for common setup
- Run tests frequently during development

### ❌ Don't

- Skip writing tests ("we'll add them later")
- Use mocks in integration tests
- Test multiple things in one test
- Rely on test execution order
- Leave tests commented out
- Ignore flaky tests
- Commit failing tests

---

## Troubleshooting Test Failures

### Ollama Connection Errors

```
ERROR: Failed to connect to Ollama at http://localhost:11434
```

**Solution:**

```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama
ollama serve

# Verify model is loaded
ollama list
```

### SIFT VM SSH Errors

```
ERROR: SSH connection to 192.168.12.101:22 failed
```

**Solution:**

```bash
# Check SIFT VM is running
ping 192.168.12.101

# Check SSH connectivity
ssh sansforensics@192.168.12.101

# Verify environment variables
echo $SIFT_VM_HOST
echo $SIFT_SSH_USER
```

### API Key Missing

```
SKIPPED [1] tests/integration/test_openai.py:12: OpenAI API key not set
```

**Solution:**

```bash
# Set API key
export OPENAI_API_KEY=sk-proj-...

# Or: Use .env file
echo "OPENAI_API_KEY=sk-proj-..." >> .env
```

---

## Next Steps

- [Contributing](contributing.md) - Contribution guidelines
- [Architecture](architecture.md) - System architecture
- [Development Setup](getting-started.md) - Local development
- [CI/CD](release.md) - Release process
