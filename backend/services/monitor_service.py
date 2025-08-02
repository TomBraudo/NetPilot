from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
import json
import os
from datetime import datetime

logger = get_logger('services.monitor')
router_connection_manager = RouterConnectionManager()

# Router script paths

ROUTER_SCRIPTS_DIR = "/tmp/netpilot_scripts"
DAILY_BACKUP_SCRIPT = f"{ROUTER_SCRIPTS_DIR}/daily_save_and_clean.sh"
CHECK_BACKUP_SCRIPT = f"{ROUTER_SCRIPTS_DIR}/check_daily_backup.sh"
STOP_BACKUP_SCRIPT = f"{ROUTER_SCRIPTS_DIR}/stop_daily_backup.sh"

def _bytes_to_mb(bytes_val):
    """Convert bytes to megabytes with 2 decimal places."""
    return round(bytes_val / (1024 * 1024), 2)

def _bytes_to_gb(bytes_val):
    """Convert bytes to gigabytes with 2 decimal places."""
    return round(bytes_val / (1024 * 1024 * 1024), 2)

def get_current_device_usage():
    """Get current device usage - returns simplified device list with usage stats."""
    try:
        logger.info("Fetching current device usage data")
        result = router_connection_manager.execute('nlbw -c json')
        
        if not result['success']:
            return None, f"Failed to execute nlbw command: {result.get('error', 'Unknown error')}"
        
        try:
            usage_data = json.loads(result['output'])
        except json.JSONDecodeError as e:
            return None, "Invalid JSON response from nlbw"
        
        # Aggregate data by MAC address
        devices = {}
        for entry in usage_data.get('data', []):
            if len(entry) >= 11:
                family, proto, port, mac, ip, conns, rx_bytes, rx_pkts, tx_bytes, tx_pkts, layer7 = entry[:11]
                
                if mac not in devices:
                    devices[mac] = {
                        'mac': mac,
                        'ip': ip,
                        'rx_bytes': 0,
                        'tx_bytes': 0,
                        'connections': 0,
                        'services': set()
                    }
                
                devices[mac]['rx_bytes'] += rx_bytes
                devices[mac]['tx_bytes'] += tx_bytes
                devices[mac]['connections'] += conns
                if layer7:
                    devices[mac]['services'].add(layer7)
        
        # Convert to clean response format
        device_list = []
        for device in devices.values():
            device_list.append({
                'mac': device['mac'],
                'ip': device['ip'],
                'download_mb': _bytes_to_mb(device['rx_bytes']),
                'upload_mb': _bytes_to_mb(device['tx_bytes']),
                'connections': device['connections'],
                'top_services': list(device['services'])[:3]  # Top 3 services
            })
        
        # Sort by total usage (download + upload)
        device_list.sort(key=lambda x: x['download_mb'] + x['upload_mb'], reverse=True)
        
        logger.info(f"Successfully retrieved usage data for {len(device_list)} devices")
        return device_list, None
        
    except Exception as e:
        logger.error(f"Error getting current device usage: {e}")
        return None, str(e)

def get_historical_device_usage(days=7):
    """Get historical device usage - returns daily summaries by device."""
    try:
        logger.info(f"Fetching historical device usage for {days} days")
        
        # Get list of available databases
        list_result = router_connection_manager.execute('nlbw -c list')
        if not list_result['success']:
            return None, "Failed to get available databases"
        
        # Parse available dates
        available_dates = [line.strip() for line in list_result['output'].strip().split('\n') if line.strip()]
        
        if not available_dates:
            return {}, None  # Empty but successful
        
        # Get data for requested days
        historical_data = {}
        
        for date in available_dates[:days]:
            try:
                result = router_connection_manager.execute(f'nlbw -c json -t {date}')
                
                if result['success']:
                    date_data = json.loads(result['output'])
                    
                    # Aggregate by device for this date
                    daily_devices = {}
                    for entry in date_data.get('data', []):
                        if len(entry) >= 11:
                            family, proto, port, mac, ip, conns, rx_bytes, rx_pkts, tx_bytes, tx_pkts, layer7 = entry[:11]
                            
                            if mac not in daily_devices:
                                daily_devices[mac] = {'mac': mac, 'rx_bytes': 0, 'tx_bytes': 0}
                            
                            daily_devices[mac]['rx_bytes'] += rx_bytes
                            daily_devices[mac]['tx_bytes'] += tx_bytes
                    
                    # Convert to clean format
                    device_summaries = []
                    for device in daily_devices.values():
                        if device['rx_bytes'] > 0 or device['tx_bytes'] > 0:  # Only include active devices
                            device_summaries.append({
                                'mac': device['mac'],
                                'download_gb': _bytes_to_gb(device['rx_bytes']),
                                'upload_gb': _bytes_to_gb(device['tx_bytes'])
                            })
                    
                    # Sort by total usage
                    device_summaries.sort(key=lambda x: x['download_gb'] + x['upload_gb'], reverse=True)
                    historical_data[date] = device_summaries[:10]  # Top 10 devices per day
                    
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to process data for {date}: {e}")
                continue
        
        logger.info(f"Retrieved historical data for {len(historical_data)} dates")
        return historical_data, None
        
    except Exception as e:
        logger.error(f"Error getting historical device usage: {e}")
        return None, str(e)

