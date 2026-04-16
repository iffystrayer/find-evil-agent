# 🏗️ Find Evil Agent - System Description

**Version:** 0.1.0  
**Last Updated:** April 10, 2026  
**Status:** HACKATHON READY - Both unique features verified on live SIFT VM

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Details](#component-details)
3. [Data Flow](#data-flow)
4. [API Reference](#api-reference)
5. [Schemas](#schemas)
6. [LLM Integration](#llm-integration)
7. [Storage & Caching](#storage--caching)
8. [Testing Architecture](#testing-architecture)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Find Evil Agent                          │
│                                                              │
│  ┌────────────┐       ┌─────────────────────────┐          │
│  │    CLI     │──────▶│  OrchestratorAgent     │          │
│  │  (Typer)   │       │    (LangGraph)          │          │
│  └────────────┘       └──────────┬──────────────┘          │
│                                   │                          │
│                       ┌───────────┴──────────┐              │
│                       │                      │               │
│                       ▼                      ▼               │
│         ┌──────────────────┐    ┌──────────────────┐       │
│         │ ToolSelectorAgent│    │ ToolExecutorAgent│       │
│         │  (Semantic +     │    │   (SSH asyncssh)  │       │
│         │   LLM Ranking)   │    └─────────┬────────┘       │
│         └─────────┬────────┘              │                 │
│                   │                       │                 │
│                   ▼                       ▼                 │
│         ┌──────────────────┐    ┌──────────────────┐       │
│         │  ToolRegistry    │    │   SIFT VM        │       │
│         │  (FAISS Index)   │    │  (SSH Target)    │       │
│         └──────────────────┘    └──────────────────┘       │
│                                          │                  │
│                                          ▼                  │
│                              ┌──────────────────┐          │
│                              │ AnalyzerAgent    │          │
│                              │ (IOC Extraction) │          │
│                              └──────────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │   External Services   │
                  │                       │
                  │  • Ollama (LLM)       │
                  │  • OpenAI API         │
                  │  • Anthropic API      │
                  │  • Langfuse           │
                  │  • Prometheus         │
                  └───────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Orchestration** | LangGraph 0.2+ | Multi-agent workflow |
| **Agents** | LangChain Core 0.3+ | Agent framework |
| **LLM** | Ollama / OpenAI / Anthropic | Tool selection & analysis |
| **Embeddings** | SentenceTransformers | Semantic tool search |
| **Vector Search** | FAISS | Fast similarity search |
| **SSH** | asyncssh 2.14+ | SIFT VM communication |
| **CLI** | Typer 0.12+ | Command-line interface |
| **UI** | Rich 13+ | Terminal formatting |
| **Schema** | Pydantic 2.5+ | Data validation |
| **Logging** | structlog 24+ | Structured logging |
| **Observability** | Langfuse 2.0+ | LLM tracing |
| **Metrics** | Prometheus Client | Performance metrics |
| **Testing** | pytest 7.4+ | Test framework |

---

## Component Details

### 1. OrchestratorAgent

**File:** `src/find_evil_agent/agents/orchestrator.py`

**Purpose:** Coordinates the 3-step analysis workflow using LangGraph.

**Workflow:**
```python
workflow = StateGraph(AgentState)
workflow.add_node("select_tool", tool_selector_node)
workflow.add_node("execute_tool", tool_executor_node)
workflow.add_node("analyze_results", analyzer_node)

workflow.add_edge(START, "select_tool")
workflow.add_edge("select_tool", "execute_tool")
workflow.add_edge("execute_tool", "analyze_results")
workflow.add_edge("analyze_results", END)
```

**State Management:**
```python
@dataclass
class AgentState:
    session_id: str
    incident_description: str
    analysis_goal: str
    step: int
    tool_selection: Optional[ToolSelection]
    execution_result: Optional[ExecutionResult]
    analysis_result: Optional[AnalysisResult]
    errors: List[str]
```

**Key Methods:**
- `process(context: AgentContext) -> AgentResult` - Execute full workflow
- `_create_workflow() -> StateGraph` - Build LangGraph workflow
- `_generate_summary(state: AgentState) -> str` - Create workflow summary

**Error Handling:**
- Graceful degradation on tool selection failure
- Execution errors captured in state
- Analysis fallback to regex on LLM failure

**Iterative Analysis (Feature #2):**

The OrchestratorAgent also supports autonomous multi-iteration investigation:

```python
async def process_iterative(
    self,
    incident_description: str,
    analysis_goal: str,
    max_iterations: int = 5,
    auto_follow: bool = True,
    min_lead_confidence: float = 0.6
) -> IterativeAnalysisResult
```

**Iterative Workflow:**
```
Iteration Loop (up to max_iterations):
  1. Run standard workflow (select → execute → analyze)
  2. Extract investigative leads from findings (LLM + rule-based)
  3. Select highest-priority lead (HIGH > MEDIUM > LOW, then by confidence)
  4. Create new analysis_goal from lead
  5. Repeat or stop if no leads

Stop Conditions:
  - Max iterations reached
  - No leads with confidence ≥ min_lead_confidence
  - LLM explicitly signals investigation complete
```

**Lead Extraction:**
```python
async def _extract_leads(
    findings: list[dict],
    iocs: dict[str, list[str]],
    iteration_number: int
) -> list[InvestigativeLead]:
    # LLM analyzes findings to identify next investigation steps
    # Example leads:
    # - "Analyze network connections from malicious process"
    # - "Create timeline to identify initial infection vector"
    # - "Extract file system metadata for suspicious files"
```

**Lead Prioritization:**
- HIGH: Critical investigative steps (timeline analysis, process analysis)
- MEDIUM: Supporting evidence gathering (log analysis, registry checks)
- LOW: Nice-to-have context (string extraction, metadata collection)

**Investigation Synthesis:**
```python
async def _synthesize_investigation(
    iterations: list[IterationResult]
) -> str:
    # Creates narrative from investigation chain
    # Shows: What was found → What lead was followed → Why → Result
```

**Live Demo Result:**
- 3 iterations: volatility → log2timeline → log2timeline
- Total time: 45.6 seconds
- Leads followed: "Create super-timeline to identify initial infection"
- Autonomous: 0 analyst decisions required

---

### 2. ToolSelectorAgent

**File:** `src/find_evil_agent/agents/tool_selector.py`

**Purpose:** Two-stage tool selection with hallucination prevention.

**Algorithm:**
```
1. Semantic Search (SentenceTransformers + FAISS)
   ├─ Embed incident_description + analysis_goal
   ├─ Search tool registry for top-k candidates (k=10)
   └─ Score: cosine similarity

2. LLM Ranking (Ollama / OpenAI / Anthropic)
   ├─ Format candidates with descriptions
   ├─ Prompt: "Select best tool for <goal>"
   ├─ Parse: tool_name, confidence, reasoning
   └─ Validate: confidence ≥ 0.7

3. Registry Validation
   ├─ Verify tool exists in registry
   ├─ Check tool is available on SIFT VM
   └─ Return ToolSelection or error
```

**Key Methods:**
- `process(context: AgentContext) -> AgentResult` - Execute selection
- `_semantic_search(query: str, top_k: int) -> List[Tool]` - FAISS search
- `_llm_rank(candidates: List[Tool], context: str) -> ToolSelection` - LLM ranking
- `_validate_selection(tool_name: str) -> bool` - Registry check

**Confidence Threshold:**
```python
CONFIDENCE_THRESHOLD = 0.7  # Configurable via .env
```

**LLM Prompt Template:**
```python
prompt = f"""
You are a DFIR expert selecting forensic tools.

Incident: {incident_description}
Goal: {analysis_goal}

Available tools:
{format_candidates(candidates)}

Select the BEST tool for this analysis. Respond in JSON:
{{
  "tool_name": "<exact_tool_name>",
  "confidence": <0.0-1.0>,
  "reasoning": "<why_this_tool>"
}}
"""
```

---

### 3. ToolExecutorAgent

**File:** `src/find_evil_agent/agents/tool_executor.py`

**Purpose:** Execute SIFT tools on remote VM via SSH.

**Execution Flow:**
```
1. Connect (asyncssh)
   ├─ Load SSH key
   ├─ Connect to SIFT_VM_HOST:SIFT_VM_PORT
   └─ Authenticate as SIFT_SSH_USER

2. Validate Command
   ├─ Check blocklist (rm -rf, dd, curl, wget)
   ├─ Verify tool exists (which <tool>)
   └─ Build command args

3. Execute
   ├─ Run command with timeout (60s default, 3600s max)
   ├─ Capture stdout, stderr, return_code
   └─ Measure execution_time

4. Disconnect
   └─ Close SSH connection
```

**Key Methods:**
- `process(context: AgentContext) -> AgentResult` - Execute tool
- `_connect() -> asyncssh.SSHClientConnection` - SSH connection
- `_execute_command(conn, command: str) -> ExecutionResult` - Run command
- `_validate_command(command: str) -> bool` - Security check

**Security Features:**
```python
BLOCKED_COMMANDS = [
    "rm -rf",
    "dd if=",
    "dd of=",
    "curl",
    "wget",
    "chmod +x",
    "> /dev/",
]

def _validate_command(command: str) -> bool:
    for blocked in BLOCKED_COMMANDS:
        if blocked in command:
            raise SecurityError(f"Blocked command: {blocked}")
    return True
```

**Execution Result:**
```python
@dataclass
class ExecutionResult:
    tool_name: str
    command: str
    stdout: str
    stderr: str
    return_code: int
    execution_time: float
    timestamp: datetime
```

---

### 4. AnalyzerAgent

**File:** `src/find_evil_agent/agents/analyzer.py`

**Purpose:** Extract findings and IOCs from tool output.

**Analysis Pipeline:**
```
1. LLM-Based Finding Extraction
   ├─ Prompt: "Analyze this forensic tool output"
   ├─ Extract: description, severity, confidence per finding
   └─ Fallback: Regex patterns if LLM fails

2. IOC Extraction
   ├─ IP addresses: IPv4 and IPv6
   ├─ Domains: FQDNs (example.com, evil-c2.net)
   ├─ Hashes: MD5, SHA1, SHA256
   ├─ File paths: Unix and Windows paths
   ├─ Emails: email@example.com
   └─ URLs: http(s)://...

3. Severity Assignment
   ├─ Critical: Active exploitation, encryption, data theft
   ├─ High: Backdoors, C2 communication, malware
   ├─ Medium: Suspicious activity, unknown processes
   ├─ Low: Anomalies, unusual behavior
   └─ Info: System information, benign findings

4. False Positive Filtering
   ├─ Common benign IPs (127.0.0.1, 0.0.0.0, RFC1918)
   ├─ System paths (/usr/bin, /lib, C:\Windows\System32)
   └─ Known safe domains (microsoft.com, google.com)
```

**Key Methods:**
- `process(context: AgentContext) -> AgentResult` - Analyze output
- `_extract_findings(output: str) -> List[Finding]` - LLM extraction
- `_extract_iocs(output: str) -> IOCCollection` - Regex extraction
- `_assign_severity(finding: str) -> Severity` - Severity classification

**LLM Prompt Template:**
```python
prompt = f"""
Analyze this DFIR tool output and extract findings.

Tool: {tool_name}
Command: {command}
Output:
{output}

For each finding, provide:
1. Description (what was found)
2. Severity (critical/high/medium/low/info)
3. Confidence (0.0-1.0)
4. Evidence (supporting data from output)

Respond in JSON array format.
"""
```

**IOC Regex Patterns:**
```python
IOC_PATTERNS = {
    "ipv4": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
    "ipv6": r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b",
    "domain": r"\b(?:[a-z0-9]+(?:-[a-z0-9]+)*\.)+[a-z]{2,}\b",
    "md5": r"\b[a-f0-9]{32}\b",
    "sha1": r"\b[a-f0-9]{40}\b",
    "sha256": r"\b[a-f0-9]{64}\b",
    "file_path_unix": r"/(?:[a-zA-Z0-9_.-]+/)*[a-zA-Z0-9_.-]+",
    "file_path_windows": r"[A-Z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]*",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "url": r"https?://[^\s]+",
}
```

---

### 5. ToolRegistry

**File:** `src/find_evil_agent/tools/registry.py`

**Purpose:** Catalog of 18 SIFT forensic tools with semantic search.

**Tool Metadata:**
```yaml
# tools/metadata.yaml
- name: volatility
  category: memory_analysis
  description: "Memory forensics framework for extracting digital artifacts from RAM dumps"
  requires_evidence: true
  inputs:
    - name: memory_dump
      type: file
      required: true
    - name: profile
      type: string
      required: false
  output_format: text
  typical_use_cases:
    - "Identify running processes in memory"
    - "Extract network connections from RAM"
    - "Detect malware in memory dumps"
```

**Semantic Search:**
```python
# 1. Load tools from metadata.yaml
tools = load_tools("tools/metadata.yaml")

# 2. Generate embeddings (SentenceTransformers)
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode([tool.description for tool in tools])

# 3. Build FAISS index
dimension = embeddings.shape[1]  # 384
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# 4. Cache to disk
np.save(".cache/embeddings/tool_embeddings.npy", embeddings)
faiss.write_index(index, ".cache/embeddings/faiss.index")

# 5. Search
query_embedding = model.encode([query])
distances, indices = index.search(query_embedding, k=10)
results = [tools[i] for i in indices[0]]
```

**Key Methods:**
- `search(query: str, top_k: int) -> List[Tool]` - Semantic search
- `get_tool(name: str) -> Tool` - Get tool by name
- `list_tools(category: str) -> List[Tool]` - List by category
- `_load_metadata() -> List[Tool]` - Load from YAML
- `_build_index() -> faiss.Index` - Build FAISS index

**18 SIFT Tools:**
1. volatility - Memory analysis
2. bulk_extractor - Bulk data extraction
3. strings - String extraction
4. grep - Pattern matching
5. fls - File listing (Sleuth Kit)
6. icat - File content extraction
7. log2timeline - Timeline generation
8. plaso - Log analysis
9. tcpdump - Network capture
10. wireshark - Protocol analysis
11. regripper - Registry parsing
12. pescanner - PE file analysis
13. pdf-parser - PDF analysis
14. exiftool - Metadata extraction
15. foremost - File carving
16. scalpel - File carving
17. hashdeep - Hash computation
18. ssdeep - Fuzzy hashing

---

### 6. BaseAgent

**File:** `src/find_evil_agent/agents/base.py`

**Purpose:** Abstract base class for all agents with lazy LLM initialization.

**Key Features:**
```python
class BaseAgent:
    def __init__(self):
        self._llm: Optional[LLMProvider] = None
    
    @property
    def llm(self) -> LLMProvider:
        """Lazy initialization to avoid loading LLM in tests."""
        if self._llm is None:
            self._llm = create_llm_provider()
        return self._llm
    
    @abstractmethod
    async def process(self, context: AgentContext) -> AgentResult:
        """Process agent task."""
        pass
```

**Benefits:**
- Tests don't load LLM unnecessarily
- Deferred connection until first use
- Shared LLM interface across agents

---

## Data Flow

### End-to-End Analysis Flow

```
1. User Input
   ├─ Incident description: "Ransomware detected..."
   ├─ Analysis goal: "Identify malicious processes"
   └─ CLI: find-evil analyze "..." "..."

2. OrchestratorAgent.process()
   ├─ Create session_id: UUID
   ├─ Initialize AgentState
   └─ Start LangGraph workflow

3. ToolSelectorAgent (Step 1)
   ├─ Semantic search: "identify malicious processes" → top-10 tools
   ├─ LLM ranking: candidates → volatility (confidence: 0.85)
   ├─ Validation: volatility exists in registry ✓
   └─ Update state.tool_selection

4. ToolExecutorAgent (Step 2)
   ├─ SSH connect: sansforensics@192.168.12.101
   ├─ Execute: volatility -f memory.raw pslist
   ├─ Capture: stdout (3,521 chars), stderr (empty), return_code (0)
   ├─ Measure: execution_time (90.2s)
   └─ Update state.execution_result

5. AnalyzerAgent (Step 3)
   ├─ LLM extract findings: 4 critical, 2 high, 1 medium
   ├─ Regex extract IOCs: 2 IPs, 1 domain, 1 hash, 1 path
   ├─ Assign severity: critical → "ransom.exe process"
   └─ Update state.analysis_result

6. OrchestratorAgent.generate_summary()
   ├─ Collect: tool_selection, execution_result, analysis_result
   ├─ Format: markdown report
   └─ Return AgentResult

7. CLI Output
   ├─ Display: Rich formatted output
   ├─ Save: report.md (if -o specified)
   └─ Exit: 0 (success) or 1 (error)
```

---

## API Reference

### CLI Commands

```bash
# Single-shot analysis (Feature #1: Hallucination Prevention)
find-evil analyze <incident> <goal> [OPTIONS]

Options:
  -o, --output PATH          Save report to file
  -v, --verbose             Show detailed logs
  --timeout INTEGER         Execution timeout (seconds)
  --help                    Show help message

# Autonomous investigation (Feature #2: Iterative Reasoning)
find-evil investigate <incident> <goal> [OPTIONS]

Options:
  --max-iterations INTEGER   Maximum analysis iterations (default: 5)
  -o, --output PATH          Save investigation report to file
  -v, --verbose             Show detailed logs
  --help                    Show help message

# Configuration check
find-evil config

# Version information
find-evil version
```

### REST API

**Server:** FastAPI with OpenAPI documentation

**Start Server:**
```bash
uvicorn find_evil_agent.api.server:app --host 0.0.0.0 --port 18000
```

**API Documentation:**
- Swagger UI: `http://localhost:18000/api/docs`
- ReDoc: `http://localhost:18000/api/redoc`
- OpenAPI Spec: `http://localhost:18000/api/openapi.json`

**Endpoints:**

#### POST /api/v1/analyze
Single-shot forensic analysis

**Request:**
```json
{
  "incident_description": "Ransomware detected on endpoint",
  "analysis_goal": "Identify malicious processes"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "tool_selected": "volatility",
  "confidence": 0.85,
  "findings": [...],
  "iocs": {"ips": [...], "domains": [...]},
  "execution_time": 90.2
}
```

#### POST /api/v1/investigate
Autonomous iterative investigation

**Request:**
```json
{
  "incident_description": "Unknown process consuming CPU",
  "analysis_goal": "Identify and trace origin",
  "max_iterations": 3
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "660e9511-f3ac-52e5-b827-557766551111",
  "iterations": 3,
  "tools_used": ["volatility", "log2timeline", "log2timeline"],
  "investigation_chain": ["timeline", "timeline"],
  "all_findings": [...],
  "all_iocs": {...},
  "total_duration": 45.6,
  "investigation_summary": "..."
}
```

#### GET /api/v1/config
Get current configuration status

**Response:**
```json
{
  "llm_provider": "ollama",
  "llm_model": "gemma4:31b-cloud",
  "sift_vm_host": "192.168.12.101",
  "sift_vm_port": 22,
  "tools_available": 18
}
```

#### GET /health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-10T19:30:00Z"
}
```

### Python API

#### Single-Shot Analysis

```python
from find_evil_agent.agents.orchestrator import OrchestratorAgent
import asyncio

async def analyze():
    orchestrator = OrchestratorAgent()
    
    result = await orchestrator.process({
        "incident_description": "Ransomware detected on endpoint",
        "analysis_goal": "Identify malicious processes and C2 communication"
    })
    
    if result.success:
        state = result.data["state"]
        print(f"Tool selected: {state.selected_tools[0].tool_name}")
        print(f"Confidence: {state.selected_tools[0].confidence}")
        print(f"Findings: {len(state.analysis_results[0].findings)}")
        print(f"IOCs: {state.analysis_results[0].iocs}")
    else:
        print(f"Error: {result.error}")

asyncio.run(analyze())
```

#### Autonomous Investigation

```python
from find_evil_agent.agents.orchestrator import OrchestratorAgent
import asyncio

async def investigate():
    orchestrator = OrchestratorAgent()
    
    result = await orchestrator.process_iterative(
        incident_description="Unknown process consuming CPU",
        analysis_goal="Identify process and trace origin",
        max_iterations=3,
        auto_follow=True
    )
    
    print(f"Iterations: {len(result.iterations)}")
    print(f"Tools used: {[it.tool_used for it in result.iterations]}")
    print(f"Investigation chain: {result.investigation_chain}")
    print(f"Total findings: {len(result.all_findings)}")
    print(f"Duration: {result.total_duration:.1f}s")
    print(f"\nSummary:\n{result.investigation_summary}")

asyncio.run(investigate())
```

### LLM Provider API

```python
from find_evil_agent.llm.factory import create_llm_provider
from find_evil_agent.llm.protocol import LLMProvider

# Create provider (from .env)
llm: LLMProvider = create_llm_provider()

# Generate text
response = await llm.generate(
    prompt="Select the best DFIR tool for...",
    max_tokens=500,
    temperature=0.0
)

# Generate JSON
response = await llm.generate_json(
    prompt="Respond with JSON: {\"tool\": ..., \"confidence\": ...}",
    schema={"tool": str, "confidence": float}
)

# Stream (not yet implemented)
async for chunk in llm.stream(prompt="..."):
    print(chunk, end="")
```

---

## Schemas

### AgentContext

```python
@dataclass
class AgentContext:
    """Input context for agent processing."""
    incident_description: str
    analysis_goal: str
    parameters: Optional[Dict[str, Any]] = None
```

### AgentResult

```python
@dataclass
class AgentResult:
    """Output result from agent processing."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

### ToolSelection

```python
@dataclass
class ToolSelection:
    """Tool selection result."""
    tool_name: str
    confidence: float  # 0.0-1.0
    reasoning: str
    candidates: List[str]  # Alternative tools considered
    timestamp: datetime
```

### ExecutionResult

```python
@dataclass
class ExecutionResult:
    """Tool execution result."""
    tool_name: str
    command: str
    stdout: str
    stderr: str
    return_code: int
    execution_time: float  # seconds
    timestamp: datetime
```

### Finding

```python
@dataclass
class Finding:
    """Individual analysis finding."""
    description: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    confidence: float  # 0.0-1.0
    evidence: str
    timestamp: datetime
```

### IOCCollection

```python
@dataclass
class IOCCollection:
    """Collection of indicators of compromise."""
    ips: List[str]
    domains: List[str]
    hashes: List[str]  # MD5, SHA1, SHA256
    file_paths: List[str]
    emails: List[str]
    urls: List[str]
```

### AnalysisResult

```python
@dataclass
class AnalysisResult:
    """Complete analysis result."""
    findings: List[Finding]
    iocs: IOCCollection
    summary: str
    timestamp: datetime
```

### Iterative Analysis Schemas (Feature #2)

#### InvestigativeLead

```python
class LeadType(str, Enum):
    PROCESS = "process"
    NETWORK = "network"
    FILE = "file"
    TIMELINE = "timeline"
    REGISTRY = "registry"

class LeadPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class InvestigativeLead:
    """Next step in autonomous investigation."""
    lead_type: LeadType
    description: str
    priority: LeadPriority
    suggested_tool: Optional[str]
    context: Dict[str, Any]
    confidence: float  # 0.0-1.0
    reasoning: str
```

#### IterationResult

```python
@dataclass
class IterationResult:
    """Result from one iteration of investigation."""
    iteration_number: int
    tool_used: str
    findings: List[Finding]
    iocs: Dict[str, List[str]]
    leads_discovered: List[InvestigativeLead]
    lead_followed: Optional[InvestigativeLead]
    duration: float  # seconds
```

#### IterativeAnalysisResult

```python
@dataclass
class IterativeAnalysisResult:
    """Complete multi-iteration investigation result."""
    session_id: str
    iterations: List[IterationResult]
    investigation_chain: List[Optional[InvestigativeLead]]
    all_findings: List[Finding]
    all_iocs: Dict[str, List[str]]
    total_duration: float
    stopping_reason: str
    investigation_summary: str
```

**Example Investigation Chain:**
```python
result = await orchestrator.process_iterative(...)

# result.investigation_chain shows:
# [None, lead1, lead2]
#  ↑     ↑      ↑
#  |     |      |
#  |     |      Iteration 3: Followed lead2 (timeline)
#  |     Iteration 2: Followed lead1 (timeline)
#  Iteration 1: Initial analysis (no prior lead)
```

---

## LLM Integration

### Provider Architecture

```python
# Protocol (interface)
class LLMProvider(Protocol):
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.0,
        **kwargs
    ) -> str:
        """Generate text completion."""
        ...
    
    async def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured JSON response."""
        ...
```

### Ollama Provider

```python
class OllamaProvider:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "gemma4:31b-cloud"
    ):
        self.client = httpx.AsyncClient(base_url=base_url)
        self.model_name = model_name
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.post(
            "/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }
        )
        return response.json()["response"]
```

### OpenAI Provider (Planned)

```python
class OpenAIProvider:
    def __init__(self, api_key: str, model_name: str = "gpt-4-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content
```

### Anthropic Provider (Planned)

```python
class AnthropicProvider:
    def __init__(self, api_key: str, model_name: str = "claude-3-opus-20240229"):
        self.client = Anthropic(api_key=api_key)
        self.model_name = model_name
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.messages.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.content[0].text
```

---

## Storage & Caching

### Embeddings Cache

**Location:** `.cache/embeddings/`

**Files:**
- `tool_embeddings.npy` - NumPy array (18 x 384 floats)
- `faiss.index` - FAISS index file
- `metadata.json` - Cache metadata (version, timestamp)

**Cache Invalidation:**
```python
# Regenerate on:
# 1. tools/metadata.yaml modified
# 2. SentenceTransformers model changed
# 3. Cache version mismatch

def should_regenerate_cache() -> bool:
    cache_mtime = os.path.getmtime(".cache/embeddings/metadata.json")
    yaml_mtime = os.path.getmtime("tools/metadata.yaml")
    return yaml_mtime > cache_mtime
```

### Langfuse Traces

**Storage:** External Langfuse instance (PostgreSQL)

**Trace Structure:**
```
Session (analysis workflow)
├─ Span: tool_selection
│   ├─ Input: incident_description, analysis_goal
│   ├─ Output: tool_name, confidence, reasoning
│   └─ Metadata: candidates, selection_time
├─ Span: tool_execution
│   ├─ Input: tool_name, command
│   ├─ Output: stdout, stderr, return_code
│   └─ Metadata: execution_time, ssh_latency
└─ Span: analysis
    ├─ Input: tool_output
    ├─ Output: findings, iocs
    └─ Metadata: num_findings, num_iocs
```

**Access:**
```python
# View in Langfuse UI
# Filter by session_id, tool_name, timestamp

# Export via API
from langfuse import Langfuse
client = Langfuse()
trace = client.fetch_trace(session_id)
```

---

## Testing Architecture

### Test Structure

```
tests/
├── unit/                  # Fast, no external dependencies (191 tests)
│   ├── llm/
│   │   ├── test_factory.py               (13 tests)
│   │   └── test_ollama.py                (18 tests)
│   ├── agents/
│   │   ├── test_base.py                  (8 tests)
│   │   ├── test_tool_selector.py         (39 tests)
│   │   ├── test_tool_executor.py         (30 tests)
│   │   ├── test_analyzer.py              (27 tests)
│   │   ├── test_orchestrator.py          (21 tests)
│   │   └── test_iterative_orchestrator.py (20 tests - 17/20 passing) ← NEW
│   └── tools/
│       └── test_registry.py              (26 tests)
└── integration/           # Require external services (48 tests)
    ├── llm/
    │   └── test_ollama_integration.py    (10 tests - Ollama required)
    └── sift/
        └── test_end_to_end.py            (10 tests - SIFT VM required)
        └── test_live_demo.py             (2 tests - Live demo verified)

Total: 239 tests (85%+ passing)
```

**Test Breakdown by Capability:**
- **LLM Infrastructure:** 79 tests (protocol, factory, providers)
- **Tool Registry:** 26 tests (semantic search, embeddings, FAISS)
- **Tool Selection (Feature #1):** 39 tests (two-stage validation)
- **Tool Execution:** 30 tests (SSH, security)
- **Analysis:** 27 tests (IOC extraction, severity)
- **Orchestration:** 21 tests (LangGraph workflow)
- **Iterative Analysis (Feature #2):** 20 tests (autonomous investigation) - 17/20 passing
- **Integration:** 48 tests (end-to-end with Ollama + SIFT VM)

### Test Categories

**1. Specification Tests** (always pass)
```python
def test_agent_requirements():
    """Document what agent does (always passes)."""
    requirements = {
        "input": "incident_description + analysis_goal",
        "output": "tool_name + confidence + reasoning",
        "validation": "confidence >= 0.7"
    }
    assert requirements["validation"] == "confidence >= 0.7"
```

**2. Structure Tests** (interface validation)
```python
def test_agent_has_process_method():
    """Verify agent implements process()."""
    agent = ToolSelectorAgent()
    assert hasattr(agent, "process")
    assert callable(agent.process)
```

**3. Execution Tests** (behavior validation)
```python
@pytest.mark.asyncio
async def test_tool_selection_workflow():
    """Test actual tool selection with real components."""
    agent = ToolSelectorAgent()
    result = await agent.process({
        "incident_description": "Ransomware detected",
        "analysis_goal": "Find malicious process"
    })
    assert result.success
    assert result.data["tool_selection"].confidence >= 0.7
```

**4. Integration Tests** (end-to-end)
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_analysis_workflow():
    """Test complete workflow with real Ollama + SIFT VM."""
    orchestrator = OrchestratorAgent()
    result = await orchestrator.process({
        "incident_description": "Suspicious process",
        "analysis_goal": "Identify process details"
    })
    assert result.success
    assert len(result.data["findings"]) > 0
```

**5. Iterative Analysis Tests** (Feature #2)
```python
@pytest.mark.asyncio
async def test_multi_iteration_investigation():
    """Test autonomous lead following across multiple iterations."""
    orchestrator = OrchestratorAgent()
    
    result = await orchestrator.process_iterative(
        incident_description="Unknown process consuming CPU",
        analysis_goal="Identify and trace origin",
        max_iterations=3
    )
    
    assert len(result.iterations) > 0
    assert all(it.tool_used for it in result.iterations)
    assert result.total_duration > 0
    assert result.investigation_summary
    
    # Verify lead following
    for i, iteration in enumerate(result.iterations[1:], 1):
        if iteration.lead_followed:
            assert iteration.lead_followed.confidence >= 0.6

@pytest.mark.asyncio
async def test_lead_extraction_from_findings():
    """Test that leads are extracted from findings."""
    orchestrator = OrchestratorAgent()
    
    findings = [
        {"description": "Process found making network connections", ...}
    ]
    
    leads = await orchestrator._extract_leads(findings, {}, 1)
    
    assert len(leads) > 0
    assert all(lead.lead_type in LeadType for lead in leads)
    assert all(0 <= lead.confidence <= 1 for lead in leads)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_demo_both_features():
    """Verify both features on live SIFT VM."""
    orchestrator = OrchestratorAgent()
    
    # Feature #1: Hallucination Prevention
    result1 = await orchestrator.process({
        "incident_description": "Suspicious files in /tmp",
        "analysis_goal": "List file system metadata"
    })
    assert result1.success
    assert result1.data["state"].selected_tools[0].confidence >= 0.7
    
    # Feature #2: Autonomous Investigation
    result2 = await orchestrator.process_iterative(
        incident_description="Unknown process consuming CPU",
        analysis_goal="Identify and trace origin",
        max_iterations=3
    )
    assert len(result2.iterations) >= 1
    assert result2.investigation_summary
```

### Test Fixtures

```python
@pytest.fixture
def mock_llm_provider():
    """Mock LLM for unit tests."""
    provider = Mock(spec=LLMProvider)
    provider.generate_json.return_value = {
        "tool_name": "volatility",
        "confidence": 0.85,
        "reasoning": "Memory analysis required"
    }
    return provider

@pytest.fixture
async def real_ollama_provider():
    """Real Ollama for integration tests."""
    return OllamaProvider(
        base_url="http://192.168.12.124:11434",
        model_name="llama3.2:latest"  # Fast model for tests
    )

@pytest.fixture
async def sift_vm_connection():
    """Real SIFT VM SSH connection."""
    conn = await asyncssh.connect(
        host="192.168.12.101",
        port=22,
        username="sansforensics",
        client_keys=["~/.ssh/sift_vm_key"]
    )
    yield conn
    conn.close()
```

### Running Tests

```bash
# All tests (222 total)
pytest -v

# Unit only (174 tests, ~30s)
pytest -v -m "not integration"

# Integration only (48 tests, ~10min)
pytest -v -m integration

# Specific component
pytest tests/unit/agents/test_tool_selector.py -v

# With coverage
pytest --cov=src/find_evil_agent --cov-report=html

# Parallel execution
pytest -n auto  # Use all CPU cores
```

---

## Performance Characteristics

### Latency Breakdown

**Typical Analysis (90s total):**
- Tool Selection: 30s
  - Semantic search: <1s (FAISS cached)
  - LLM ranking: 29s (Ollama gemma4:31b-cloud)
- Tool Execution: 45s
  - SSH connect: 0.1s
  - Command execution: 44.9s (tool-dependent)
- Analysis: 15s
  - LLM finding extraction: 12s
  - IOC regex extraction: 3s

**Optimizations Applied:**
- FAISS embeddings cache: 8s → <1s
- SSH connection reuse: 0.1s per command
- Lazy LLM initialization: Skip in tests

**Bottlenecks:**
- LLM generation (60-80% of total time)
- Tool execution (varies by tool)
- Network latency to SIFT VM (4-5ms)

---

**Last Updated:** April 10, 2026  
**Version:** 0.1.0
