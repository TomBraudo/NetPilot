from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import with_commands_server, handle_commands_errors

# Set up logging
logger = get_logger('services.commands_server_operations.monitor_execute')

base_path = "/api/monitor"

@with_commands_server
@handle_commands_errors("Get Current Devices Monitor")
def execute_get_current_devices_monitor(commands_server, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Execute command to get current devices monitoring data.

    Corresponds to: GET /api/monitor/current
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (devices_data_list, error_message)
    """
    endpoint = f"{base_path}/current"
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "GET", None, None
    )
    
    if error:
        logger.error(f"Failed to get current devices monitor: {error}")
        return None, error
    
    if response_data and isinstance(response_data, list):
        logger.info(f"Successfully retrieved current devices monitor data for {len(response_data)} devices")
        return response_data, None
    
    logger.warning("No current devices monitor data found")
    return [], None


@with_commands_server
@handle_commands_errors("Get Last Week Devices Monitor")
def execute_get_last_week_devices_monitor(commands_server, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Execute command to get last week devices monitoring data.

    Corresponds to: GET /api/monitor/last-week
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (devices_data_list, error_message)
    """
    endpoint = f"{base_path}/last-week"
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "GET", None, None
    )
    
    if error:
        logger.error(f"Failed to get last week devices monitor: {error}")
        return None, error
    
    if response_data and isinstance(response_data, list):
        logger.info(f"Successfully retrieved last week devices monitor data for {len(response_data)} devices")
        return response_data, None
    
    logger.warning("No last week devices monitor data found")
    return [], None


@with_commands_server
@handle_commands_errors("Get Last Month Devices Monitor")
def execute_get_last_month_devices_monitor(commands_server, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Execute command to get last month devices monitoring data.

    Corresponds to: GET /api/monitor/last-month
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (devices_data_list, error_message)
    """
    endpoint = f"{base_path}/last-month"
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "GET", None, None
    )
    
    if error:
        logger.error(f"Failed to get last month devices monitor: {error}")
        return None, error
    
    if response_data and isinstance(response_data, list):
        logger.info(f"Successfully retrieved last month devices monitor data for {len(response_data)} devices")
        return response_data, None
    
    logger.warning("No last month devices monitor data found")
    return [], None


@with_commands_server
@handle_commands_errors("Get Device Monitor by MAC")
def execute_get_device_monitor_by_mac(commands_server, router_id: str, session_id: str, mac: str, period: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to get monitoring data for a specific device by MAC address.

    Corresponds to: GET /api/monitor/device/{mac}?period={period}
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        mac: MAC address of the device
        period: Time period (current, week, month)
        
    Returns:
        Tuple of (device_data, error_message)
    """
    endpoint = f"{base_path}/device/{mac}"
    query_params = {"period": period}
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "GET", query_params, None
    )
    
    if error:
        logger.error(f"Failed to get device monitor for MAC {mac} with period {period}: {error}")
        return None, error
    
    if response_data and isinstance(response_data, dict):
        logger.info(f"Successfully retrieved device monitor data for MAC {mac} with period {period}")
        return response_data, None
    
    logger.warning(f"No device monitor data found for MAC {mac} with period {period}")
    return None, "Device not found or no data available"
