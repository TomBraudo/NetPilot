#!/bin/sh
# Daily nlbwmon data backup and cleanup script
# This script runs FOREVER in the background, waking up daily at 23:55
# to commit, save, and clean up nlbwmon data files.

# Configuration
BACKUP_DIR="/tmp/nlbwmon/daily"
MAX_FILES=35  # Keep 35 days of daily backups
LOG_FILE="$BACKUP_DIR/daily_backup.log"
PID_FILE="$BACKUP_DIR/daily_backup.pid"

# Create directories if they don't exist
mkdir -p "$BACKUP_DIR"

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to perform daily backup
perform_daily_backup() {
    local DATE=$(date +%Y-%m-%d)
    local DAILY_FILE="$BACKUP_DIR/daily_$DATE.json"
    
    log "Starting daily backup for $DATE"
    
    # Step 1: Commit current nlbwmon data to ensure it's saved
    if nlbw -c commit >/dev/null 2>&1; then
        log "Successfully committed nlbwmon data"
    else
        log "WARNING: Failed to commit nlbwmon data"
    fi
    
    # Step 2: Get current raw JSON data
    if nlbw -c json > "$DAILY_FILE" 2>/dev/null; then
        log "Successfully saved daily data to $DAILY_FILE"
        
        # Check file size for validation
        local FILE_SIZE=$(wc -c < "$DAILY_FILE" 2>/dev/null || echo "0")
        log "Daily file size: $FILE_SIZE bytes"
        
        # Basic validation - file should be at least 50 bytes (minimal JSON structure)
        if [ "$FILE_SIZE" -lt 50 ]; then
            log "WARNING: Daily file seems too small, possible data issue"
        fi
    else
        log "ERROR: Failed to save daily data to $DAILY_FILE"
        return 1
    fi
    
    # Step 3: Clean up old files (keep only MAX_FILES)
    cleanup_old_files
    
    log "Daily backup completed successfully"
    return 0
}

# Function to clean up old daily backup files
cleanup_old_files() {
    log "Starting cleanup of old daily files"
    
    # Count current daily files
    local FILE_COUNT=$(ls -1 "$BACKUP_DIR"/daily_*.json 2>/dev/null | wc -l)
    log "Found $FILE_COUNT daily backup files"
    
    # If we have more than MAX_FILES, remove the oldest ones
    if [ "$FILE_COUNT" -gt "$MAX_FILES" ]; then
        local FILES_TO_DELETE=$((FILE_COUNT - MAX_FILES))
        log "Need to delete $FILES_TO_DELETE old files"
        
        # List files by date (oldest first) and delete the excess
        ls -1t "$BACKUP_DIR"/daily_*.json 2>/dev/null | tail -n "$FILES_TO_DELETE" | while read -r OLD_FILE; do
            if rm -f "$OLD_FILE" 2>/dev/null; then
                log "Deleted old file: $(basename "$OLD_FILE")"
            else
                log "ERROR: Failed to delete old file: $(basename "$OLD_FILE")"
            fi
        done
    else
        log "No cleanup needed, file count ($FILE_COUNT) within limit ($MAX_FILES)"
    fi
}

# Function to calculate seconds until next 23:55
calculate_sleep_seconds() {
    local NOW=$(date +%s)
    local TODAY_2355=$(date -d "today 23:55" +%s 2>/dev/null || date -d "$(date +%Y-%m-%d) 23:55:00" +%s)
    
    # If 23:55 has already passed today, calculate for tomorrow
    if [ "$NOW" -ge "$TODAY_2355" ]; then
        local TOMORROW_2355=$(date -d "tomorrow 23:55" +%s 2>/dev/null || date -d "$(date -d "+1 day" +%Y-%m-%d) 23:55:00" +%s)
        echo $((TOMORROW_2355 - NOW))
    else
        echo $((TODAY_2355 - NOW))
    fi
}

# Function to handle script termination
cleanup_and_exit() {
    log "Received termination signal, shutting down gracefully"
    rm -f "$PID_FILE"
    exit 0
}

# Main daemon loop
main_daemon() {
    # Write PID file
    echo $$ > "$PID_FILE"
    
    # Set up signal handlers for graceful shutdown
    trap cleanup_and_exit TERM INT QUIT
    
    log "Daily backup daemon started (PID: $$)"
    log "Configuration: BACKUP_DIR=$BACKUP_DIR, MAX_FILES=$MAX_FILES"
    
    # Main loop - runs forever
    while true; do
        # Calculate how long to sleep until next 23:55
        local SLEEP_SECONDS=$(calculate_sleep_seconds)
        local NEXT_RUN=$(date -d "+$SLEEP_SECONDS seconds" '+%Y-%m-%d %H:%M:%S')
        
        log "Next backup scheduled for: $NEXT_RUN (sleeping $SLEEP_SECONDS seconds)"
        
        # Sleep until next backup time
        sleep "$SLEEP_SECONDS"
        
        # Perform the daily backup
        perform_daily_backup
        
        # After backup, sleep for 70 seconds to avoid running twice in the same minute
        # This handles edge cases with daylight saving time or leap seconds
        sleep 70
    done
}

# Function to check if daemon is already running
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

# Command line interface
case "${1:-start}" in
    start)
        if is_daemon_running; then
            echo "Daily backup daemon is already running (PID: $(cat "$PID_FILE"))"
            exit 1
        else
            echo "Starting daily backup daemon..."
            # Run in background and detach from terminal completely
            # setsid creates new session, nohup ignores hangup signals
            nohup setsid "$0" daemon </dev/null >/dev/null 2>&1 &
            echo "Daily backup daemon started successfully"
            log "Daemon started via '$0 start' command"
        fi
        ;;
    
    daemon)
        # This is the actual daemon process
        main_daemon
        ;;
    
    stop)
        if is_daemon_running; then
            local PID=$(cat "$PID_FILE")
            echo "Stopping daily backup daemon (PID: $PID)..."
            kill "$PID" 2>/dev/null
            sleep 2
            if is_daemon_running; then
                echo "Daemon didn't stop gracefully, force killing..."
                kill -9 "$PID" 2>/dev/null
                rm -f "$PID_FILE"
            fi
            echo "Daily backup daemon stopped"
            log "Daemon stopped via '$0 stop' command"
        else
            echo "Daily backup daemon is not running"
        fi
        ;;
    
    status)
        if is_daemon_running; then
            local PID=$(cat "$PID_FILE")
            echo "Daily backup daemon is running (PID: $PID)"
            echo "Log file: $LOG_FILE"
            echo "Backup directory: $BACKUP_DIR"
            
            # Show recent log entries
            if [ -f "$LOG_FILE" ]; then
                echo ""
                echo "Recent log entries:"
                tail -n 5 "$LOG_FILE"
            fi
        else
            echo "Daily backup daemon is not running"
        fi
        ;;
    
    test)
        echo "Running test backup..."
        log "Test backup initiated manually"
        if perform_daily_backup; then
            echo "Test backup completed successfully"
        else
            echo "Test backup failed - check log file: $LOG_FILE"
            exit 1
        fi
        ;;
    
    *)
        echo "Usage: $0 {start|stop|status|test}"
        echo ""
        echo "Commands:"
        echo "  start  - Start the daily backup daemon"
        echo "  stop   - Stop the daily backup daemon"
        echo "  status - Show daemon status and recent logs"
        echo "  test   - Run a test backup immediately"
        echo ""
        echo "The daemon will run forever and perform daily backups at 23:55"
        echo "It will keep the last $MAX_FILES daily backup files"
        exit 1
        ;;
esac
