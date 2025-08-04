from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
import json
import os
from datetime import datetime

logger = get_logger('services.monitor')
router_connection_manager = RouterConnectionManager()

# Router script paths - kept for reference but actual management moved to utils.daily_management
ROUTER_SCRIPTS_DIR = "/tmp/netpilot_scripts"
DAILY_BACKUP_SCRIPT = f"{ROUTER_SCRIPTS_DIR}/daily_save_and_clean.sh"
CHECK_BACKUP_SCRIPT = f"{ROUTER_SCRIPTS_DIR}/check_daily_backup.sh"
STOP_BACKUP_SCRIPT = f"{ROUTER_SCRIPTS_DIR}/stop_daily_backup.sh"

class DeviceUsage():
    def __init__(self, mac, ip, download, upload, connections):
        self.mac = mac
        self.ip = ip
        self.download = download  # Always in MB
        self.upload = upload      # Always in MB
        self.connections = connections
        self.unit = 'MB'  # Always MB
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'mac': self.mac,
            'ip': self.ip,
            'download': round(self.download, 2),
            'upload': round(self.upload, 2),
            'unit': self.unit,
            'connections': self.connections
        }
    def combine(self, other):
        """Combine another DeviceUsage instance into this one."""
        if self.mac != other.mac:
            raise ValueError("Cannot combine different devices")
        
        # Since both are always in MB, just add them directly
        self.download += other.download
        self.upload += other.upload
        # Unit stays 'MB'

def _bytes_to_mb(bytes_val):
    """Convert bytes to megabytes with 2 decimal places."""
    return round(bytes_val / (1024 * 1024), 2)

def _bytes_to_gb(bytes_val):
    """Convert bytes to gigabytes with 2 decimal places."""
    return round(bytes_val / (1024 * 1024 * 1024), 2)

# =============================================================================
# PRIVATE UTILITY FUNCTIONS FOR JSON PROCESSING AND DATA AGGREGATION
# =============================================================================

def _parse_nlbw_json_response(raw_output):
    """Parse nlbw command JSON output and return structured data.
    
    Args:
        raw_output (str): Raw JSON string from nlbw command
        
    Returns:
        tuple: (parsed_data, error_message)
            parsed_data: List of nlbw entries or None if error
            error_message: Error description or None if successful
    """
    try:
        if not raw_output or not raw_output.strip():
            return None, "Empty response from nlbw command"
            
        usage_data = json.loads(raw_output)
        entries = usage_data.get('data', [])
        
        if not isinstance(entries, list):
            return None, "Invalid data format - expected list of entries"
            
        logger.debug(f"Parsed {len(entries)} nlbw entries from JSON response")
        return entries, None
        
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON response from nlbw: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error parsing nlbw response: {str(e)}"

def _parse_nlbw_entry(entry):
    """Parse a single nlbw entry into structured format.
    
    Args:
        entry (list): Raw nlbw entry array
        
    Returns:
        dict or None: Parsed entry data or None if invalid
    """
    try:
        if not isinstance(entry, list) or len(entry) < 11:
            return None
            
        # Extract the standard 11 fields from nlbw entry
        family, proto, port, mac, ip, conns, rx_bytes, rx_pkts, tx_bytes, tx_pkts, layer7 = entry[:11]
        
        # Validate required fields
        if not mac or not ip:
            return None
            
        return {
            'family': family,
            'protocol': proto,
            'port': port,
            'mac': mac,
            'ip': ip,
            'connections': int(conns) if isinstance(conns, (int, float)) else 0,
            'rx_bytes': int(rx_bytes) if isinstance(rx_bytes, (int, float)) else 0,
            'rx_packets': int(rx_pkts) if isinstance(rx_pkts, (int, float)) else 0,
            'tx_bytes': int(tx_bytes) if isinstance(tx_bytes, (int, float)) else 0,
            'tx_packets': int(tx_pkts) if isinstance(tx_pkts, (int, float)) else 0,
            'layer7_service': layer7 if layer7 else None
        }
        
    except (ValueError, TypeError, IndexError) as e:
        logger.debug(f"Failed to parse nlbw entry {entry}: {e}")
        return None

