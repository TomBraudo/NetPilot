#!/bin/bash

# NetPilot Cloud Port Manager Deployment Test Script
# Run this on the cloud VM to test and diagnose the deployment

# Configuration
SERVICE_PORT="8080"
TARGET_DIR="/opt/netpilot-port-manager"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "===== NetPilot Cloud Port Manager Deployment Test ====="

# Check if we're on the cloud VM
log_info "Checking system information..."
echo "Hostname: $(hostname)"
echo "User: $(whoami)"
echo "Working directory: $(pwd)"
echo "Node.js version: $(node --version 2>/dev/null || echo 'Not installed')"
echo "NPM version: $(npm --version 2>/dev/null || echo 'Not installed')"
echo "PM2 version: $(pm2 --version 2>/dev/null || echo 'Not installed')"

# Check if service directory exists
log_info "Checking service directory..."
if [ -d "$TARGET_DIR" ]; then
    log_success "Service directory exists: $TARGET_DIR"
    echo "Directory contents:"
    ls -la $TARGET_DIR
else
    log_error "Service directory not found: $TARGET_DIR"
    exit 1
fi

# Check if data directory exists
log_info "Checking data directory..."
if [ -d "$TARGET_DIR/data" ]; then
    log_success "Data directory exists"
    echo "Data directory permissions:"
    ls -la $TARGET_DIR/data
else
    log_warning "Data directory not found, creating it..."
    mkdir -p $TARGET_DIR/data
    chmod 755 $TARGET_DIR/data
fi

# Check PM2 status
log_info "Checking PM2 status..."
pm2 status

# Check if service is running
log_info "Checking if service is listening on port $SERVICE_PORT..."
if netstat -tuln | grep -q ":$SERVICE_PORT "; then
    log_success "Service is listening on port $SERVICE_PORT"
else
    log_warning "Service not listening on port $SERVICE_PORT"
fi

# Test health endpoint
log_info "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" http://localhost:$SERVICE_PORT/api/health)
HTTP_CODE="${HEALTH_RESPONSE: -3}"
RESPONSE_BODY="${HEALTH_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ]; then
    log_success "Health check passed!"
    echo "Response: $RESPONSE_BODY"
else
    log_error "Health check failed. HTTP Code: $HTTP_CODE"
    if [ -n "$RESPONSE_BODY" ]; then
        echo "Response: $RESPONSE_BODY"
    fi
fi

# Check PM2 logs
log_info "Recent PM2 logs:"
pm2 logs netpilot-port-manager --lines 10 --nostream

# Check firewall status
log_info "Checking firewall status..."
sudo ufw status

# Test external connectivity
log_info "Testing external connectivity..."
EXTERNAL_IP=$(curl -s ifconfig.me)
echo "External IP: $EXTERNAL_IP"

if [ -n "$EXTERNAL_IP" ]; then
    log_info "Testing external access to health endpoint..."
    curl -s -w "%{http_code}" http://$EXTERNAL_IP:$SERVICE_PORT/api/health | tail -c 3
fi

log_info "Deployment test completed." 