from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from services.commands_server_operations.monitor_execute import (
    execute_get_current_devices_monitor,
    execute_get_last_week_devices_monitor,
    execute_get_last_month_devices_monitor,
    execute_get_device_monitor_by_mac
)
from .base import (
    handle_service_errors,
    log_service_operation
)

# Set up logging
logger = get_logger(__name__)


def _enrich_monitor_data_with_device_names(user_id: str, router_id: str, monitor_data: List[Dict]) -> List[Dict]:
    """
    Enrich monitor data with device names from database.
    
    Args:
        user_id: User ID
        router_id: Router ID  
        monitor_data: List of bandwidth usage data from router
        
    Returns:
        Enriched monitor data with device names
    """
    if not monitor_data:
        return []
    
    try:
        # Import here to avoid circular imports
        from services.db_operations.device_db import get_devices_by_ips_db
        
        # Extract IPs from monitor data
        ips = [device['ip'] for device in monitor_data if device.get('ip')]
        
        if not ips:
            logger.warning("No IP addresses found in monitor data to enrich")
            return monitor_data
        
        # Get device names from database
        devices_with_names = get_devices_by_ips_db(user_id, router_id, ips)
        
        # Create IP to device name mapping
        ip_to_name = {}
        for device in devices_with_names:
            ip_to_name[str(device.ip)] = {
                'device_name': device.device_name,
                'hostname': device.hostname,
                'manufacturer': device.manufacturer
            }
        
        # Enrich monitor data and filter out devices with less than 10MB total traffic
        enriched_data = []
        for device in monitor_data:
            # Calculate total traffic
            total_traffic = (device.get('download', 0) or 0) + (device.get('upload', 0) or 0)
            
            # Filter out devices with less than 10MB total traffic
            if total_traffic < 10:
                logger.debug(f"Filtering out device {device.get('ip', 'unknown')} with {total_traffic:.2f} MB total traffic (below 10MB threshold)")
                continue
            
            enriched_device = device.copy()
            device_info = ip_to_name.get(device['ip'], {})
            enriched_device.update({
                'device_name': device_info.get('device_name'),
                'hostname': device_info.get('hostname'), 
                'manufacturer': device_info.get('manufacturer')
            })
            enriched_data.append(enriched_device)
        
        logger.info(f"Successfully enriched {len(enriched_data)} devices with names from database (filtered out {len(monitor_data) - len(enriched_data)} devices below 10MB threshold)")
        return enriched_data
        
    except Exception as e:
        logger.error(f"Failed to enrich monitor data with device names: {str(e)}")
        # Return original data if enrichment fails, but still apply 10MB filter
        filtered_data = []
        for device in monitor_data:
            total_traffic = (device.get('download', 0) or 0) + (device.get('upload', 0) or 0)
            if total_traffic >= 10:
                filtered_data.append(device)
        
        logger.info(f"Applied 10MB filter only: {len(filtered_data)} devices remain out of {len(monitor_data)}")
        return filtered_data


@handle_service_errors("get_current_devices_monitor")
def get_current_devices_monitor(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Get current devices monitoring data.
    
    Args:
        user_id: User ID
        router_id: Router ID to get monitor data from
        session_id: Session ID for the command
        
    Returns:
        Tuple of (devices_data_list, error_message)
    """
    logger.info(f"Getting current devices monitor for user {user_id}, router {router_id}")
    
    # Execute the command on the commands server
    devices_data, error = execute_get_current_devices_monitor(router_id, session_id)
    
    if error:
        logger.error(f"Failed to get current devices monitor: {error}")
        return None, error
    
    # Enrich data with device names from database
    enriched_data = _enrich_monitor_data_with_device_names(user_id, router_id, devices_data)
    
    logger.info(f"Successfully retrieved current devices monitor data")
    return enriched_data, None


@handle_service_errors("get_last_week_devices_monitor")
def get_last_week_devices_monitor(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Get last week devices monitoring data.
    
    Args:
        user_id: User ID
        router_id: Router ID to get monitor data from
        session_id: Session ID for the command
        
    Returns:
        Tuple of (devices_data_list, error_message)
    """
    logger.info(f"Getting last week devices monitor for user {user_id}, router {router_id}")
    
    # Execute the command on the commands server
    devices_data, error = execute_get_last_week_devices_monitor(router_id, session_id)
    
    if error:
        logger.error(f"Failed to get last week devices monitor: {error}")
        return None, error
    
    # Enrich data with device names from database
    enriched_data = _enrich_monitor_data_with_device_names(user_id, router_id, devices_data)
    
    logger.info(f"Successfully retrieved last week devices monitor data")
    return enriched_data, None


@handle_service_errors("get_last_month_devices_monitor")
def get_last_month_devices_monitor(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Get last month devices monitoring data.
    
    Args:
        user_id: User ID
        router_id: Router ID to get monitor data from
        session_id: Session ID for the command
        
    Returns:
        Tuple of (devices_data_list, error_message)
    """
    logger.info(f"Getting last month devices monitor for user {user_id}, router {router_id}")
    
    # Execute the command on the commands server
    devices_data, error = execute_get_last_month_devices_monitor(router_id, session_id)
    
    if error:
        logger.error(f"Failed to get last month devices monitor: {error}")
        return None, error
    
    # Enrich data with device names from database
    enriched_data = _enrich_monitor_data_with_device_names(user_id, router_id, devices_data)
    
    logger.info(f"Successfully retrieved last month devices monitor data")
    return enriched_data, None


@handle_service_errors("get_device_monitor_by_mac")
def get_device_monitor_by_mac(user_id: str, router_id: str, session_id: str, mac: str, period: str = "current") -> Tuple[Optional[Dict], Optional[str]]:
    """
    Get monitoring data for a specific device by MAC address.
    
    Args:
        user_id: User ID
        router_id: Router ID to get monitor data from
        session_id: Session ID for the command
        mac: MAC address of the device
        period: Time period (current, week, month)
        
    Returns:
        Tuple of (device_data, error_message)
    """
    logger.info(f"Getting device monitor for MAC {mac} with period {period} for user {user_id}, router {router_id}")
    
    # Validate period parameter
    valid_periods = ["current", "week", "month"]
    if period not in valid_periods:
        error_msg = f"Invalid period '{period}'. Must be one of: {', '.join(valid_periods)}"
        logger.error(error_msg)
        return None, error_msg
    
    # Execute the command on the commands server
    device_data, error = execute_get_device_monitor_by_mac(router_id, session_id, mac, period)
    
    if error:
        logger.error(f"Failed to get device monitor for MAC {mac}: {error}")
        return None, error
    
    # Enrich single device data with names from database
    if device_data and device_data.get('ip'):
        enriched_data = _enrich_monitor_data_with_device_names(user_id, router_id, [device_data])
        if enriched_data:
            device_data = enriched_data[0]
    
    logger.info(f"Successfully retrieved device monitor data for MAC {mac}")
    return device_data, None
