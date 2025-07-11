# NetPilot Commands Server Deployment Guide

This guide explains how to deploy the NetPilot Commands Server (backend) to your cloud VM using the `deploy.sh` script.

## Overview

The deployment script takes the commands server from your local development environment and deploys it as a production service on your cloud VM. It handles:

- File transfer and environment configuration
- Python virtual environment setup
- Systemd service creation
- Firewall configuration
- Health verification

## Prerequisites

### 1. Local Environment

Ensure you have the following installed on your local machine:

```bash
# Ubuntu/WSL
sudo apt-get install sshpass rsync

# macOS
brew install sshpass rsync
```

### 2. Cloud VM Configuration

Your cloud VM should have:
- Port Manager service running on port 8080
- SSH access enabled
- Python 3 available (will be installed if missing)
- sudo privileges for the deployment user

### 3. Environment Configuration

Create or verify your `agent/.env` file contains the required VM credentials:

```bash
# Cloud VM Configuration
CLOUD_VM_IP=your.vm.ip.address
CLOUD_VM_USER=netpilot-agent
CLOUD_VM_PASSWORD=your_vm_password
CLOUD_VM_PORT=22

# Port Configuration
PORT_RANGE_START=2200
PORT_RANGE_END=2299

# Optional
AUTOSSH_CLEANUP_TOKEN=your_token_here
```

## Deployment Process

### 1. Basic Deployment

To deploy the commands server:

```bash
./deploy.sh
```

This will:
1. Check prerequisites and VM connectivity
2. Prepare backend files for production
3. Transfer files to VM
4. Set up Python environment
5. Create and start systemd service
6. Configure firewall
7. Verify deployment

### 2. Pre-deployment Check

To verify prerequisites without deploying:

```bash
./deploy.sh --check
```

### 3. Service Management

After deployment, manage the service with:

```bash
# Restart service
./deploy.sh --restart

# View logs
./deploy.sh --logs

# Check status
./deploy.sh --status
```

## Production Configuration

The deployment script creates a production environment with:

### Service Details
- **Service Name**: `netpilot-commands-server`
- **Location**: `/opt/netpilot-commands-server`
- **Port**: `5000`
- **Logs**: `/var/log/netpilot/`

### Environment Configuration
```bash
# Production settings (auto-generated)
PORT_MANAGER_URL=http://localhost:8080  # Direct connection
DEVELOPMENT_MODE=false
FLASK_DEBUG=false
SERVER_PORT=5000
LOG_LEVEL=INFO
```

### Systemd Service
The service is configured with:
- Automatic restart on failure
- Security hardening
- Proper logging to systemd journal
- Start on boot

## API Endpoints

Once deployed, the following endpoints are available:

```bash
# Health check
curl http://your-vm-ip:5000/health

# Network operations
curl http://your-vm-ip:5000/api/network/scan

# Session management
curl http://your-vm-ip:5000/api/session/start

# WiFi management
curl http://your-vm-ip:5000/api/wifi/status

# Whitelist/Blacklist operations
curl http://your-vm-ip:5000/api/whitelist/list
curl http://your-vm-ip:5000/api/blacklist/list
```

## Monitoring and Maintenance

### Service Management Commands

```bash
# On the VM, you can manage the service with:
sudo systemctl start netpilot-commands-server
sudo systemctl stop netpilot-commands-server
sudo systemctl restart netpilot-commands-server
sudo systemctl status netpilot-commands-server
sudo systemctl enable netpilot-commands-server  # Auto-start on boot
```

### Log Monitoring

```bash
# Real-time logs
sudo journalctl -u netpilot-commands-server -f

# Recent logs
sudo journalctl -u netpilot-commands-server --since "1 hour ago"

# Application logs
tail -f /var/log/netpilot/commands-server.log
```

### Health Checks

```bash
# Service health
curl http://localhost:5000/health

# Port status
netstat -tuln | grep :5000

# Process status
ps aux | grep python | grep server.py
```

## Troubleshooting

### Common Issues

#### 1. Connection Failed
```bash
# Check VM connectivity
ping your-vm-ip
ssh your-vm-user@your-vm-ip

# Verify credentials in agent/.env
cat agent/.env
```

#### 2. Service Won't Start
```bash
# Check service status
sudo systemctl status netpilot-commands-server

# Check logs
sudo journalctl -u netpilot-commands-server --no-pager -l

# Check Python environment
cd /opt/netpilot-commands-server
source venv/bin/activate
python server.py  # Manual test
```

#### 3. Port Manager Connection Issues
```bash
# Verify port manager is running
curl http://localhost:8080/api/health

# Check port manager status
pm2 status
pm2 logs netpilot-port-manager
```

#### 4. Firewall Issues
```bash
# Check firewall status
sudo ufw status

# Open required ports
sudo ufw allow 5000/tcp
sudo ufw allow 8080/tcp
```

### Re-deployment

To redeploy after making changes:

```bash
# Stop the service
./deploy.sh --restart

# Or full redeployment
./deploy.sh
```

The script is idempotent - it can be run multiple times safely.

## Integration with NetPilot Agent

After successful deployment, update your NetPilot agent configuration to use the deployed commands server:

```javascript
// In your agent configuration
const COMMANDS_SERVER_URL = 'http://your-vm-ip:5000';
```

## Security Considerations

The deployment includes several security measures:
- Service runs as non-root user
- Systemd security hardening enabled
- Protected file system access
- Firewall configuration
- No debug mode in production

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review service logs: `./deploy.sh --logs`
3. Verify VM connectivity: `./deploy.sh --check`
4. Check port manager status on VM

The deployment script provides detailed error messages and logs to help diagnose issues. 