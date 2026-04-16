# SIFT VM Setup

Guide for setting up SANS SIFT Workstation for use with Find Evil Agent.

## What is SIFT?

SANS Investigative Forensic Toolkit (SIFT) is a free Ubuntu-based distribution containing 100+ digital forensics and incident response tools.

**Official Site:** [https://sans.org/tools/sift-workstation](https://sans.org/tools/sift-workstation)

## Prerequisites

- Virtualization software (VMware, VirtualBox, UTM)
- 4GB+ RAM allocated to VM
- 50GB+ disk space
- Network connectivity to host machine

## Installation Options

### Option 1: Pre-built VM (Recommended)

Download the official SIFT OVA from SANS:

1. Visit [https://digital-forensics.sans.org/community/downloads](https://digital-forensics.sans.org/community/downloads)
2. Download SIFT Workstation OVA
3. Import into VMware/VirtualBox

**Default Credentials:**
- Username: `sansforensics`
- Password: `forensics`

### Option 2: Install on Existing Ubuntu

```bash
# Install SIFT on Ubuntu 20.04/22.04
wget https://github.com/teamdfir/sift-cli/releases/latest/download/sift-cli-linux
chmod +x sift-cli-linux
sudo ./sift-cli-linux install --mode=server
```

## Network Configuration

### Bridged Network (Recommended)

Configure VM to use bridged networking:

1. Open VM settings → Network
2. Select "Bridged Adapter"
3. Choose physical network interface
4. Start VM

Find VM IP address:

```bash
ip addr show
```

Note the IP (e.g., `192.168.12.101`) for Find Evil Agent configuration.

### Host-Only Network (Alternative)

For isolated testing:

1. Create host-only network in virtualization software
2. Configure VM to use host-only adapter
3. Note VM IP address (typically `192.168.56.x`)

## SSH Configuration

### Enable SSH Server

```bash
# Install OpenSSH server
sudo apt update
sudo apt install openssh-server

# Start SSH service
sudo systemctl start ssh
sudo systemctl enable ssh

# Verify SSH is running
sudo systemctl status ssh
```

### Configure SSH Access

**On SIFT VM:**

```bash
# Create .ssh directory
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

**On Host Machine:**

```bash
# Generate SSH key
ssh-keygen -t ed25519 -f ~/.ssh/sift_vm_key -C "find-evil-agent"

# Copy public key to SIFT VM
ssh-copy-id -i ~/.ssh/sift_vm_key sansforensics@192.168.12.101

# Test connection
ssh -i ~/.ssh/sift_vm_key sansforensics@192.168.12.101 hostname
```

### Disable Password Authentication (Optional)

For enhanced security:

```bash
# On SIFT VM
sudo vi /etc/ssh/sshd_config

# Set:
PasswordAuthentication no
PubkeyAuthentication yes

# Restart SSH
sudo systemctl restart ssh
```

## Tool Verification

Verify forensic tools are installed:

```bash
# Memory analysis
which volatility
volatility --version

# Timeline analysis
which log2timeline
log2timeline --version

# Sleuth Kit
which fls
fls -V

# String extraction
which strings
strings --version

# Network analysis
which tcpdump
tcpdump --version
```

## Evidence Storage

Create evidence directory:

```bash
# Create evidence mount point
sudo mkdir -p /mnt/evidence
sudo chown sansforensics:sansforensics /mnt/evidence

# Test write access
touch /mnt/evidence/test.txt
ls -la /mnt/evidence/
```

## Firewall Configuration

Allow SSH access:

```bash
# Ubuntu UFW
sudo ufw allow 22/tcp
sudo ufw enable
sudo ufw status
```

## Performance Tuning

### Increase RAM (if needed)

- Recommended: 8GB+ for memory analysis
- Minimum: 4GB

### Enable Nested Virtualization

For better performance:

**VMware:**
- VM Settings → Processors → Enable "Virtualize Intel VT-x/EPT"

**VirtualBox:**
- VM Settings → System → Acceleration → Enable "VT-x/AMD-V"

## Integration with Find Evil Agent

### Configure .env

```bash
# On host machine
cd find-evil-agent
vi .env
```

Set SIFT VM details:

```bash
SIFT_VM_HOST=192.168.12.101
SIFT_VM_PORT=22
SIFT_SSH_USER=sansforensics
SIFT_SSH_KEY_PATH=/Users/username/.ssh/sift_vm_key
```

### Test Connection

```bash
# From find-evil-agent directory
find-evil config
```

Expected output:

```
✅ SIFT VM: sansforensics@192.168.12.101:22
✅ SSH Key: /Users/username/.ssh/sift_vm_key
```

### Test Tool Execution

```bash
find-evil analyze \
  "Test system information gathering" \
  "List installed forensic tools" \
  -v
```

## Troubleshooting

### Cannot Connect to SIFT VM

```bash
# Verify VM is running
ping 192.168.12.101

# Test SSH manually
ssh -v sansforensics@192.168.12.101

# Check firewall
sudo ufw status
```

### Permission Denied

```bash
# Check SSH key permissions
chmod 600 ~/.ssh/sift_vm_key
chmod 644 ~/.ssh/sift_vm_key.pub

# Verify authorized_keys on SIFT VM
cat ~/.ssh/authorized_keys
```

### Tool Not Found

```bash
# Install missing tools
sudo apt update
sudo apt install <tool-name>

# Or reinstall SIFT
sudo sift-cli install --mode=server
```

## Security Considerations

### Network Isolation

- Use host-only networking for sensitive analysis
- Disable internet access during evidence examination
- Use dedicated VLAN for forensic infrastructure

### Evidence Integrity

- Mount evidence read-only
- Use write blockers for physical media
- Enable audit logging

```bash
# Mount evidence read-only
sudo mount -o ro /dev/sdb1 /mnt/evidence

# Enable audit logging
sudo apt install auditd
sudo systemctl enable auditd
```

### Access Control

- Use strong SSH keys (ed25519, 256-bit)
- Disable password authentication
- Implement fail2ban for brute-force protection

```bash
# Install fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

## Maintenance

### Update SIFT

```bash
# Update SIFT tools
sudo sift-cli update

# Update Ubuntu packages
sudo apt update
sudo apt upgrade
```

### Backup Configuration

```bash
# Backup SIFT VM configuration
sudo tar czf sift-backup.tar.gz \
  /home/sansforensics/.ssh \
  /etc/ssh/sshd_config \
  /mnt/evidence

# Restore if needed
sudo tar xzf sift-backup.tar.gz -C /
```

## Next Steps

- [LLM Configuration](llm-config.md) - Configure LLM providers
- [Security Guide](security.md) - Security best practices
- [Getting Started](../getting-started.md) - Install Find Evil Agent
- [Quick Start](../quick-start.md) - Run first analysis

## Resources

- [SIFT Workstation Documentation](https://digital-forensics.sans.org/community/downloads)
- [SIFT GitHub Repository](https://github.com/teamdfir/sift)
- [SANS DFIR Community](https://digital-forensics.sans.org)