def _aggregate_entries_by_device(entries):
    """Aggregate nlbw entries by MAC address to get per-device totals.
    
    Args:
        entries (list): List of parsed nlbw entries
        
    Returns:
        dict: Device aggregations keyed by MAC address
    """
    devices = {}
    
    for entry in entries:
        parsed = _parse_nlbw_entry(entry)
        if not parsed:
            continue
            
        mac = parsed['mac']
        
        if mac not in devices:
            devices[mac] = {
                'mac': mac,
                'ip': parsed['ip'],  # Use last seen IP
                'rx_bytes': 0,
                'tx_bytes': 0,
                'rx_packets': 0,
                'tx_packets': 0,
                'connections': 0,
                'services': set(),
                'protocols': set(),
                'ports': set()
            }
        
        # Aggregate the data
        device = devices[mac]
        device['rx_bytes'] += parsed['rx_bytes']
        device['tx_bytes'] += parsed['tx_bytes']
        device['rx_packets'] += parsed['rx_packets']
        device['tx_packets'] += parsed['tx_packets']
        device['connections'] += parsed['connections']
        
        # Track unique services, protocols, and ports
        if parsed['layer7_service']:
            device['services'].add(parsed['layer7_service'])
        if parsed['protocol']:
            device['protocols'].add(parsed['protocol'])
        if parsed['port']:
            device['ports'].add(parsed['port'])
    
    logger.debug(f"Aggregated {len(entries)} entries into {len(devices)} devices")
    return devices

def _format_device_for_current_usage(device_data):
    """Format aggregated device data for current usage API response.
    
    Args:
        device_data (dict): Aggregated device data
        
    Returns:
        DeviceUsage: Formatted device data object
    """
    # Always use MB values
    download = _bytes_to_mb(device_data['rx_bytes'])
    upload = _bytes_to_mb(device_data['tx_bytes'])
    
    return DeviceUsage(
        mac=device_data['mac'],
        ip=device_data['ip'],
        download=download,
        upload=upload,
        connections=device_data['connections']
    )

def _format_device_for_historical_usage(device_data):
    """Format aggregated device data for historical usage API response.
    
    Args:
        device_data (dict): Aggregated device data
        
    Returns:
        DeviceUsage: Formatted device data object
    """
    return DeviceUsage(
        mac=device_data['mac'],
        ip=device_data.get('ip'),  # IP might not be available in historical data
        download=_bytes_to_mb(device_data['rx_bytes']),
        upload=_bytes_to_mb(device_data['tx_bytes']),
        connections=device_data.get('connections', 0)  # Connections might not be available
    )



def _get_nlbw_current_data():
    """Get and parse current nlbw data with error handling.
    
    Returns:
        tuple: (parsed_entries, error_message)
    """
    try:
        output, error = router_connection_manager.execute('nlbw -c json')
        
        if error:
            return None, f"Failed to execute nlbw command: {error}"
        
        return _parse_nlbw_json_response(output)
        
    except Exception as e:
        logger.error(f"Error getting current nlbw data: {e}")
        return None, str(e)

def _get_nlbw_historical_data(date):
    """Get and parse historical nlbw data for specific date.
    
    Args:
        date (str): Date identifier for historical data
        
    Returns:
        tuple: (parsed_entries, error_message)
    """
    try:
        output, error = router_connection_manager.execute(f'nlbw -c json -t {date}')
        
        if error:
            return None, f"Failed to get data for {date}: {error}"
        
        return _parse_nlbw_json_response(output)
        
    except Exception as e:
        logger.error(f"Error getting historical data for {date}: {e}")
        return None, str(e)

def _get_daily_json_file_data(date):
    """Get data from daily JSON backup file.
    
    Args:
        date (str): Date in YYYY-MM-DD format
        
    Returns:
        tuple: (parsed_entries, error_message)
    """
    try:
        daily_file = f"/tmp/nlbwmon/daily/daily_{date}.json"
        output, error = router_connection_manager.execute(f"[ -f {daily_file} ] && cat {daily_file} || echo 'File not found'")
        
        if error:
            return None, f"Failed to read daily file for {date}: {error}"
        
        if 'File not found' in output:
            return None, f"Daily backup file not found for {date}"
        
        return _parse_nlbw_json_response(output)
        
    except Exception as e:
        logger.error(f"Error reading daily file for {date}: {e}")
        return None, str(e)

def _filter_active_devices(devices, min_bytes=0):
    """Filter devices to only include those with usage above threshold.
    
    Args:
        devices (dict): Device data keyed by MAC
        min_bytes (int): Minimum total bytes to include device
        
    Returns:
        dict: Filtered devices
    """
    filtered = {}
    for mac, device in devices.items():
        total_bytes = device.get('rx_bytes', 0) + device.get('tx_bytes', 0)
        if total_bytes > min_bytes:
            filtered[mac] = device
    
    logger.debug(f"Filtered {len(devices)} devices down to {len(filtered)} active devices")
    return filtered

