#!/bin/bash

# Port forwarding script
# Forwards ports from localhost to 34.38.207.87

TARGET_IP="34.38.207.87"
TARGET_USER="netpilot-agent"
TARGET_PASSWORD="agent"

echo "Starting port forwarding to $TARGET_IP..."

# Function to handle cleanup on script exit
cleanup() {
    echo "Cleaning up port forwarding rules..."
    # Kill all ssh port forwarding processes started by this script
    pkill -f "ssh.*$TARGET_USER@$TARGET_IP.*-L"
    echo "Port forwarding stopped."
    exit 0
}

# Set up signal handlers for cleanup
trap cleanup SIGINT SIGTERM

# Check if sshpass is installed for password authentication
if ! command -v sshpass &> /dev/null; then
    echo "Error: sshpass is required for password authentication"
    echo "Install it with: sudo apt-get install sshpass (Ubuntu/Debian) or sudo yum install sshpass (CentOS/RHEL)"
    exit 1
fi

# Forward port 8080 to 8080
echo "Forwarding localhost:8080 -> $TARGET_IP:8080"
sshpass -p "$TARGET_PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -N -L 8080:localhost:8080 $TARGET_USER@$TARGET_IP &
sleep 1

# Forward port range 2200-2299 to 2200-2299 (with connection limiting)
echo "Forwarding localhost:2200-2299 -> $TARGET_IP:2200-2299"
echo "Note: Creating connections in batches to avoid overwhelming SSH server..."

connection_count=0
max_concurrent=10  # Limit concurrent connections

for port in {2200..2299}; do
    # Wait if we've hit the concurrent connection limit
    if (( connection_count >= max_concurrent )); then
        echo "Waiting for connections to stabilize..."
        sleep 2
        connection_count=0
    fi
    
    echo "Creating tunnel for port $port..."
    sshpass -p "$TARGET_PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -N -L $port:localhost:$port $TARGET_USER@$TARGET_IP &
    
    # Check if the SSH command failed
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to create tunnel for port $port"
    fi
    
    ((connection_count++))
    sleep 0.1  # Small delay between connections
done

echo "Port forwarding established. Press Ctrl+C to stop."
echo "Active forwards:"
echo "  localhost:8080 -> $TARGET_IP:8080"
echo "  localhost:2200-2299 -> $TARGET_IP:2200-2299"

# Wait for user to stop the script
wait
