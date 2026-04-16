# Architecture

Find Evil Agent uses a multi-agent architecture orchestrated by LangGraph to provide hallucination-resistant tool selection and autonomous investigative reasoning.

## System Overview

```mermaid
graph TB
    subgraph "Client Layer"
        CLI[CLI Interface<br/>Typer + Rich]
        REST[REST API<br/>FastAPI]
        MCP[MCP Server<br/>FastMCP]
    end
    
    subgraph "Orchestration Layer"
        ORCH[OrchestratorAgent<br/>LangGraph StateGraph]
    end
    
    subgraph "Agent Layer"
        SEL[ToolSelectorAgent<br/>Two-Stage Selection]
        EXEC[ToolExecutorAgent<br/>SSH Execution]
        ANAL[AnalyzerAgent<br/>IOC Extraction]
    end
    
    subgraph "Infrastructure Layer"
        REG[ToolRegistry<br/>FAISS Vector Store]
        BASE[BaseAgent<br/>Lazy LLM Init]
    end
    
    subgraph "External Services"
        SIFT[SIFT VM<br/>18+ Forensic Tools]
        LLM[LLM Provider<br/>Ollama/OpenAI/Anthropic]
        LANG[Langfuse<br/>Observability]
    end
    
    CLI --> ORCH
    REST --> ORCH
    MCP --> ORCH
    
    ORCH --> SEL
    ORCH --> EXEC
    ORCH --> ANAL
    
    SEL --> REG
    SEL --> LLM
    EXEC --> SIFT
    ANAL --> LLM
    
    SEL -.-> BASE
    EXEC -.-> BASE
    ANAL -.-> BASE
    
    ORCH -.-> LANG
    SEL -.-> LANG
    EXEC -.-> LANG
    ANAL -.-> LANG
```

## Component Architecture

### OrchestratorAgent

**Purpose:** Coordinates the 3-step analysis workflow using LangGraph.

**Workflow:**

```mermaid
stateDiagram-v2
    [*] --> SelectTool
    SelectTool --> ExecuteTool: Tool Selected
    ExecuteTool --> AnalyzeResults: Execution Complete
    AnalyzeResults --> [*]: Analysis Complete
    
    SelectTool --> [*]: Selection Failed
    ExecuteTool --> [*]: Execution Failed
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

**Key Responsibilities:**

- Workflow orchestration
- State management across agents
- Error handling and recovery
- Report generation

### ToolSelectorAgent

**Purpose:** Two-stage tool selection with hallucination prevention.

**Algorithm:**

```mermaid
flowchart TD
    A[Incident Description<br/>+ Analysis Goal] --> B[Stage 1: Semantic Search<br/>SentenceTransformers + FAISS]
    B --> C[Top-10 Candidates]
    C --> D[Stage 2: LLM Ranking<br/>Ollama/OpenAI/Anthropic]
    D --> E{Confidence ≥ 0.7?}
    E -->|Yes| F[Stage 3: Registry Validation]
    E -->|No| G[Reject Selection]
    F --> H{Tool Exists?}
    H -->|Yes| I[Tool Confirmed]
    H -->|No| G
    G --> J[Request More Context]
```

**Hallucination Prevention:**

1. **Semantic Search:** Narrows to real tools only (FAISS index of 18 tools)
2. **LLM Ranking:** Selects best tool with reasoning
3. **Confidence Threshold:** Rejects uncertain selections (≥0.7 required)
4. **Registry Validation:** Confirms tool exists before execution

**Key Features:**

- Impossible to hallucinate tools (FAISS only returns real tools)
- Confidence scoring prevents low-quality selections
- Alternative tools provided for transparency
- Reasoning captured for audit trail

### ToolExecutorAgent

**Purpose:** Execute SIFT tools safely on remote VM via SSH.

**Execution Flow:**

```mermaid
sequenceDiagram
    participant E as ExecutorAgent
    participant V as SSH Validator
    participant S as SIFT VM
    
    E->>V: Validate Command
    V->>V: Check Blocklist<br/>(rm -rf, dd, curl)
    V->>V: Verify Tool Exists<br/>(which <tool>)
    V-->>E: Validation Result
    
    E->>S: SSH Connect
    S-->>E: Connection Established
    
    E->>S: Execute Tool<br/>(with timeout)
    S-->>E: stdout + stderr + return_code
    
    E->>E: Measure execution_time
    E->>S: Disconnect
```

**Security Features:**

```python
BLOCKED_COMMANDS = [
    "rm -rf",      # Destructive deletion
    "dd if=",      # Disk operations
    "dd of=",      # Disk writing
    "curl",        # External downloads
    "wget",        # External downloads
    "chmod +x",    # Permission changes
    "> /dev/",     # Device access
]
```

**Key Responsibilities:**

- SSH connection management
- Command validation
- Timeout enforcement (60s default, 3600s max)
- Evidence integrity (read-only operations)

### AnalyzerAgent

**Purpose:** Extract findings and IOCs from tool output.

**Analysis Pipeline:**

```mermaid
flowchart LR
    A[Tool Output] --> B[LLM Extraction<br/>Findings]
    A --> C[Regex Extraction<br/>IOCs]
    B --> D[Severity Assignment<br/>Critical→Info]
    C --> E[False Positive Filter<br/>127.0.0.1, RFC1918]
    D --> F[Analysis Result]
    E --> F