def get_device_usage_summary():
    """Get top devices by total usage - returns ranked device list."""
    try:
        logger.info("Generating device usage summary")
        
        # Get current usage data
        current_data, error = get_current_device_usage()
        if error:
            return None, error
        
        # Convert to summary format with rankings
        summary = []
        for rank, device in enumerate(current_data, 1):
            total_gb = _bytes_to_gb((device['download_mb'] + device['upload_mb']) * 1024 * 1024)
            if total_gb > 0:  # Only include devices with usage
                summary.append({
                    'rank': rank,
                    'mac': device['mac'],
                    'ip': device['ip'],
                    'total_gb': total_gb,
                    'download_gb': _bytes_to_gb(device['download_mb'] * 1024 * 1024),
                    'upload_gb': _bytes_to_gb(device['upload_mb'] * 1024 * 1024),
                    'connections': device['connections']
                })
        
        logger.info(f"Generated summary for {len(summary)} active devices")
        return summary[:20], None  # Top 20 devices
        
    except Exception as e:
        logger.error(f"Error generating device usage summary: {e}")
        return None, str(e)

def reset_usage_counters():
    
    """Reset nlbwmon usage counters - commits current data.
    try:
        logger.info("Resetting nlbwmon usage counters")
        
        # Commit current data to database
        commit_result = router_connection_manager.execute('nlbw -c commit')
        if not commit_result['success']:
            return None, f"Failed to commit data: {commit_result.get('error', 'Unknown error')}"
        
        logger.info("Data committed successfully")
        return {
            "status": "committed",
            "timestamp": datetime.now().isoformat(),
            "note": "Counters reset automatically by nlbwmon daemon"
        }, None
        
    except Exception as e:
        logger.error(f"Error resetting usage counters: {e}")
        return None, str(e)
    """
    pass

def check_nlbwmon_status():
    """Check nlbwmon service status - returns basic status info."""
    try:
        logger.info("Checking nlbwmon service status")
        
        # Test if nlbw command responds
        result = router_connection_manager.execute('nlbw -c json')
        
        if not result['success']:
            return None, f"nlbw command failed: {result.get('error', 'Unknown error')}"
        
        try:
            data = json.loads(result['output'])
            entry_count = len(data.get('data', []))
            
            # Check database files
            db_result = router_connection_manager.execute('ls -la /tmp/nlbwmon/')
            db_accessible = db_result['success']
            
            status = {
                "running": True,
                "active_devices": len(set(entry[3] for entry in data.get('data', []) if len(entry) > 3)),  # Unique MACs
                "total_entries": entry_count,
                "database_accessible": db_accessible,
                "last_update": datetime.now().isoformat()
            }
            
            logger.info(f"nlbwmon is running with {entry_count} entries")
            return status, None
            
        except json.JSONDecodeError:
            return None, "nlbwmon responding but returning invalid data"
            
    except Exception as e:
        logger.error(f"Error checking nlbwmon status: {e}")
        return None, str(e)

# =============================================================================
# DAILY BACKUP SCRIPT MANAGEMENT FUNCTIONS
# =============================================================================

