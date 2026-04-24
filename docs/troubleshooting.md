# Troubleshooting Guide

Solutions to common issues with Find Evil Agent.

## Connection Issues

### Cannot Connect to SIFT VM

**Symptoms:**
```
Error: SSH connection failed to 192.168.12.101:22
```

**Solutions:**

1. **Verify SIFT VM is running:**
   ```bash
   ping 192.168.12.101
   ```

2. **Test SSH manually:**
   ```bash
   ssh -i ~/.ssh/sift_vm sansforensics@192.168.12.101
   ```

3. **Check SSH key permissions:**
   ```bash
   chmod 600 ~/.ssh/sift_vm
   ```

4. **Verify firewall settings:**
   ```bash
   # On SIFT VM
   sudo ufw status
   sudo ufw allow 22/tcp
   ```

### Ollama Connection Failed

**Symptoms:**
```
Error: Could not connect to Ollama at http://192.168.12.124:11434
```

**Solutions:**

1. **Verify Ollama is running:**
   ```bash
   curl http://192.168.12.124:11434/api/tags
   ```

2. **Check Ollama logs:**
   ```bash
   # On host machine
   ollama list
   journalctl -u ollama -f
   ```

3. **Test with different model:**
   ```bash
   find-evil analyze "test" "test" --provider ollama --model llama3:8b
   ```

## LLM Provider Issues

### OpenAI API Key Invalid

**Symptoms:**
```
Error: Invalid API key provided
```

**Solutions:**

1. **Verify API key:**
   ```bash
   echo $OPENAI_API_KEY
   ```

2. **Check key format:**
   ```bash
   # Should start with sk-
   echo $OPENAI_API_KEY | grep "^sk-"
   ```

3. **Test API key:**
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

### Anthropic Rate Limit

**Symptoms:**
```
Error: Rate limit exceeded for Claude API
```

**Solutions:**

1. **Add retry delay:**
   ```bash
   export ANTHROPIC_RETRY_DELAY=5
   ```

2. **Use lower tier model:**
   ```bash
   find-evil analyze "..." "..." --model claude-3-haiku-20240307
   ```

3. **Check usage limits:**
   ```bash
   curl https://api.anthropic.com/v1/usage \
     -H "x-api-key: $ANTHROPIC_API_KEY"
   ```

## Tool Execution Issues

### Tool Not Found on SIFT VM

**Symptoms:**
```
Error: Command 'volatility' not found on SIFT VM
```

**Solutions:**

1. **Check tool availability:**
   ```bash
   ssh sansforensics@192.168.12.101 "which volatility"
   ```

2. **Install missing tool:**
   ```bash
   # On SIFT VM
   sudo apt-get update
   sudo apt-get install volatility
   ```

3. **Use alternative tool:**
   ```bash
   find-evil analyze "..." "..." --tool strings
   ```

### Command Timeout

**Symptoms:**
```
Error: Command execution timed out after 60s
```

**Solutions:**

1. **Increase timeout:**
   ```bash
   export SIFT_COMMAND_TIMEOUT=300
   find-evil analyze "..." "..." --timeout 300
   ```

2. **Check SIFT VM resources:**
   ```bash
   ssh sansforensics@192.168.12.101 "top -bn1"
   ```

## Analysis Issues

### Low Confidence Scores

**Symptoms:**
```
Warning: Tool selection confidence 0.65 below threshold 0.7
```

**Solutions:**

1. **Improve incident description:**
   ```bash
   # ❌ Poor
   find-evil analyze "something wrong" "check it"
   
   # ✅ Good
   find-evil analyze \
     "Suspicious outbound connection from svchost.exe to 185.220.101.42:443" \
     "Identify malicious process and C2 communication patterns"
   ```

2. **Lower confidence threshold:**
   ```bash
   find-evil analyze "..." "..." --confidence 0.6
   ```

3. **Use more specific tool:**
   ```bash
   # Manually specify tool if known
   find-evil execute netstat
   ```

### No IOCs Extracted

**Symptoms:**
```
Analysis complete: 0 IOCs found
```

**Solutions:**

1. **Check tool output:**
   ```bash
   # Run with verbose to see raw output
   find-evil analyze "..." "..." --verbose
   ```

2. **Verify incident has IOCs:**
   ```bash
   # Test with known IOC-rich incident
   find-evil analyze \
     "Network traffic to 185.220.101.42" \
     "Extract IP addresses and domains"
   ```

