#!/bin/sh
# Daily nlbwmon data backup and cleanup script
# This script runs FOREVER in the background, waking up daily at 23:55
# to commit, save, and clean up nlbwmon data files.

# Configuration
BACKUP_DIR="/tmp/nlbwmon/daily"
MAX_FILES=35  # Keep 35 days of daily backups
LOG_FILE="$BACKUP_DIR/daily_backup.log"
PID_FILE="$BACKUP_DIR/daily_backup.pid"
RESET_FLAG_FILE="$BACKUP_DIR/initial_reset_done"  # Flag to track if initial reset was performed

# Create directories if they don't exist
mkdir -p "$BACKUP_DIR"

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to perform daily backup (23:55)
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

# Function to perform midnight reset (00:00)
perform_midnight_reset() {
    log "Starting midnight reset process"
    
    # Check if this is the first reset or if we should let database_interval handle it
    if [ ! -f "$RESET_FLAG_FILE" ]; then
        # First time - perform service restart to align with our schedule
        log "First midnight reset - performing service restart to align with database_interval"
        if /etc/init.d/nlbwmon restart >/dev/null 2>&1; then
            log "Successfully restarted nlbwmon service - database_interval cycle now aligned"
        else
            log "WARNING: Failed to restart nlbwmon service"
        fi
        
        # Create flag file to indicate initial reset is done
        touch "$RESET_FLAG_FILE"
        log "Initial reset completed - future resets will be handled by database_interval automatically"
    else
        # Not the first time - let database_interval handle the reset automatically
        log "Midnight reached - nlbwmon database_interval should automatically reset tracking"
        log "No manual service restart needed - relying on configured database_interval"
    fi
    
    # Always update database_interval for tomorrow (regardless of restart)
    local TOMORROW=$(date -d '+1 day' +%Y-%m-%d)
    log "Configuring database_interval for tomorrow ($TOMORROW) midnight reset"
    if uci set nlbwmon.@nlbwmon[0].database_interval="$TOMORROW/1" && uci commit nlbwmon >/dev/null 2>&1; then
        log "Successfully configured database_interval to $TOMORROW/1 for next day's automatic reset"
    else
        log "WARNING: Failed to configure database_interval for tomorrow - automatic resets may not work properly"
    fi
    
    log "Midnight reset process completed successfully"
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
    local CURRENT_HOUR=$(date +%H)
    local CURRENT_MIN=$(date +%M)
    
    # Convert current time to minutes since midnight
    local CURRENT_MINUTES=$((CURRENT_HOUR * 60 + CURRENT_MIN))
    local TARGET_MINUTES=$((23 * 60 + 55))  # 23:55 in minutes
    
    # Calculate seconds until target time
    if [ "$CURRENT_MINUTES" -lt "$TARGET_MINUTES" ]; then
        # Target time is today
        local MINUTES_TO_WAIT=$((TARGET_MINUTES - CURRENT_MINUTES))
        echo $((MINUTES_TO_WAIT * 60))
    else
        # Target time is tomorrow (24 hours - elapsed + target)
        local MINUTES_TO_WAIT=$((1440 - CURRENT_MINUTES + TARGET_MINUTES))
        echo $((MINUTES_TO_WAIT * 60))
    fi
}

# Function to calculate seconds until next 00:00 (midnight)
calculate_sleep_until_midnight() {
    local NOW=$(date +%s)
    local CURRENT_HOUR=$(date +%H)
    local CURRENT_MIN=$(date +%M)
    local CURRENT_SEC=$(date +%S)
    
    # Convert current time to seconds since midnight
    local CURRENT_SECONDS=$((CURRENT_HOUR * 3600 + CURRENT_MIN * 60 + CURRENT_SEC))
    
    # Calculate seconds until next midnight
    if [ "$CURRENT_SECONDS" -eq 0 ]; then
        # Already at midnight
        echo 0
    else
        # Seconds until next midnight (24 hours - elapsed)
        echo $((86400 - CURRENT_SECONDS))
    fi
}

