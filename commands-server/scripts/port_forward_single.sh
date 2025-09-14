#!/bin/bash

# Port forwarding script using a single SSH connection
# More efficient and less likely to overwhelm the SSH server

TARGET_IP="34.38.207.87"
TARGET_USER="netpilot-agent"
TARGET_PASSWORD="agent"

echo "Starting port forwarding to $TARGET_IP using single SSH connection..."

# Check if sshpass is installed for password authentication
if ! command -v sshpass &> /dev/null; then
    echo "Error: sshpass is required for password authentication"
    echo "Install it with: sudo apt-get install sshpass (Ubuntu/Debian) or sudo yum install sshpass (CentOS/RHEL)"
    exit 1
fi

# Build the SSH command with multiple -L options
SSH_CMD="sshpass -p $TARGET_PASSWORD ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -N"

# Add port 8080
SSH_CMD="$SSH_CMD -L 8080:localhost:8080"

# Add port range 2200-2299
for port in {2200..2299}; do
    SSH_CMD="$SSH_CMD -L $port:localhost:$port"
done

# Add the target
SSH_CMD="$SSH_CMD $TARGET_USER@$TARGET_IP"

echo "Forwarding ports:"
echo "  localhost:8080 -> $TARGET_IP:8080"
echo "  localhost:2200-2299 -> $TARGET_IP:2200-2299"
echo ""
echo "Starting single SSH connection with all port forwards..."
echo "Press Ctrl+C to stop."

# Execute the command
exec $SSH_CMD
