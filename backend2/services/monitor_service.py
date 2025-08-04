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
    
    logger.info(f"Successfully retrieved current devices monitor data")
    return devices_data, None


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
    
    logger.info(f"Successfully retrieved last week devices monitor data")
    return devices_data, None


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
    
    logger.info(f"Successfully retrieved last month devices monitor data")
    return devices_data, None


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
    
    logger.info(f"Successfully retrieved device monitor data for MAC {mac}")
    return device_data, None