# Function to handle script termination
cleanup_and_exit() {
    log "Received termination signal, shutting down gracefully"
    rm -f "$PID_FILE"
    # Note: We intentionally keep RESET_FLAG_FILE to remember that initial reset was done
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
    
    # Configure nlbwmon database_interval for daily midnight resets on startup
    log "Configuring nlbwmon for daily midnight resets..."
    local TODAY=$(date +%Y-%m-%d)
    if uci set nlbwmon.@nlbwmon[0].database_interval="$TODAY/1" && uci commit nlbwmon >/dev/null 2>&1; then
        log "Successfully configured database_interval to $TODAY/1 for daily midnight resets"
        # Restart nlbwmon to apply the new database_interval configuration
        if /etc/init.d/nlbwmon restart >/dev/null 2>&1; then
            log "nlbwmon service restarted with new database_interval configuration"
        else
            log "WARNING: Failed to restart nlbwmon service after database_interval configuration"
        fi
    else
        log "WARNING: Failed to configure database_interval - continuing with default behavior"
    fi
    
    # Main loop - runs forever with two-step process: backup at 23:55, reset at 00:00
    while true; do
        # Step 1: Sleep until next 23:55 for backup
        local SLEEP_SECONDS=$(calculate_sleep_seconds)
        local HOURS=$((SLEEP_SECONDS / 3600))
        local MINUTES=$(((SLEEP_SECONDS % 3600) / 60))
        
        log "Next backup in ${HOURS}h ${MINUTES}m (sleeping $SLEEP_SECONDS seconds)"
        
        # Sleep until backup time
        sleep "$SLEEP_SECONDS"
        
        # Perform the daily backup
        perform_daily_backup
        
        # Step 2: Sleep until midnight (00:00) for reset
        local SLEEP_UNTIL_MIDNIGHT=$(calculate_sleep_until_midnight)
        local MINUTES_UNTIL_MIDNIGHT=$((SLEEP_UNTIL_MIDNIGHT / 60))
        
        log "Backup completed. Sleeping ${MINUTES_UNTIL_MIDNIGHT} minutes until midnight reset..."
        
        # Sleep until midnight
        sleep "$SLEEP_UNTIL_MIDNIGHT"
        
        # Perform midnight reset
        perform_midnight_reset
        
        # Sleep for 70 seconds to avoid running twice in the same minute
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
            # Run in background and detach from terminal
            "$0" daemon </dev/null >/dev/null 2>&1 &
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
        PID=$(cat "$PID_FILE")  # Remove 'local' keyword
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
            PID=$(cat "$PID_FILE")  # Remove 'local' keyword
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
    
    reset)
        echo "Resetting daemon state..."
        if is_daemon_running; then
            echo "ERROR: Cannot reset while daemon is running. Stop the daemon first."
            exit 1
        fi
        
        # Remove reset flag to force service restart on next midnight
        if [ -f "$RESET_FLAG_FILE" ]; then
            rm -f "$RESET_FLAG_FILE"
            echo "Reset flag cleared - next midnight will perform service restart"
            log "Reset flag manually cleared via '$0 reset' command"
        else
            echo "Reset flag was not set - next midnight will perform service restart anyway"
        fi
        ;;
    
    *)
        echo "Usage: $0 {start|stop|status|test|reset}"
        echo ""
        echo "Commands:"
        echo "  start  - Start the daily backup daemon"
        echo "  stop   - Stop the daily backup daemon" 
        echo "  status - Show daemon status and recent logs"
        echo "  test   - Run a test backup immediately"
        echo "  reset  - Clear reset flag (force service restart on next midnight)"
        echo ""
        echo "The daemon will run forever and perform daily backups at 23:55"
        echo "It will keep the last $MAX_FILES daily backup files"
        echo "Midnight resets: First reset uses service restart, then automatic via database_interval"
        exit 1
        ;;
esac
