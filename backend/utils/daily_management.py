"""
Daily backup script management utilities for nlbwmon data.

This module handles deployment, management, and monitoring of daily backup scripts
on the router filesystem. These scripts provide automated daily data backup and
cleanup functionality for nlbwmon usage data.
"""

from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
import os

logger = get_logger('utils.daily_management')

# Router script paths
ROUTER_SCRIPTS_DIR = "/tmp/netpilot_scripts"
DAILY_BACKUP_SCRIPT = f"{ROUTER_SCRIPTS_DIR}/daily_save_and_clean.sh"
CHECK_BACKUP_SCRIPT = f"{ROUTER_SCRIPTS_DIR}/check_daily_backup.sh"
STOP_BACKUP_SCRIPT = f"{ROUTER_SCRIPTS_DIR}/stop_daily_backup.sh"

def _get_script_content(script_name):
    """Read script content from local router_scripts directory."""
    try:
        # Get the services directory path, then navigate to router_scripts
        services_dir = os.path.dirname(os.path.dirname(__file__))  # Go up from utils to backend
        script_path = os.path.join(services_dir, 'services', 'router_scripts', script_name)
        with open(script_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read script {script_name}: {e}")
        return None

def _deploy_script_to_router(script_name, router_path, router_connection_manager):
    """Deploy a single script to router filesystem."""
    try:
        # Read script content
        content = _get_script_content(script_name)
        if not content:
            return False, f"Failed to read script content for {script_name}"
        
        # Create directory on router
        mkdir_output, mkdir_error = router_connection_manager.execute(f"mkdir -p {ROUTER_SCRIPTS_DIR}")
        if mkdir_error:
            return False, f"Failed to create script directory: {mkdir_error}"
        
        # Create script on router using heredoc to avoid quote issues
        deploy_command = f"""cat > {router_path} << 'EOF_NETPILOT_SCRIPT'
{content}
EOF_NETPILOT_SCRIPT"""
        
        deploy_output, deploy_error = router_connection_manager.execute(deploy_command)
        if deploy_error:
            return False, f"Failed to create script file: {deploy_error}"
        
        # Make script executable
        chmod_output, chmod_error = router_connection_manager.execute(f"chmod +x {router_path}")
        if chmod_error:
            return False, f"Failed to make script executable: {chmod_error}"
        
        # Verify script was created
        verify_output, verify_error = router_connection_manager.execute(f"[ -f {router_path} ] && echo 'exists' || echo 'missing'")
        if verify_error or 'missing' in verify_output:
            return False, f"Script verification failed - file not found"
        
        logger.info(f"Successfully deployed {script_name} to {router_path}")
        return True, None
        
    except Exception as e:
        logger.error(f"Error deploying script {script_name}: {e}")
        return False, str(e)

def deploy_daily_backup_scripts(router_connection_manager):
    """Deploy all daily backup scripts to router filesystem."""
    try:
        logger.info("Deploying daily backup scripts to router")
        
        scripts_to_deploy = [
            ('daily_save_and_clean.sh', DAILY_BACKUP_SCRIPT),
            ('check_daily_backup.sh', CHECK_BACKUP_SCRIPT),
            ('stop_daily_backup.sh', STOP_BACKUP_SCRIPT)
        ]
        
        deployed_count = 0
        errors = []
        
        for script_name, router_path in scripts_to_deploy:
            success, error = _deploy_script_to_router(script_name, router_path, router_connection_manager)
            if success:
                deployed_count += 1
            else:
                errors.append(f"{script_name}: {error}")
        
        if deployed_count == len(scripts_to_deploy):
            logger.info(f"Successfully deployed all {deployed_count} daily backup scripts")
            return True, None
        else:
            error_msg = f"Deployed {deployed_count}/{len(scripts_to_deploy)} scripts. Errors: {'; '.join(errors)}"
            logger.error(error_msg)
            return False, error_msg
            
    except Exception as e:
        logger.error(f"Error deploying daily backup scripts: {e}")
        return False, str(e)

def check_daily_backup_status(router_connection_manager):
    """Check if daily backup daemon is running on router."""
    try:
        logger.info("Checking daily backup daemon status")
        
        # Execute check script
        output, error = router_connection_manager.execute(CHECK_BACKUP_SCRIPT)
        
        if error:
            # If script doesn't exist, it means scripts aren't deployed
            if 'No such file' in error:
                return False, "Daily backup scripts not deployed"
            return False, f"Failed to check backup status: {error}"
        
        # Parse result - script outputs "RUNNING" or "STOPPED"
        status = output.strip()
        is_running = (status == "RUNNING")
        
        logger.info(f"Daily backup daemon status: {status}")
        return is_running, None
        
    except Exception as e:
        logger.error(f"Error checking daily backup status: {e}")
        return False, str(e)

def start_daily_backup_daemon(router_connection_manager):
    """Start the daily backup daemon on router."""
    try:
        logger.info("Starting daily backup daemon")
        
        # Execute start command
        output, error = router_connection_manager.execute(f"{DAILY_BACKUP_SCRIPT} start")
        
        if error:
            if 'No such file' in error:
                return False, "Daily backup scripts not deployed"
            return False, f"Failed to start backup daemon: {error}"
        
        # Check if start was successful
        if 'already running' in output:
            logger.info("Daily backup daemon was already running")
            return True, "Already running"
        elif 'started successfully' in output:
            logger.info("Daily backup daemon started successfully")
            return True, "Started successfully"
        else:
            # If no error but unexpected output, assume success
            logger.warning(f"Unexpected start response: {output}")
            return True, "Started (unexpected output)"
            
    except Exception as e:
        logger.error(f"Error starting daily backup daemon: {e}")
        return False, str(e)

def stop_daily_backup_daemon(router_connection_manager):
    """Stop the daily backup daemon on router."""
    try:
        logger.info("Stopping daily backup daemon")
        
        # Execute stop script
        output, error = router_connection_manager.execute(STOP_BACKUP_SCRIPT)
        
        if error:
            if 'No such file' in error:
                return False, "Daily backup scripts not deployed"
            return False, f"Failed to stop backup daemon: {error}"
        
        # Parse result
        if 'not running' in output:
            logger.info("Daily backup daemon was not running")
            return True, "Not running"
        elif 'stopped successfully' in output:
            logger.info("Daily backup daemon stopped successfully")
            return True, "Stopped successfully"
        elif 'Failed to stop' in output:
            return False, f"Failed to stop daemon: {output}"
        else:
            # Assume success if no error indicators
            logger.info(f"Daily backup daemon stop command completed: {output}")
            return True, "Stop completed"
            
    except Exception as e:
        logger.error(f"Error stopping daily backup daemon: {e}")
        return False, str(e)

def setup_daily_backup_infrastructure(router_connection_manager):
    """Set up monitoring infrastructure with exact flow: deploy scripts, create folder, start daemon, verify."""
    try:
        logger.info("Setting up daily backup infrastructure")
        
        # 4.1: Create scripts folder + copy the scripts
        deploy_success, deploy_error = deploy_daily_backup_scripts(router_connection_manager)
        if not deploy_success:
            return False, f"Script deployment failed: {deploy_error}"
        
        # 4.2: Create the daily folder (or nothing if exists)
        backup_dir = "/tmp/nlbwmon/daily"
        mkdir_output, mkdir_error = router_connection_manager.execute(f"mkdir -p {backup_dir}")
        if mkdir_error:
            logger.warning(f"Failed to create backup directory: {mkdir_error}")
        
        # 4.3: Start the daemon (script handles proper detachment internally)
        start_success, start_error = start_daily_backup_daemon(router_connection_manager)
        if not start_success:
            return False, f"Failed to start daemon: {start_error}"

        # 4.4: Verify the daemon is running (with delay to let it start and detach)
        import time
        time.sleep(4)  # Give daemon time to start and detach properly
        
        is_running, verify_error = check_daily_backup_status(router_connection_manager)
        if verify_error:
            logger.error(f"Daemon verification failed: {verify_error}")
            return False, f"Daemon verification failed: {verify_error}"
        elif not is_running:
            logger.error("Daemon started but not detected as running")
            return False, "Daemon started but not detected as running"
        else:
            logger.info("Daemon verified as running")
        
        logger.info("Daily backup infrastructure setup completed successfully")
        return True, None
        
    except Exception as e:
        logger.error(f"Error setting up daily backup infrastructure: {e}")
        return False, f"Infrastructure setup failed: {str(e)}"

def get_daily_backup_logs(router_connection_manager):
    """Get recent daily backup log entries."""
    try:
        logger.info("Fetching daily backup logs")
        
        log_file = "/tmp/nlbwmon/daily/daily_backup.log"
        
        # Check if log file exists and get recent entries
        output, error = router_connection_manager.execute(f"[ -f {log_file} ] && tail -n 20 {log_file} || echo 'Log file not found'")
        
        if error:
            return None, f"Failed to read log file: {error}"
        
        if 'Log file not found' in output:
            return [], None  # Empty logs but no error
        
        # Parse log entries
        log_lines = output.strip().split('\n')
        log_entries = []
        
        for line in log_lines:
            if line.strip() and ' - ' in line:
                try:
                    timestamp_str, message = line.split(' - ', 1)
                    log_entries.append({
                        'timestamp': timestamp_str.strip(),
                        'message': message.strip()
                    })
                except:
                    # If parsing fails, include raw line
                    log_entries.append({'raw': line.strip()})
        
        logger.info(f"Retrieved {len(log_entries)} log entries")
        return log_entries, None
        
    except Exception as e:
        logger.error(f"Error getting daily backup logs: {e}")
        return None, str(e)