# =============================================================================
# PRIVATE FUNCTIONS FOR DEVICE-SPECIFIC DATA RETRIEVAL BY TIME PERIOD
# =============================================================================

def _get_device_from_aggregated_data(devices, mac_address, min_bytes_threshold, period_name):
    """Extract specific device data from aggregated device data.
    
    Args:
        devices (dict): Aggregated device data keyed by MAC
        mac_address (str): Normalized MAC address (lowercase)
        min_bytes_threshold (int): Minimum bytes threshold for the period
        period_name (str): Period name for error messages
        
    Returns:
        tuple: (device_data, error_message)
    """
    # Find the specific device by MAC
    target_device = None
    for mac, device_data in devices.items():
        if mac.lower() == mac_address:
            target_device = device_data
            break
    
    if not target_device:
        return None, f"Device with MAC '{mac_address}' not found in {period_name} data"
    
    # Check minimum usage threshold
    total_bytes = target_device.get('rx_bytes', 0) + target_device.get('tx_bytes', 0)
    if total_bytes < min_bytes_threshold:
        return None, f"Device with MAC '{mac_address}' has insufficient {period_name} usage data"
    
    return target_device, None

def _get_device_current_data(mac_address):
    """Get current usage data for a specific device by MAC.
    
    Args:
        mac_address (str): Normalized MAC address (lowercase)
        
    Returns:
        tuple: (device_data, error_message)
    """
    try:
        # Reuse existing current data logic
        entries, error = _get_nlbw_current_data()
        if error:
            return None, error
        
        if not entries:
            return None, "No current data available"
        
        # Aggregate by device using existing function
        devices = _aggregate_entries_by_device(entries)
        
        # Extract the specific device
        return _get_device_from_aggregated_data(devices, mac_address, 1024, "current")
        
    except Exception as e:
        logger.error(f"Error getting current data for MAC {mac_address}: {e}")
        return None, str(e)

def _get_device_week_data(mac_address):
    """Get weekly usage data for a specific device by MAC.
    
    Reuses the existing weekly data collection logic but works with raw data to preserve IP.
    
    Args:
        mac_address (str): Normalized MAC address (lowercase)
        
    Returns:
        tuple: (device_data, error_message)
    """
    try:
        # Step 1: Get current usage data
        current_entries, error = _get_nlbw_current_data()
        if error:
            logger.warning(f"Failed to get current data: {error}")
            current_entries = []
        
        # Step 2: Get the last 6 daily backup files
        output, error = router_connection_manager.execute('ls -1 /tmp/nlbwmon/daily/daily_*.json 2>/dev/null | sort -r | head -6')
        if error:
            logger.warning("Failed to list daily backup files, using only current data")
            daily_files = []
        else:
            daily_files = [line.strip() for line in output.strip().split('\n') if line.strip()]
        
        # Step 3: Collect all entries from daily files
        all_entries = current_entries if current_entries else []
        
        for file_path in daily_files:
            try:
                # Extract date from filename: /tmp/nlbwmon/daily/daily_2024-08-01.json -> 2024-08-01
                filename = file_path.split('/')[-1]
                if filename.startswith('daily_') and filename.endswith('.json'):
                    date = filename[6:-5]  # Remove 'daily_' prefix and '.json' suffix
                    
                    entries, error = _get_daily_json_file_data(date)
                    if error:
                        logger.warning(f"Failed to get data for {date}: {error}")
                        continue
                    
                    if entries:
                        all_entries.extend(entries)
                        logger.debug(f"Added {len(entries)} entries from {date}")
                    
            except Exception as e:
                logger.warning(f"Failed to process daily file {file_path}: {e}")
                continue
        
        if not all_entries:
            return None, "No weekly data available"
        
        # Step 4: Aggregate all entries by device
        devices = _aggregate_entries_by_device(all_entries)
        
        # Step 5: Extract the specific device using existing helper
        return _get_device_from_aggregated_data(devices, mac_address, 1024*1024, "weekly")
        
    except Exception as e:
        logger.error(f"Error getting weekly data for MAC {mac_address}: {e}")
        return None, str(e)

