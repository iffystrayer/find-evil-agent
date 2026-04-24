# REST API Reference

Complete HTTP API documentation for Find Evil Agent.

## Base URL

```
http://localhost:18000/api/v1
```

## Authentication

Currently no authentication required. For production deployment, implement API key authentication.

## Endpoints

### POST /api/v1/analyze

Single-shot incident analysis.

**Request:**
```json
{
  "incident_description": "Suspicious network traffic to 185.220.101.42",
  "analysis_goal": "Identify malicious processes and C2 communication",
  "provider": "ollama",
  "model": "llama3:8b",
  "confidence_threshold": 0.7,
  "timeout": 60
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "tool_selected": "netstat",
  "confidence": 0.85,
  "execution_time": 0.23,
  "command": "netstat -tulpn",
  "output": "...",
  "iocs": [
    {
      "type": "ip",
      "value": "185.220.101.42",
      "context": "Suspicious outbound connection",
      "severity": "HIGH"
    }
  ],
  "findings": [
    "Malicious process detected: svchost.exe",
    "C2 communication identified"
  ],
  "severity": "HIGH",
  "report_markdown": "# Incident Response Report\n...",
  "report_html": "<html>...</html>"
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "Invalid incident description",
  "details": "Description must be at least 10 characters"
}
```

### POST /api/v1/investigate

Multi-iteration autonomous investigation.

**Request:**
```json
{
  "incident_description": "Ransomware detected on Windows 10 endpoint",
  "analysis_goal": "Complete attack chain analysis",
  "max_iterations": 5,
  "provider": "openai",
  "model": "gpt-4"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "iterations": [
    {
      "iteration": 1,
      "tool": "volatility",
      "confidence": 0.88,
      "duration": 18.7,
      "leads_found": 3
    },
    {
      "iteration": 2,
      "tool": "log2timeline",
      "confidence": 0.82,
      "duration": 13.9,
      "leads_found": 2
    }
  ],
  "total_duration": 45.6,
  "total_iocs": 12,
  "final_report": "...",
  "attack_chain": [
    "Initial access via phishing email",
    "Credential dumping with Mimikatz",
    "Lateral movement to domain controller"
  ]
}
```

### GET /api/v1/models

List available LLM models.

**Query Parameters:**
- `provider` (optional) - Filter by provider (ollama/openai/anthropic)

**Request:**
```bash
GET /api/v1/models?provider=ollama
```

**Response:**
```json
{
  "provider": "ollama",
  "models": [
    {
      "name": "llama3:8b",
      "size": "4.7GB",
      "description": "Fast, efficient model"
    },
    {
      "name": "llama3:70b",
      "size": "39GB",
      "description": "High quality, slower"
    }
  ]
}
```

### GET /api/v1/tools

List available SIFT tools.

**Response:**
```json
{
  "tools": [
    {
      "name": "fls",
      "description": "List file and directory names in a disk image",
      "category": "file_system",
      "command_template": "fls -r {image_path}"
    },
    {
      "name": "strings",
      "description": "Extract printable strings from binary files",
      "category": "analysis",
      "command_template": "strings {file_path}"
    }
  ],
  "count": 18
}
```

### POST /api/v1/execute

Execute specific SIFT tool directly.

**Request:**
```json
{
  "tool_name": "strings",
  "arguments": {
    "file_path": "/evidence/malware.exe"
  },
  "timeout": 60
}
```

**Response:**
```json
{
  "success": true,
  "tool": "strings",
  "command": "strings /evidence/malware.exe",
  "output": "MZ\nThis program cannot be run...",
  "execution_time": 0.15,
  "exit_code": 0
}
```

### GET /api/v1/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "sift_vm": {
    "connected": true,
    "host": "192.168.12.101",
    "latency_ms": 12
  },
  "llm": {
    "provider": "ollama",
    "available": true,
    "models": 3
  }
}
```

### GET /api/v1/config

View current configuration (sanitized).

**Response:**
```json
{
  "llm_provider": "ollama",
  "sift_vm_host": "192.168.12.101",
  "min_confidence": 0.7,
  "max_iterations": 10,
  "observability_enabled": true
}
```

## Error Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 400 | Bad Request | Invalid input parameters |
| 404 | Not Found | Unknown endpoint |
| 500 | Internal Error | Server error, check logs |
| 503 | Service Unavailable | SIFT VM or LLM unavailable |
| 504 | Gateway Timeout | Command execution timeout |

## Rate Limiting

No rate limiting currently implemented. For production:

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/analyze")
@limiter.limit("10/minute")
def analyze():
    ...
```

## Examples

### cURL Examples

```bash
# Simple analysis
curl -X POST http://localhost:18000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "incident_description": "Malware detected",
    "analysis_goal": "Identify IOCs"
  }'

# Investigation with specific provider
curl -X POST http://localhost:18000/api/v1/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "incident_description": "Ransomware attack",
    "analysis_goal": "Complete timeline",
    "max_iterations": 5,
    "provider": "openai",
    "model": "gpt-4"
  }'

# List models
curl http://localhost:18000/api/v1/models

# Health check
curl http://localhost:18000/api/v1/health
```

### Python Client

```python
import requests

class FindEvilClient:
    def __init__(self, base_url="http://localhost:18000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def analyze(self, incident, goal, **kwargs):
        response = self.session.post(
            f"{self.base_url}/api/v1/analyze",
            json={
                "incident_description": incident,
                "analysis_goal": goal,
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()
    
    def investigate(self, incident, goal, max_iterations=3, **kwargs):
        response = self.session.post(
            f"{self.base_url}/api/v1/investigate",
            json={
                "incident_description": incident,
                "analysis_goal": goal,
                "max_iterations": max_iterations,
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()
    
    def list_models(self, provider=None):
        params = {"provider": provider} if provider else {}
        response = self.session.get(
            f"{self.base_url}/api/v1/models",
            params=params
        )
        return response.json()
    
    def health(self):
        response = self.session.get(f"{self.base_url}/api/v1/health")
        return response.json()

# Usage
client = FindEvilClient()

# Run analysis
result = client.analyze(
    incident="Suspicious network traffic",
    goal="Identify C2 servers",
    provider="ollama"
)
print(f"Found {len(result['iocs'])} IOCs")

# Multi-iteration investigation
investigation = client.investigate(
    incident="Ransomware detected",
    goal="Complete attack timeline",
    max_iterations=5
)
print(f"Completed {len(investigation['iterations'])} iterations")
```

### JavaScript/TypeScript Client

```typescript
class FindEvilClient {
  constructor(private baseUrl = 'http://localhost:18000') {}
  
  async analyze(incident: string, goal: string, options = {}) {
    const response = await fetch(`${this.baseUrl}/api/v1/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        incident_description: incident,
        analysis_goal: goal,
        ...options
      })
    });
    return response.json();
  }
  
  async investigate(incident: string, goal: string, maxIterations = 3) {
    const response = await fetch(`${this.baseUrl}/api/v1/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        incident_description: incident,
        analysis_goal: goal,
        max_iterations: maxIterations
      })
    });
    return response.json();
  }
}

// Usage
const client = new FindEvilClient();
const result = await client.analyze(
  "Malware detected",
  "Extract IOCs"
);
```

## Interactive Documentation

Visit **http://localhost:18000/docs** for interactive Swagger UI.

## OpenAPI Specification

Download full spec: **http://localhost:18000/openapi.json**

## Next Steps

- [Python API](python.md) - Programmatic Python usage
- [CLI Reference](cli.md) - Command-line interface
- [Usage Guide](../usage.md) - Common workflows