3. **Use different analysis goal:**
   ```bash
   # Be explicit about what to extract
   find-evil analyze "..." "Extract all IP addresses, domains, and file paths"
   ```

## Web UI Issues

### React UI Not Loading

**Symptoms:**
- Blank page at http://localhost:15173
- Loading spinner forever

**Solutions:**

1. **Check Docker containers:**
   ```bash
   docker-compose ps
   docker-compose logs frontend
   ```

2. **Rebuild frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

3. **Clear browser cache:**
   ```
   Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)
   ```

### API Endpoint Not Responding

**Symptoms:**
```
Failed to fetch: http://localhost:18000/api/v1/analyze
```

**Solutions:**

1. **Verify backend is running:**
   ```bash
   curl http://localhost:18000/api/v1/health
   ```

2. **Check CORS settings:**
   ```bash
   # In docker-compose.yml
   environment:
     - CORS_ORIGINS=http://localhost:15173
   ```

3. **Restart services:**
   ```bash
   docker-compose restart backend
   ```

## Performance Issues

### Slow Analysis

**Symptoms:**
- Analysis takes >5 minutes
- High CPU/memory usage

**Solutions:**

1. **Use faster LLM model:**
   ```bash
   find-evil analyze "..." "..." --model llama3:8b
   ```

2. **Reduce max iterations:**
   ```bash
   find-evil investigate "..." "..." --max-iterations 3
   ```

3. **Enable SSH connection pooling:**
   ```bash
   export SIFT_SSH_POOL_SIZE=5
   ```

### Memory Issues

**Symptoms:**
```
Error: Out of memory
```

**Solutions:**

1. **Limit model size:**
   ```bash
   # Use smaller model
   export OLLAMA_MODEL=llama3:8b
   ```

2. **Increase Docker memory:**
   ```bash
   # In Docker Desktop settings
   Resources → Memory → 8GB
   ```

## Docker Issues

### Container Won't Start

**Symptoms:**
```
Error: Cannot start container
```

**Solutions:**

1. **Check port conflicts:**
   ```bash
   lsof -i :18000
   lsof -i :15173
   ```

2. **View container logs:**
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   ```

3. **Rebuild containers:**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

## Testing Issues

### Tests Failing

**Symptoms:**
```
FAILED tests/test_something.py - Connection refused
```

**Solutions:**

1. **Skip integration tests:**
   ```bash
   pytest -m "not integration"
   ```

2. **Verify test dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Check test configuration:**
   ```bash
   cat pyproject.toml | grep -A10 "\[tool.pytest"
   ```

## Diagnostic Commands

### System Health Check

```bash
# Full diagnostic
find-evil config
find-evil test-connection

# Check services
docker-compose ps
curl http://localhost:18000/api/v1/health
curl http://192.168.12.124:11434/api/tags

# Test SIFT VM
ssh sansforensics@192.168.12.101 "uname -a"
```

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
find-evil analyze "..." "..." --verbose
```

### Collect Logs

```bash
# Application logs
cat ~/.find-evil/logs/app.log

# Docker logs
docker-compose logs > debug.log

# System logs
journalctl -u ollama > ollama.log
```

## Getting Help

If issues persist:

1. **Check GitHub Issues:** https://github.com/iffystrayer/find-evil-agent/issues
2. **Review Documentation:** All guides at /docs
3. **Enable Debug Mode:** `export LOG_LEVEL=DEBUG`
4. **Collect Diagnostics:** Run diagnostic commands above

## Common Error Messages

### "Command blocked by security policy"

**Cause:** Dangerous command detected (rm -rf, dd, etc.)

**Solution:** This is intentional security feature. Revise incident description to avoid suggesting dangerous operations.

### "No leads found after iteration"

**Cause:** Investigation reached natural conclusion

**Solution:** This is normal. Review results - investigation may be complete.

### "FAISS index not found"

**Cause:** Tool registry embeddings not initialized

**Solution:**
```bash
python -c "from find_evil_agent.tools.registry import ToolRegistry; ToolRegistry()"
```

## Next Steps

- [Configuration Guide](configuration.md) - Verify settings
- [Deployment Guide](deployment/sift-setup.md) - SIFT VM setup
- [Security Guide](deployment/security.md) - Security best practices