def _get_device_month_data(mac_address):
    """Get monthly usage data for a specific device by MAC.
    
    Uses nlbw monthly database directly to preserve IP information.
    
    Args:
        mac_address (str): Normalized MAC address (lowercase)
        
    Returns:
        tuple: (device_data, error_message)
    """
    try:
        # Step 1: Get current date and calculate first of current month
        from datetime import datetime
        current_date = datetime.now()
        first_of_month = current_date.strftime('%Y-%m-01')
        
        logger.debug(f"Looking for monthly data for: {first_of_month}")
        
        # Step 2: Get monthly data using nlbw historical command
        entries, error = _get_nlbw_historical_data(first_of_month)
        if error:
            return None, f"Failed to get monthly data for {first_of_month}: {error}"
        
        if not entries:
            return None, "No monthly data available"
        
        # Step 3: Aggregate by device
        devices = _aggregate_entries_by_device(entries)
        
        # Step 4: Extract the specific device using existing helper
        return _get_device_from_aggregated_data(devices, mac_address, 10*1024*1024, "monthly")
        
    except Exception as e:
        logger.error(f"Error getting monthly data for MAC {mac_address}: {e}")
        return None, str(e)

def get_current_device_usage():
    """Get current device usage - returns simplified device list with usage stats.
    
    This function gets real-time usage data from the active nlbw process,
    not from backup files or monthly databases.
    """
    try:
        logger.info("Fetching current device usage data")
        
        # Get current nlbw data using helper function
        entries, error = _get_nlbw_current_data()
        if error:
            return None, error
        
        if not entries:
            return [], None
        
        # Aggregate by device using helper function
        devices = _aggregate_entries_by_device(entries)
        
        # Filter active devices
        active_devices = _filter_active_devices(devices, min_bytes=1024)  # Filter < 1KB
        
        # Format and sort devices
        device_objects = []
        for device in active_devices.values():
            device_obj = _format_device_for_current_usage(device)
            device_objects.append(device_obj)
        
        # Sort by total usage (all values are in MB now)
        device_objects.sort(key=lambda x: x.download + x.upload, reverse=True)
        
        # Convert to dictionaries for API response
        device_list = [device_obj.to_dict() for device_obj in device_objects]
        
        logger.info(f"Successfully retrieved usage data for {len(device_list)} devices")
        return device_list, None
        
    except Exception as e:
        logger.error(f"Error getting current device usage: {e}")
        return None, str(e)

def get_last_week_device_usage():
    """Get device usage for the last week (6 daily files + current).
    
    Combines the last 6 daily backup files with current usage data.
    """
    try:
        logger.info("Fetching last week device usage (6 daily files + current)")
        
        # Step 1: Get current usage data
        current_entries, error = _get_nlbw_current_data()
        if error:
            logger.warning(f"Failed to get current data: {error}")
            current_entries = []
        
        # Step 2: Get the last 6 daily backup files
        output, error = router_connection_manager.execute('ls -1 /tmp/nlbwmon/daily/daily_*.json 2>/dev/null | sort -r | head -6')
        if error:
            logger.warning("Failed to list daily backup files, using only current data")
            daily_files = []
        else:
            daily_files = [line.strip() for line in output.strip().split('\n') if line.strip()]
        
        # Step 3: Collect all entries from daily files
        all_entries = current_entries if current_entries else []
        
        for file_path in daily_files:
            try:
                # Extract date from filename: /tmp/nlbwmon/daily/daily_2024-08-01.json -> 2024-08-01
                filename = file_path.split('/')[-1]
                if filename.startswith('daily_') and filename.endswith('.json'):
                    date = filename[6:-5]  # Remove 'daily_' prefix and '.json' suffix
                    
                    entries, error = _get_daily_json_file_data(date)
                    if error:
                        logger.warning(f"Failed to get data for {date}: {error}")
                        continue
                    
                    if entries:
                        all_entries.extend(entries)
                        logger.debug(f"Added {len(entries)} entries from {date}")
                    
            except Exception as e:
                logger.warning(f"Failed to process daily file {file_path}: {e}")
                continue
        
        if not all_entries:
            return [], None
        
        # Step 4: Aggregate all entries by device
        devices = _aggregate_entries_by_device(all_entries)
        
        # Step 5: Filter active devices
        active_devices = _filter_active_devices(devices, min_bytes=1024*1024)  # Filter < 1MB for week
        
        # Step 6: Format for weekly usage (use GB for longer period)
        device_objects = []
        for device in active_devices.values():
            device_obj = _format_device_for_historical_usage(device)
            device_objects.append(device_obj)
        
        # Step 7: Sort by total usage
        device_objects.sort(key=lambda x: x.download + x.upload, reverse=True)
        
        # Convert to dictionaries for API response
        device_list = [device_obj.to_dict() for device_obj in device_objects]
        
        logger.info(f"Successfully retrieved week usage data for {len(device_list)} devices from {len(daily_files)} daily files + current")
        return device_list, None
        
    except Exception as e:
        logger.error(f"Error getting last week device usage: {e}")
        return None, str(e)

