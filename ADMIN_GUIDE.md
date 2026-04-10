# 🛡️ Find Evil Agent - Administrator Guide

**Version:** 0.1.0  
**Last Updated:** April 10, 2026

## Table of Contents

1. [Deployment](#deployment)
2. [SIFT VM Setup](#sift-vm-setup)
3. [LLM Provider Configuration](#llm-provider-configuration)
4. [Security Hardening](#security-hardening)
5. [Monitoring & Observability](#monitoring--observability)
6. [Performance Tuning](#performance-tuning)
7. [Backup & Recovery](#backup--recovery)
8. [Troubleshooting](#troubleshooting)

---

## Deployment

### System Requirements

**Find Evil Agent Host:**
- **OS:** Linux (Ubuntu 22.04+ recommended), macOS 12+, Windows 10+
- **CPU:** 2+ cores (4+ recommended)
- **RAM:** 4GB minimum (8GB recommended)
- **Disk:** 5GB for application + dependencies
- **Network:** SSH access to SIFT VM, HTTPS access to LLM provider

**SIFT Workstation VM:**
- **OS:** Ubuntu 24.04 LTS (SIFT distribution)
- **CPU:** 4+ cores
- **RAM:** 8GB minimum (16GB+ for memory analysis)
- **Disk:** 50GB+ (100GB+ for large evidence files)
- **Network:** SSH port accessible from Find Evil Agent host

### Deployment Options

#### Option 1: Local Development

```bash
# Install on development machine
git clone https://github.com/iffystrayer/find-evil-agent.git
cd find-evil-agent

# Setup environment
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with local settings

# Verify
find-evil config
pytest -v -m "not integration"  # Unit tests only
```

#### Option 2: Production Server

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash findevil
sudo su - findevil

# Install application
git clone https://github.com/iffystrayer/find-evil-agent.git /opt/findevil
cd /opt/findevil

# Production environment
uv venv
source .venv/bin/activate
uv pip install -e .  # No dev dependencies

# Configure
cp .env.example .env.production
# Edit .env.production with production settings

# Create systemd service (see below)
```

#### Option 3: Docker Container

**Dockerfile:**
```dockerfile
FROM python:3.13-slim

# Install uv
RUN pip install uv

# Create app user
RUN useradd -m -s /bin/bash findevil
WORKDIR /app

# Copy application
COPY --chown=findevil:findevil . /app

# Install dependencies
USER findevil
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install -e .

# Expose MCP port (if needed)
EXPOSE 16790

# Run CLI
ENTRYPOINT [".venv/bin/find-evil"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  findevil:
    build: .
    container_name: find-evil-agent
    volumes:
      - ./reports:/app/reports
      - ~/.ssh/sift_vm_key:/app/.ssh/sift_vm_key:ro
    env_file:
      - .env.production
    networks:
      - findevil_net
    restart: unless-stopped

networks:
  findevil_net:
    driver: bridge
```

**Build and run:**
```bash
docker-compose build
docker-compose run findevil analyze "incident" "goal" -o /app/reports/report.md
```

### Environment Configuration

**Production .env template:**
```bash
# LLM Provider
LLM_PROVIDER=openai  # or anthropic, ollama
LLM_MODEL_NAME=gpt-4-turbo
OPENAI_API_KEY=sk-proj-...

# SIFT VM
SIFT_VM_HOST=192.168.1.100
SIFT_VM_PORT=22
SIFT_SSH_USER=findevil-agent
SIFT_SSH_KEY_PATH=/opt/findevil/.ssh/sift_vm_key

# Security
TOOL_SELECTION_CONFIDENCE_THRESHOLD=0.7
TOOL_EXECUTION_TIMEOUT=300
ALLOWED_TOOLS=strings,grep,volatility,log2timeline  # Whitelist

# Observability
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://langfuse.company.internal

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json  # json or console
PROMETHEUS_PORT=19090  # Metrics endpoint
```

### Systemd Service (Linux)

**/etc/systemd/system/findevil.service:**
```ini
[Unit]
Description=Find Evil Agent
After=network.target

[Service]
Type=simple
User=findevil
Group=findevil
WorkingDirectory=/opt/findevil
EnvironmentFile=/opt/findevil/.env.production
ExecStart=/opt/findevil/.venv/bin/find-evil analyze "${INCIDENT}" "${GOAL}" -o /var/log/findevil/report.md
Restart=on-failure
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/findevil

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable findevil
sudo systemctl start findevil
sudo systemctl status findevil
```

---

## SIFT VM Setup

### Initial Setup

**1. Download SIFT VM:**
```bash
# Download OVA from SANS
wget https://downloads.digitalcorpora.org/sift/sift-workstation-4.0.ova

# Import to VirtualBox/VMware
VBoxManage import sift-workstation-4.0.ova
```

**2. Network Configuration:**
- **Option A (Bridged):** VM gets IP on local network (recommended for production)
- **Option B (Host-Only):** VM accessible only from host (good for isolated testing)
- **Option C (NAT with port forwarding):** Forward port 22 to host port 12022

**VMware/VirtualBox:**
```bash
# Set to bridged network
VBoxManage modifyvm "SIFT Workstation" --nic1 bridged --bridgeadapter1 en0

# Start VM
VBoxManage startvm "SIFT Workstation" --type headless
```

**3. Find VM IP Address:**
```bash
# Login to VM console
# Username: sansforensics
# Password: forensics (default)

# Get IP address
ip addr show
```

### Create Dedicated User

```bash
# SSH to SIFT VM
ssh sansforensics@192.168.1.100

# Create findevil-agent user
sudo useradd -m -s /bin/bash -G forensics findevil-agent

# Set up SSH key authentication (from Find Evil Agent host)
# On Find Evil Agent host:
ssh-keygen -t ed25519 -f ~/.ssh/sift_vm_key -C "findevil-agent"
ssh-copy-id -i ~/.ssh/sift_vm_key findevil-agent@192.168.1.100

# Test key-based auth
ssh -i ~/.ssh/sift_vm_key findevil-agent@192.168.1.100 whoami
```

### Install Additional Tools

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Volatility 3 (if not present)
sudo apt install -y volatility3

# Install additional forensic tools
sudo apt install -y \
  bulk-extractor \
  sleuthkit \
  autopsy \
  foremost \
  scalpel \
  hashdeep

# Verify installations
volatility3 --version
bulk_extractor --version
fls -V
```

### Configure Tool Permissions

```bash
# Allow findevil-agent to run specific tools without password
sudo visudo

# Add to sudoers:
findevil-agent ALL=(ALL) NOPASSWD: /usr/bin/volatility3
findevil-agent ALL=(ALL) NOPASSWD: /usr/bin/bulk_extractor
findevil-agent ALL=(ALL) NOPASSWD: /usr/bin/fls
findevil-agent ALL=(ALL) NOPASSWD: /usr/bin/strings
```

### Evidence Storage

```bash
# Create evidence directory
sudo mkdir -p /mnt/evidence
sudo chown findevil-agent:forensics /mnt/evidence
sudo chmod 755 /mnt/evidence

# Mount read-only for safety
sudo mount --bind -o ro /path/to/evidence /mnt/evidence

# Or use NFS/SMB for network storage
sudo apt install -y nfs-common
sudo mount -t nfs nfsserver:/evidence /mnt/evidence -o ro
```

### Firewall Configuration

```bash
# Allow SSH from Find Evil Agent host only
sudo ufw allow from 192.168.1.50 to any port 22 proto tcp
sudo ufw enable
sudo ufw status
```

---

## LLM Provider Configuration

### Ollama (Self-Hosted)

**Installation:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull gemma4:31b-cloud

# Run as service
sudo systemctl enable ollama
sudo systemctl start ollama

# Test
curl http://localhost:11434/api/tags
```

**Configuration:**
```bash
# .env
LLM_PROVIDER=ollama
LLM_MODEL_NAME=gemma4:31b-cloud
OLLAMA_BASE_URL=http://192.168.1.50:11434
```

**Resource Requirements:**
- **gemma4:31b:** 64GB RAM, GPU optional but recommended
- **llama3.2:latest:** 8GB RAM, good for testing
- **mistral:7b:** 8GB RAM, fast for production

### OpenAI (Managed)

**API Key Setup:**
```bash
# Create API key at https://platform.openai.com/api-keys
# Set usage limits to prevent overrun

# .env
LLM_PROVIDER=openai
LLM_MODEL_NAME=gpt-4-turbo-2024-04-09
OPENAI_API_KEY=sk-proj-...
OPENAI_ORGANIZATION=org-...  # Optional
```

**Cost Estimates (per analysis):**
- **Tool Selection:** ~1,500 tokens ($0.015 with GPT-4 Turbo)
- **Analysis:** ~2,000 tokens ($0.020 with GPT-4 Turbo)
- **Total per analysis:** ~$0.035
- **Monthly (1000 analyses):** ~$35

### Anthropic (Managed)

**API Key Setup:**
```bash
# Create API key at https://console.anthropic.com/settings/keys

# .env
LLM_PROVIDER=anthropic
LLM_MODEL_NAME=claude-3-opus-20240229
ANTHROPIC_API_KEY=sk-ant-...
```

**Cost Estimates (per analysis):**
- **Tool Selection:** ~1,500 tokens ($0.075 with Opus)
- **Analysis:** ~2,000 tokens ($0.100 with Opus)
- **Total per analysis:** ~$0.175
- **Monthly (1000 analyses):** ~$175

**Budget Optimization:**
- Use Claude 3 Haiku for tool selection: ~$0.01/analysis
- Use Claude 3 Sonnet for analysis: ~$0.03/analysis
- Total: ~$0.04/analysis (88% cost reduction)

---

## Security Hardening

### SSH Key Security

```bash
# Generate strong key
ssh-keygen -t ed25519 -a 100 -f ~/.ssh/sift_vm_key

# Set correct permissions
chmod 600 ~/.ssh/sift_vm_key
chmod 644 ~/.ssh/sift_vm_key.pub

# Use SSH agent for password-protected keys
eval $(ssh-agent)
ssh-add ~/.ssh/sift_vm_key
```

### Command Injection Prevention

**Built-in protections:**
- Blocklist validation (rm -rf, dd, curl, wget)
- No shell=True in subprocess calls
- Arguments passed as list, not string

**Additional hardening:**
```python
# src/find_evil_agent/config/settings.py

# Whitelist allowed tools (reject all others)
ALLOWED_TOOLS = ["strings", "grep", "volatility3", "fls"]

# Maximum execution time
TOOL_EXECUTION_TIMEOUT = 300  # 5 minutes

# Maximum output size (prevent DoS)
MAX_OUTPUT_SIZE = 10 * 1024 * 1024  # 10 MB
```

### Network Security

**Firewall rules (Find Evil Agent host):**
```bash
# Allow outbound to SIFT VM SSH
sudo ufw allow out to 192.168.1.100 port 22 proto tcp

# Allow outbound to LLM provider
sudo ufw allow out to any port 443 proto tcp  # HTTPS

# Deny all other outbound by default
sudo ufw default deny outgoing
sudo ufw enable
```

**Firewall rules (SIFT VM):**
```bash
# Allow inbound SSH from Find Evil Agent host only
sudo ufw allow from 192.168.1.50 to any port 22 proto tcp

# Deny all other inbound
sudo ufw default deny incoming
sudo ufw enable
```

### Secrets Management

**Avoid hardcoding secrets:**
```bash
# Use environment variables
export OPENAI_API_KEY=$(cat /run/secrets/openai_api_key)

# Or use vault (HashiCorp Vault, AWS Secrets Manager)
export OPENAI_API_KEY=$(vault kv get -field=api_key secret/findevil/openai)
```

**Docker secrets:**
```yaml
# docker-compose.yml
services:
  findevil:
    secrets:
      - openai_api_key
      - sift_ssh_key

secrets:
  openai_api_key:
    file: ./secrets/openai_api_key.txt
  sift_ssh_key:
    file: ./secrets/sift_vm_key
```

### Audit Logging

```python
# src/find_evil_agent/telemetry/__init__.py

# Log all tool executions
logger.info(
    "tool_execution",
    tool_name=tool_name,
    command=command,
    user=os.getenv("USER"),
    timestamp=datetime.utcnow().isoformat(),
    session_id=session_id
)
```

**Centralized logging:**
```bash
# Send logs to Elasticsearch/Loki
# Configure in .env
LOKI_URL=http://loki.company.internal:60100
ELASTICSEARCH_URL=http://elasticsearch.company.internal:60200
```

---

## Monitoring & Observability

### Langfuse Dashboard

**Setup:**
```bash
# Self-hosted Langfuse
docker run -d \
  --name langfuse \
  -p 33000:3000 \
  -e DATABASE_URL=postgresql://... \
  langfuse/langfuse:latest

# Or use Langfuse Cloud
# Sign up at https://cloud.langfuse.com
```

**Access:**
```
http://localhost:33000
```

**Key Metrics:**
- Tool selection confidence distribution
- LLM latency (p50, p95, p99)
- Token usage per analysis
- Error rate by tool
- Session durations

### Prometheus Metrics

**Exposed metrics:**
```
# Tool selection
tool_selection_confidence_histogram
tool_selection_duration_seconds
tool_selection_errors_total

# Tool execution
tool_execution_duration_seconds{tool="volatility"}
tool_execution_errors_total{tool="volatility"}

# Analysis
analysis_findings_total{severity="critical"}
analysis_iocs_extracted_total{type="ip"}
```

**Prometheus configuration:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'findevil'
    static_configs:
      - targets: ['localhost:19090']
    scrape_interval: 15s
```

**Access metrics:**
```
http://localhost:19090/metrics
```

### Grafana Dashboards

**Dashboard panels:**
1. **Tool Selection Success Rate** (gauge)
2. **Average Analysis Duration** (graph)
3. **IOCs Extracted (Last 24h)** (counter)
4. **LLM Token Usage** (graph)
5. **Error Rate by Component** (heatmap)
6. **Top 10 Tools Used** (bar chart)

**Import dashboard:**
```bash
# grafana_dashboard.json provided in docs/
# Import via Grafana UI: Dashboards → Import → Upload JSON
```

### Alerting

**Alert rules:**
```yaml
# prometheus_alerts.yml
groups:
  - name: findevil
    rules:
      - alert: HighErrorRate
        expr: rate(tool_execution_errors_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate in Find Evil Agent"
      
      - alert: LowToolSelectionConfidence
        expr: avg(tool_selection_confidence_histogram) < 0.75
        for: 10m
        annotations:
          summary: "Tool selection confidence below threshold"
      
      - alert: LLMAPIDown
        expr: up{job="findevil"} == 0
        for: 1m
        annotations:
          summary: "Find Evil Agent cannot reach LLM API"
```

**Notification channels:**
- Email
- Slack
- PagerDuty
- Telegram

---

## Performance Tuning

### LLM Response Time

**Optimization strategies:**

1. **Use faster models for tool selection:**
   ```bash
   # Fast: llama3.2:latest (~5s)
   # Medium: gemma4:31b-cloud (~30s)
   # Slow: gpt-4 (~60s)
   ```

2. **Reduce prompt size:**
   ```python
   # Limit candidates shown to LLM
   TOP_K_CANDIDATES = 5  # Default: 10
   ```

3. **Cache embeddings:**
   ```bash
   # Embeddings are cached in .cache/embeddings/
   # Persist this directory across deployments
   ```

### SSH Connection Pooling

**Reuse connections:**
```python
# Connection pool (already implemented)
# Maintains 1 persistent connection per session
# Reduces overhead from 0.1s to <0.01s per command
```

### Parallel Tool Execution

**Future enhancement (not yet implemented):**
```python
# Execute multiple tools concurrently
tools = ["strings", "bulk_extractor", "volatility"]
results = await asyncio.gather(*[execute_tool(t) for t in tools])
```

### Database for Results

**Store results for faster retrieval:**
```bash
# PostgreSQL for analysis history
sudo apt install -y postgresql
sudo -u postgres createdb findevil

# Configure in .env
DATABASE_URL=postgresql://findevil:password@localhost/findevil
```

**Schema:**
```sql
CREATE TABLE analyses (
    id UUID PRIMARY KEY,
    incident_description TEXT,
    analysis_goal TEXT,
    tool_selected VARCHAR(100),
    tool_confidence FLOAT,
    findings JSONB,
    iocs JSONB,
    duration_seconds FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tool ON analyses(tool_selected);
CREATE INDEX idx_timestamp ON analyses(created_at);
```

---

## Backup & Recovery

### Critical Data

**Configuration:**
```bash
# Backup .env files
rsync -av .env.production backups/env/$(date +%Y%m%d).env

# Version control for metadata
git add tools/metadata.yaml
git commit -m "Update tool metadata"
```

**Embeddings cache:**
```bash
# Backup cache (regeneration takes ~8s)
tar -czf embeddings_backup.tar.gz .cache/embeddings/
```

**Analysis reports:**
```bash
# Backup reports directory
rsync -av reports/ backups/reports/
```

### Disaster Recovery

**Recovery procedure:**
```bash
# 1. Restore application
git clone https://github.com/iffystrayer/find-evil-agent.git
cd find-evil-agent

# 2. Restore configuration
cp backups/env/20260410.env .env.production

# 3. Restore embeddings cache (optional, speeds up first run)
tar -xzf embeddings_backup.tar.gz

# 4. Reinstall dependencies
uv venv && source .venv/bin/activate
uv pip install -e .

# 5. Test
find-evil config
pytest -v -m "not integration"
```

**SIFT VM recovery:**
```bash
# 1. Restore VM snapshot
VBoxManage snapshot "SIFT Workstation" restore "snapshot-20260410"

# 2. Reconfigure SSH keys
ssh-copy-id -i ~/.ssh/sift_vm_key findevil-agent@192.168.1.100

# 3. Test connection
ssh -i ~/.ssh/sift_vm_key findevil-agent@192.168.1.100 hostname
```

---

## Troubleshooting

### High Memory Usage

**Symptoms:**
- OOM errors
- System slowdown
- Swap usage increasing

**Diagnosis:**
```bash
# Check memory usage
htop

# Profile Python process
py-spy top --pid $(pgrep -f find-evil)
```

**Solutions:**
- Use smaller LLM models (llama3.2 instead of gemma4:31b)
- Limit tool output size: `MAX_OUTPUT_SIZE=5000000`
- Increase system RAM
- Run Ollama on separate host

### Slow Analysis Times

**Diagnosis:**
```bash
# Enable verbose logging
find-evil analyze ... -v

# Check component timings:
# - Tool selection: Should be <60s
# - Tool execution: Varies by tool
# - Analysis: Should be <30s
```

**Solutions:**
- **Slow LLM:** Use faster model or increase Ollama resources
- **Slow SSH:** Check network latency (`ping 192.168.1.100`)
- **Slow tool execution:** Check SIFT VM resources (`ssh siftvm top`)

### Permission Errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/mnt/evidence/disk.raw'
```

**Solutions:**
```bash
# Check file permissions on SIFT VM
ssh siftvm ls -la /mnt/evidence/disk.raw

# Fix ownership
ssh siftvm sudo chown findevil-agent:forensics /mnt/evidence/disk.raw

# Fix permissions
ssh siftvm sudo chmod 644 /mnt/evidence/disk.raw
```

### LLM API Rate Limits

**Symptoms:**
```
Error: Rate limit exceeded (429)
```

**Solutions:**
- **OpenAI:** Increase tier (check platform.openai.com/settings)
- **Anthropic:** Contact support for limit increase
- **Ollama:** No rate limits, but check resource usage
- Implement retry with exponential backoff (already built-in via tenacity)

---

## Appendix

### Port Allocation

| Port | Service | Protocol |
|------|---------|----------|
| 22 | SIFT VM SSH | TCP |
| 11434 | Ollama | HTTP |
| 16790 | MCP Server (future) | HTTP |
| 19090 | Prometheus Metrics | HTTP |
| 33000 | Langfuse | HTTP |
| 60090 | Prometheus (global) | HTTP |
| 60001 | Grafana (global) | HTTP |

### Useful Commands

```bash
# Check service status
systemctl status findevil

# View logs
journalctl -u findevil -f

# Test SSH connection
ssh -i ~/.ssh/sift_vm_key findevil-agent@192.168.1.100 whoami

# Test LLM provider
curl http://localhost:11434/api/tags  # Ollama
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"

# View metrics
curl http://localhost:19090/metrics

# Check embeddings cache
ls -lh .cache/embeddings/

# Regenerate embeddings
rm -rf .cache/embeddings/ && find-evil analyze "test" "test"
```

---

**Last Updated:** April 10, 2026  
**Version:** 0.1.0
