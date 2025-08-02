#!/bin/sh
# Stop daily backup daemon
# Returns exit code 0 if successfully stopped or not running
# Returns exit code 1 only if stop operation failed

# Configuration - must match daily_save_and_clean.sh
BACKUP_DIR="/tmp/nlbwmon/daily"
PID_FILE="$BACKUP_DIR/daily_backup.pid"
LOG_FILE="$BACKUP_DIR/daily_backup.log"

# Function to log with timestamp (same as main script)
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

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

# Stop the daemon
if is_daemon_running; then
    PID=$(cat "$PID_FILE")
    echo "Stopping daily backup daemon (PID: $PID)..."
    log "Daemon stop requested via stop script"
    
    # Send TERM signal for graceful shutdown
    kill "$PID" 2>/dev/null
    sleep 2
    
    # Check if it stopped gracefully
    if is_daemon_running; then
        echo "Daemon didn't stop gracefully, force killing..."
        kill -9 "$PID" 2>/dev/null
        rm -f "$PID_FILE"
        
        # Final check
        if is_daemon_running; then
            echo "ERROR: Failed to stop daemon"
            log "ERROR: Failed to stop daemon (PID: $PID)"
            exit 1
        fi
    fi
    
    echo "Daily backup daemon stopped successfully"
    log "Daemon stopped successfully via stop script"
    exit 0
else
    echo "Daily backup daemon is not running"
    exit 0  # Not running is success for stop operation
fi
