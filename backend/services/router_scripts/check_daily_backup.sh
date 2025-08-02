#!/bin/sh
# Check if daily backup daemon is running
# Returns exit code 0 if running, 1 if not running
# Minimal output for easy parsing by Python backend

# Configuration - must match daily_save_and_clean.sh
BACKUP_DIR="/tmp/nlbwmon/daily"
PID_FILE="$BACKUP_DIR/daily_backup.pid"

# Function to check if daemon is running (same logic as main script)
is_daemon_running() {
    if [ -f "$PID_FILE" ]; then
        local PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            return 0  # Daemon is running
        else
            # PID file exists but process is dead, clean it up
            rm -f "$PID_FILE"
            return 1  # Daemon is not running
        fi
    else
        return 1  # No PID file, daemon is not running
    fi
}

# Check daemon status and return appropriate exit code
if is_daemon_running; then
    echo "RUNNING"
    exit 0
else
    echo "STOPPED"
    exit 1
fi