def get_last_month_device_usage():
    """Get device usage for the last month using monthly database.
    
    Uses nlbw monthly database for the first of the current month.
    """
    try:
        logger.info("Fetching last month device usage from monthly database")
        
        # Step 1: Get current date and calculate first of current month
        from datetime import datetime
        current_date = datetime.now()
        first_of_month = current_date.strftime('%Y-%m-01')
        
        logger.debug(f"Looking for monthly data for: {first_of_month}")
        
        # Step 2: Get monthly data using nlbw historical command
        entries, error = _get_nlbw_historical_data(first_of_month)
        if error:
            return None, f"Failed to get monthly data for {first_of_month}: {error}"
        
        if not entries:
            return [], None
        
        # Step 3: Aggregate by device
        devices = _aggregate_entries_by_device(entries)
        
        # Step 4: Filter active devices (higher threshold for monthly data)
        active_devices = _filter_active_devices(devices, min_bytes=10*1024*1024)  # Filter < 10MB for month
        
        # Step 5: Format for monthly usage (GB units)
        device_objects = []
        for device in active_devices.values():
            device_obj = _format_device_for_historical_usage(device)
            device_objects.append(device_obj)
        
        # Step 6: Sort by total usage
        device_objects.sort(key=lambda x: x.download + x.upload, reverse=True)
        
        # Convert to dictionaries for API response
        device_list = [device_obj.to_dict() for device_obj in device_objects]
        
        logger.info(f"Successfully retrieved monthly usage data for {len(device_list)} devices for {first_of_month}")
        return device_list, None
        
    except Exception as e:
        logger.error(f"Error getting last month device usage: {e}")
        return None, str(e)


def get_device_usage_by_mac(mac_address, period='current'):
    """Get usage data for a specific device by MAC address for different time periods.
    
    This is a wrapper function that validates input and delegates to period-specific functions.
    
    Args:
        mac_address (str): MAC address of the device
        period (str): Time period - 'current', 'week', or 'month'
        
    Returns:
        tuple: (device_data, error_message)
            device_data: Device usage data or None if error/not found
            error_message: Error description or None if successful
    """
    try:
        logger.info(f"Fetching {period} usage data for device MAC: {mac_address}")
        
        # Validate MAC address format (basic check)
        if not mac_address or not isinstance(mac_address, str):
            return None, "Invalid MAC address format"
        
        # Normalize MAC address (convert to lowercase for consistent comparison)
        mac_address = mac_address.lower().strip()
        
        # Validate period parameter
        if period not in ['current', 'week', 'month']:
            return None, f"Invalid period '{period}'. Must be 'current', 'week', or 'month'"
        
        # Get device data based on period using modular functions
        if period == 'current':
            target_device, error = _get_device_current_data(mac_address)
        elif period == 'week':
            target_device, error = _get_device_week_data(mac_address)
        else:  # period == 'month'
            target_device, error = _get_device_month_data(mac_address)
        
        # Handle errors from data retrieval
        if error:
            return None, error
        
        # Format the device data using the appropriate formatter
        if period == 'current':
            device_obj = _format_device_for_current_usage(target_device)
        else:  # week or month
            device_obj = _format_device_for_historical_usage(target_device)
        
        # Convert to dictionary for API response
        formatted_device = device_obj.to_dict()
        
        # Add period and timestamp information
        formatted_device['period'] = period
        formatted_device['timestamp'] = datetime.now().isoformat()
        
        logger.info(f"Successfully retrieved {period} usage data for device MAC: {mac_address}")
        return formatted_device, None
        
    except Exception as e:
        logger.error(f"Error getting {period} usage data for MAC {mac_address}: {e}")
        return None, str(e)

def check_nlbwmon_status():
    """Check nlbwmon service status - returns basic status info."""
    try:
        logger.info("Checking nlbwmon service status")
        
        # Test if nlbw command responds
        output, error = router_connection_manager.execute('nlbw -c json')
        
        if error:
            return None, f"nlbw command failed: {error}"
        
        try:
            data = json.loads(output)
            entry_count = len(data.get('data', []))
            
            # Check database files
            db_output, db_error = router_connection_manager.execute('ls -la /tmp/nlbwmon/')
            db_accessible = not db_error
            
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