```

**IOC Extraction:**

| IOC Type | Pattern | Example |
|----------|---------|---------|
| IPv4 | `\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b` | 203.0.113.42 |
| IPv6 | `\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b` | 2001:db8::1 |
| Domain | `\b(?:[a-z0-9]+(?:-[a-z0-9]+)*\.)+[a-z]{2,}\b` | evil-c2.net |
| MD5 | `\b[a-f0-9]{32}\b` | 5d41402abc4b2a76b9719d911017c592 |
| SHA1 | `\b[a-f0-9]{40}\b` | aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d |
| SHA256 | `\b[a-f0-9]{64}\b` | 2c26b46b68ffc68ff99b453c1d30413413422d706... |
| File Path | `/(?:[a-zA-Z0-9_.-]+/)*[a-zA-Z0-9_.-]+` | /tmp/malware.exe |

**Severity Levels:**

- **Critical:** Active exploitation, encryption, data theft
- **High:** Backdoors, C2 communication, malware
- **Medium:** Suspicious activity, unknown processes
- **Low:** Anomalies, unusual behavior
- **Info:** System information, benign findings

### ToolRegistry

**Purpose:** Catalog of 18 SIFT forensic tools with semantic search.

**Tool Categories:**

| Category | Tools | Count |
|----------|-------|-------|
| Memory Analysis | volatility | 1 |
| Disk Forensics | fls, icat, foremost, scalpel | 4 |
| Timeline | log2timeline, plaso | 2 |
| Network | tcpdump, wireshark, bulk_extractor | 3 |
| Analysis | strings, grep, pdf-parser, pescanner | 4 |
| Hashing | hashdeep, ssdeep | 2 |
| Metadata | exiftool, regripper | 2 |

**Semantic Search Architecture:**

```mermaid
graph LR
    A[Tool Metadata<br/>tools/metadata.yaml] --> B[SentenceTransformers<br/>all-MiniLM-L6-v2]
    B --> C[Embeddings<br/>18 × 384 floats]
    C --> D[FAISS Index<br/>IndexFlatL2]
    D --> E[Cache<br/>.cache/embeddings/]
    
    F[Query] --> B
    B --> G[Query Embedding]
    G --> D
    D --> H[Top-K Results<br/>Cosine Similarity]
```

**Cache Strategy:**

- Embeddings cached to `.cache/embeddings/tool_embeddings.npy`
- FAISS index cached to `.cache/embeddings/faiss.index`
- Regenerated if `tools/metadata.yaml` modified
- Performance: 8s → <1s on subsequent searches

## Data Flow

### Single-Shot Analysis

```mermaid
sequenceDiagram
    participant U as User/Client
    participant O as Orchestrator
    participant S as ToolSelector
    participant E as ToolExecutor
    participant A as Analyzer
    
    U->>O: analyze(incident, goal)
    O->>O: Create session_id
    
    Note over O,S: Step 1: Tool Selection
    O->>S: select_tool(incident, goal)
    S->>S: Semantic search (FAISS)
    S->>S: LLM ranking
    S->>S: Validate confidence ≥0.7
    S-->>O: ToolSelection
    
    Note over O,E: Step 2: Tool Execution
    O->>E: execute_tool(tool_name)
    E->>E: SSH connect
    E->>E: Validate command
    E->>E: Execute with timeout
    E->>E: Disconnect
    E-->>O: ExecutionResult
    
    Note over O,A: Step 3: Analysis
    O->>A: analyze_output(tool_output)
    A->>A: LLM extract findings
    A->>A: Regex extract IOCs
    A->>A: Assign severity
    A-->>O: AnalysisResult
    
    O->>O: Generate report
    O-->>U: AgentResult
```

### Autonomous Investigation

```mermaid
sequenceDiagram
    participant U as User/Client
    participant O as Orchestrator
    participant L as LeadExtractor
    
    U->>O: investigate(incident, goal, max_iterations)
    
    loop For each iteration (up to max)
        Note over O: Run Standard Analysis
        O->>O: select → execute → analyze
        
        Note over O,L: Extract Leads
        O->>L: extract_leads(findings, iocs)
        L->>L: LLM identify next steps
        L->>L: Rule-based lead generation
        L-->>O: List[InvestigativeLead]
        
        alt Leads available
            O->>O: Select highest priority
            O->>O: Update analysis_goal
            Note over O: Continue to next iteration
        else No leads or max iterations
            Note over O: Stop investigation
        end
    end
    
    O->>O: Synthesize investigation
    O-->>U: IterativeAnalysisResult