def _get_script_content(script_name):
    """Read script content from local router_scripts directory."""
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'router_scripts', script_name)
        with open(script_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read script {script_name}: {e}")
        return None

def _deploy_script_to_router(script_name, router_path):
    """Deploy a single script to router filesystem."""
    try:
        # Read script content
        content = _get_script_content(script_name)
        if not content:
            return False, f"Failed to read script content for {script_name}"
        
        # Create directory on router
        mkdir_result = router_connection_manager.execute(f"mkdir -p {ROUTER_SCRIPTS_DIR}")
        if not mkdir_result['success']:
            return False, f"Failed to create script directory: {mkdir_result.get('error', 'Unknown error')}"
        
        # Create script on router using heredoc to avoid quote issues
        deploy_command = f"""cat > {router_path} << 'EOF_NETPILOT_SCRIPT'
{content}
EOF_NETPILOT_SCRIPT"""
        
        deploy_result = router_connection_manager.execute(deploy_command)
        if not deploy_result['success']:
            return False, f"Failed to create script file: {deploy_result.get('error', 'Unknown error')}"
        
        # Make script executable
        chmod_result = router_connection_manager.execute(f"chmod +x {router_path}")
        if not chmod_result['success']:
            return False, f"Failed to make script executable: {chmod_result.get('error', 'Unknown error')}"
        
        # Verify script was created
        verify_result = router_connection_manager.execute(f"[ -f {router_path} ] && echo 'exists' || echo 'missing'")
        if not verify_result['success'] or 'missing' in verify_result['output']:
            return False, f"Script verification failed - file not found"
        
        logger.info(f"Successfully deployed {script_name} to {router_path}")
        return True, None
        
    except Exception as e:
        logger.error(f"Error deploying script {script_name}: {e}")
        return False, str(e)

def deploy_daily_backup_scripts():
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
            success, error = _deploy_script_to_router(script_name, router_path)
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

def check_daily_backup_status():
    """Check if daily backup daemon is running on router."""
    try:
        logger.info("Checking daily backup daemon status")
        
        # Execute check script
        result = router_connection_manager.execute(CHECK_BACKUP_SCRIPT)
        
        if not result['success']:
            # If script doesn't exist, it means scripts aren't deployed
            if 'No such file' in result.get('error', ''):
                return False, "Daily backup scripts not deployed"
            return False, f"Failed to check backup status: {result.get('error', 'Unknown error')}"
        
        # Parse result - script outputs "RUNNING" or "STOPPED"
        status = result['output'].strip()
        is_running = (status == "RUNNING")
        
        logger.info(f"Daily backup daemon status: {status}")
        return is_running, None
        
    except Exception as e:
        logger.error(f"Error checking daily backup status: {e}")
        return False, str(e)

def start_daily_backup_daemon():
    """Start the daily backup daemon on router."""
    try:
        logger.info("Starting daily backup daemon")
        
        # Execute start command
        result = router_connection_manager.execute(f"{DAILY_BACKUP_SCRIPT} start")
        
        if not result['success']:
            if 'No such file' in result.get('error', ''):
                return False, "Daily backup scripts not deployed"
            return False, f"Failed to start backup daemon: {result.get('error', 'Unknown error')}"
        
        # Check if start was successful
        if 'already running' in result['output']:
            logger.info("Daily backup daemon was already running")
            return True, "Already running"
        elif 'started successfully' in result['output']:
            logger.info("Daily backup daemon started successfully")
            
            # Verify it's actually running
            is_running, check_error = check_daily_backup_status()
            if check_error:
                return False, f"Started but verification failed: {check_error}"
            elif not is_running:
                return False, "Started but daemon is not running"
            
            return True, "Started successfully"
        else:
            return False, f"Unexpected start response: {result['output']}"
            
    except Exception as e:
        logger.error(f"Error starting daily backup daemon: {e}")
        return False, str(e)

def stop_daily_backup_daemon():
    """Stop the daily backup daemon on router."""
    try:
        logger.info("Stopping daily backup daemon")
        
        # Execute stop script
        result = router_connection_manager.execute(STOP_BACKUP_SCRIPT)
        
        if not result['success']:
            if 'No such file' in result.get('error', ''):
                return False, "Daily backup scripts not deployed"
            return False, f"Failed to stop backup daemon: {result.get('error', 'Unknown error')}"
        
        # Parse result
        if 'not running' in result['output']:
            logger.info("Daily backup daemon was not running")
            return True, "Not running"
        elif 'stopped successfully' in result['output']:
            logger.info("Daily backup daemon stopped successfully")
            return True, "Stopped successfully"
        elif 'Failed to stop' in result['output']:
            return False, f"Failed to stop daemon: {result['output']}"
        else:
            # Assume success if no error indicators
            logger.info(f"Daily backup daemon stop command completed: {result['output']}")
            return True, "Stop completed"
            
    except Exception as e:
        logger.error(f"Error stopping daily backup daemon: {e}")
        return False, str(e)

def setup_daily_backup_infrastructure():
    """Complete setup of daily backup infrastructure - deploy scripts and start daemon."""
    try:
        logger.info("Setting up daily backup infrastructure")
        
        # Step 1: Deploy scripts
        deploy_success, deploy_error = deploy_daily_backup_scripts()
        if not deploy_success:
            return False, f"Script deployment failed: {deploy_error}"
        
        # Step 2: Check if daemon is already running
        is_running, check_error = check_daily_backup_status()
        if check_error:
            return False, f"Status check failed: {check_error}"
        
        if is_running:
            logger.info("Daily backup daemon is already running - setup complete")
            return True, "Already running"
        
        # Step 3: Start daemon
        start_success, start_error = start_daily_backup_daemon()
        if not start_success:
            return False, f"Failed to start daemon: {start_error}"
        
        logger.info("Daily backup infrastructure setup completed successfully")
        return True, "Setup completed successfully"
        
    except Exception as e:
        logger.error(f"Error setting up daily backup infrastructure: {e}")
        return False, str(e)

def get_daily_backup_logs():
    """Get recent daily backup log entries."""
    try:
        logger.info("Fetching daily backup logs")
        
        log_file = "/tmp/nlbwmon/daily/daily_backup.log"
        
        # Check if log file exists and get recent entries
        result = router_connection_manager.execute(f"[ -f {log_file} ] && tail -n 20 {log_file} || echo 'Log file not found'")
        
        if not result['success']:
            return None, f"Failed to read log file: {result.get('error', 'Unknown error')}"
        
        if 'Log file not found' in result['output']:
            return [], None  # Empty logs but no error
        
        # Parse log entries
        log_lines = result['output'].strip().split('\n')
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
