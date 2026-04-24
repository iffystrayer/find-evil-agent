# Configuration Reference

Complete configuration guide for Find Evil Agent.

## Environment Variables

Configuration is managed through environment variables in `.env` file.

### LLM Provider Configuration

#### Ollama (Local)

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://192.168.12.124:11434
OLLAMA_MODEL=llama3:8b
OLLAMA_TIMEOUT=300
```

**Available Models:**
- `llama3:8b` - Fast, good for development
- `llama3:70b` - High quality, slower
- `gemma2:27b` - Balanced performance
- `mistral:7b` - Fast inference

#### OpenAI

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TIMEOUT=120
```

**Recommended Models:**
- `gpt-4-turbo-preview` - Best quality
- `gpt-4` - High quality
- `gpt-3.5-turbo` - Fast and cost-effective

#### Anthropic Claude

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_TIMEOUT=120
```

**Recommended Models:**
- `claude-3-5-sonnet-20241022` - Best balance
- `claude-3-opus-20240229` - Highest quality
- `claude-3-haiku-20240307` - Fastest

### SIFT VM Configuration

```bash
SIFT_VM_HOST=192.168.12.101
SIFT_VM_PORT=22
SIFT_SSH_USER=sansforensics
SIFT_SSH_KEY_PATH=~/.ssh/sift_vm
SIFT_CONNECTION_TIMEOUT=10
SIFT_COMMAND_TIMEOUT=60
```

**Options:**
- `SIFT_VM_HOST` - SIFT VM IP address or hostname
- `SIFT_VM_PORT` - SSH port (default: 22)
- `SIFT_SSH_USER` - SSH username (default: sansforensics)
- `SIFT_SSH_KEY_PATH` - Path to SSH private key
- `SIFT_CONNECTION_TIMEOUT` - Connection timeout in seconds
- `SIFT_COMMAND_TIMEOUT` - Command execution timeout

### Observability Configuration

#### Langfuse (Optional)

```bash
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

#### Prometheus (Optional)

```bash
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=60090
```

### Application Settings

```bash
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Tool Selection
MIN_CONFIDENCE_THRESHOLD=0.7
MAX_TOOL_CANDIDATES=10

# Investigation
MAX_ITERATIONS=10
DEFAULT_ITERATIONS=3

# Report Generation
REPORT_TEMPLATE_DIR=./templates
REPORT_OUTPUT_DIR=./reports
```

## Configuration Files

### .env.example

Template with all available options:

```bash
# Copy and customize
cp .env.example .env
```

### pyproject.toml

Project dependencies and metadata. Don't modify unless adding dependencies.

### mkdocs.yml

Documentation configuration. Customize for deployment.

## Advanced Configuration

### Custom Tool Registry

Add custom SIFT tools to the registry:

```python
# config/custom_tools.py
from find_evil_agent.tools.registry import ToolRegistry

registry = ToolRegistry()
registry.register_tool(
    name="custom_tool",
    description="My custom forensic tool",
    command_template="custom_tool {args}",
    category="custom"
)
```

### LLM Prompt Templates

Customize prompts for tool selection and analysis:

```python
# config/prompts.py
TOOL_SELECTION_PROMPT = """
Given the incident: {incident}
Goal: {goal}

Select the best SIFT tool from: {tools}
...
"""
```

### SSH Connection Pooling

Enable connection reuse for better performance:

```bash
SIFT_SSH_POOL_SIZE=5
SIFT_SSH_POOL_TIMEOUT=300
```

## Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    environment:
      - LLM_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
      - SIFT_VM_HOST=192.168.12.101
    ports:
      - "18000:18000"
  
  frontend:
    ports:
      - "15173:15173"
```

### Environment in Containers

Pass environment variables to containers:

```bash
docker-compose --env-file .env up -d
```

## Security Best Practices

1. **Never commit .env** - Already in .gitignore
2. **Use SSH keys** - No password authentication
3. **Rotate API keys** - Regularly update LLM provider keys
4. **Limit SIFT access** - Read-only SSH user preferred
5. **Enable observability** - Monitor for suspicious activity

## Validation

Test your configuration:

```bash
# Check all settings
find-evil config

# Test SIFT connection
find-evil test-connection

# Verify LLM provider
find-evil analyze "test" "test" --verbose
```

## Troubleshooting

**Connection Issues:**
```bash
# Test SSH manually
ssh -i ~/.ssh/sift_vm sansforensics@192.168.12.101

# Test Ollama
curl http://192.168.12.124:11434/api/tags
```

**LLM Provider Issues:**
```bash
# Verify API key
echo $OPENAI_API_KEY | cut -c1-10

# Test with simple prompt
find-evil analyze "test" "test" --provider openai --verbose
```

## Next Steps

- [Deployment Guide](deployment/sift-setup.md) - Set up SIFT VM
- [LLM Configuration](deployment/llm-config.md) - Configure LLM providers
- [Security Guide](deployment/security.md) - Security best practices