```

## Technology Stack

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| langgraph | 0.2+ | Multi-agent orchestration |
| langchain-core | 0.3+ | Agent framework |
| sentence-transformers | 3.3+ | Text embeddings |
| faiss-cpu | 1.9+ | Vector similarity search |
| asyncssh | 2.14+ | SSH client library |
| pydantic | 2.5+ | Data validation |
| structlog | 24+ | Structured logging |

### Interface Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| typer | 0.12+ | CLI framework |
| rich | 13+ | Terminal formatting |
| fastapi | 0.115+ | REST API |
| mcp | 1.0+ | Model Context Protocol |

### LLM Providers

| Provider | Library | Models |
|----------|---------|--------|
| Ollama | httpx | gemma4, llama3.2, mistral |
| OpenAI | openai | gpt-4, gpt-4-turbo |
| Anthropic | anthropic | claude-3-opus, claude-3-sonnet |

### Observability

| Tool | Purpose | Port |
|------|---------|------|
| Langfuse | LLM tracing and monitoring | 33000 |
| Prometheus | Metrics collection | 60090 |
| structlog | Structured logging | N/A |

## State Management

### AgentState Schema

```python
@dataclass
class AgentState:
    """Shared state across LangGraph workflow."""
    
    # Session metadata
    session_id: str
    timestamp: datetime
    
    # Input
    incident_description: str
    analysis_goal: str
    
    # Workflow state
    step: int
    errors: List[str]
    
    # Agent outputs
    selected_tools: List[ToolSelection]
    execution_results: List[ExecutionResult]
    analysis_results: List[AnalysisResult]
    
    # Iterative investigation
    investigative_leads: List[InvestigativeLead]
    investigation_chain: List[Optional[InvestigativeLead]]
```

### State Transitions

```mermaid
stateDiagram-v2
    [*] --> Initial: Create State
    Initial --> ToolSelected: ToolSelector Success
    Initial --> Failed: ToolSelector Failed
    
    ToolSelected --> ToolExecuted: ToolExecutor Success
    ToolSelected --> Failed: ToolExecutor Failed
    
    ToolExecuted --> Analyzed: Analyzer Success
    ToolExecuted --> Failed: Analyzer Failed
    
    Analyzed --> LeadsExtracted: Extract Leads
    LeadsExtracted --> ToolSelected: Follow Lead (iterative)
    LeadsExtracted --> Complete: No More Leads
    
    Complete --> [*]
    Failed --> [*]
```

## Performance Characteristics

### Latency Breakdown

**Typical Analysis (90s total):**

| Component | Duration | % of Total |
|-----------|----------|-----------|
| Tool Selection | 30s | 33% |
| - Semantic search | <1s | <1% |
| - LLM ranking | 29s | 32% |
| Tool Execution | 45s | 50% |
| - SSH connect | 0.1s | <1% |
| - Command execution | 44.9s | 50% |
| Analysis | 15s | 17% |
| - LLM extraction | 12s | 13% |
| - IOC regex | 3s | 3% |

### Optimizations Applied

1. **FAISS Embeddings Cache:** 8s → <1s on subsequent searches
2. **SSH Connection Reuse:** Single connection per workflow
3. **Lazy LLM Initialization:** Skip in tests
4. **Parallel Analysis:** IOC extraction concurrent with LLM

### Bottlenecks

- **LLM Generation:** 60-80% of total time (tool selection + analysis)
- **Tool Execution:** Varies by tool (strings: 0.2s, volatility: 90s)
- **Network Latency:** 4-5ms to SIFT VM (local network)

## Error Handling

### Graceful Degradation

```python
# Tool selection fallback
try:
    selection = await selector.select_tool(incident, goal)
except LLMError:
    # Fallback to semantic search only
    selection = await selector.semantic_fallback(incident, goal)

# Analysis fallback
try:
    findings = await analyzer.llm_extract_findings(output)
except LLMError:
    # Fallback to regex-based extraction
    findings = await analyzer.regex_fallback(output)
```

### Error Categories

| Category | Handling | Recovery |
|----------|----------|----------|
| **Network Errors** | Retry with backoff | 3 attempts, exponential |
| **SSH Errors** | Connection pool | Reconnect on failure |
| **LLM Errors** | Fallback to regex | Continue without LLM |
| **Timeout Errors** | Kill process | Return partial output |
| **Validation Errors** | Reject command | Request user input |

## Security Architecture

### Threat Model

```mermaid
graph TD
    A[Threat: Tool Hallucination] --> B[Mitigation: FAISS Constraint]
    C[Threat: Command Injection] --> D[Mitigation: Blocklist Validation]
    E[Threat: SSH Compromise] --> F[Mitigation: Key-based Auth]
    G[Threat: Timeout DoS] --> H[Mitigation: Timeout Enforcement]
    I[Threat: Evidence Tampering] --> J[Mitigation: Read-only Ops]
```

### Security Controls

1. **Tool Hallucination:** FAISS only returns real tools from registry
2. **Command Injection:** Blocklist prevents destructive commands
3. **SSH Security:** Key-based authentication, no passwords
4. **Timeout DoS:** Configurable timeouts (60s default, 3600s max)
5. **Evidence Integrity:** Read-only operations on SIFT VM

## Next Steps

- [Components Deep Dive](components.md) - Detailed component documentation
- [Workflows](workflows.md) - Common workflow patterns
- [API Reference](api/cli.md) - Complete API documentation
- [Deployment](deployment/sift-setup.md) - Deployment and security guide
