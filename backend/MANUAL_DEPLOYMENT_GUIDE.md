# NetPilot Commands Server - Manual Deployment Guide

This guide provides comprehensive instructions for manually deploying the NetPilot Commands Server to the production VM after running the `copy-to-vm.sh` script.

## Prerequisites

- Files have been copied to VM using `scripts/copy-to-vm.sh`

## Quick Deployment Steps

### 1. SSH to the VM

### 2. Navigate to New Deployment
```bash
cd /home/netpilot-agent/netpilot-commands-server-new
```

### 3. Set Up Virtual Environment
```bash
# Create fresh virtual environment (CRITICAL: Don't copy old venv)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify Python version and location
python --version
which python
```

### 4. Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Verify installations
pip list
```

### 5. Test the Server
```bash
# Set test port environment variable
export SERVER_PORT_TEST=5001

# Start server in test mode
python server.py
```

### 6. Verify Health (in another terminal)
```bash
# SSH to VM in another terminal
ssh netpilot-agent@34.38.207.87

# Test health endpoint
curl http://localhost:5001/health

# Expected response: {"status": "healthy", "timestamp": "..."}
```

### 7. Deploy to Production
If testing is successful, deploy to production:

```bash
# Stop the test server (Ctrl+C)

# Stop current production service
sudo systemctl stop netpilot-commands-server

# Replace production deployment
rm -rf /home/netpilot-agent/netpilot-commands-server-production
mv /home/netpilot-agent/netpilot-commands-server-new /home/netpilot-agent/netpilot-commands-server-production

# Update systemd service to use new location
sudo systemctl daemon-reload

# Start production service
sudo systemctl start netpilot-commands-server

# Enable auto-start on boot
sudo systemctl enable netpilot-commands-server

# Check service status
sudo systemctl status netpilot-commands-server
```

### 8. Verify Production Deployment
```bash
# Test production health endpoint
curl http://localhost:5000/health

# Check service logs
sudo journalctl -u netpilot-commands-server -f
```

## Systemd Service Configuration

The systemd service should be configured as follows:

**File: `/etc/systemd/system/netpilot-commands-server.service`**
```ini
[Unit]
Description=NetPilot Commands Server
After=network.target

[Service]
Type=simple
User=netpilot-agent
WorkingDirectory=/home/netpilot-agent/netpilot-commands-server-production
Environment=PATH=/home/netpilot-agent/netpilot-commands-server-production/venv/bin
ExecStart=/home/netpilot-agent/netpilot-commands-server-production/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Virtual Environment Issues
**Problem**: ImportError or module not found errors
**Solution**: 
```bash
# Always create fresh virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Port Manager Connection Issues
**Problem**: Server fails to connect to Port-Manager
**Solution**:
```bash
# Check Port-Manager is running
curl http://localhost:8080/health

# Verify .env configuration
cat .env | grep PORT_MANAGER_URL
# Should show: PORT_MANAGER_URL=http://localhost:8080
```

### Service Start Issues
**Problem**: systemd service fails to start
**Solution**:
```bash
# Check service logs
sudo journalctl -u netpilot-commands-server -n 50

# Verify service file
sudo systemctl cat netpilot-commands-server

# Test manual start
cd /home/netpilot-agent/netpilot-commands-server-production
source venv/bin/activate
python server.py
```

### Firewall Issues
**Problem**: Cannot access server from external hosts
**Solution**:
```bash
# Check UFW status
sudo ufw status

# Allow production port
sudo ufw allow 5000

# Allow test port
sudo ufw allow 5001
```

### File Permission Issues
**Problem**: Permission denied errors
**Solution**:
```bash
# Fix ownership
sudo chown -R netpilot-agent:netpilot-agent /home/netpilot-agent/netpilot-commands-server-*

# Fix permissions
chmod +x server.py
chmod -R 755 /home/netpilot-agent/netpilot-commands-server-production
```

## Environment Variables

The server uses these key environment variables from `.env`:

- `PORT_MANAGER_URL`: http://localhost:8080 (Port-Manager service)
- `SERVER_PORT_TEST`: 5001 (for testing)
- `SERVER_PORT`: 5000 (for production)

## Testing Checklist

Before deploying to production, verify:

- [ ] Virtual environment created successfully
- [ ] All dependencies installed without errors
- [ ] Server starts without crashes
- [ ] Health endpoint returns 200 OK
- [ ] Port-Manager connectivity working
- [ ] No import or module errors in logs

## Rollback Procedure

If deployment fails:

```bash
# Stop failed service
sudo systemctl stop netpilot-commands-server

# Restore previous version
mv /home/netpilot-agent/netpilot-commands-server-production /home/netpilot-agent/netpilot-commands-server-failed
mv /home/netpilot-agent/netpilot-commands-server-old /home/netpilot-agent/netpilot-commands-server-production

# Restart service
sudo systemctl start netpilot-commands-server
```

## Production Monitoring

Monitor the service with:

```bash
# Service status
sudo systemctl status netpilot-commands-server

# Live logs
sudo journalctl -u netpilot-commands-server -f

# Health check
curl http://localhost:5000/health

# Resource usage
htop | grep python
```

## Success Criteria

Deployment is successful when:

1. Service starts without errors
2. Health endpoint returns 200 OK
3. Service is enabled for auto-start
4. No error messages in systemd logs
5. Port-Manager connectivity confirmed
6. Service survives system reboot

---

**Note**: Always create a fresh virtual environment after copying files. Virtual environments are not portable between directories and will cause import errors if reused.
