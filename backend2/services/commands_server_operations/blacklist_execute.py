"""
Blacklist Commands Server Operations

This service handles all router command executions for blacklist functionality.
It provides command execution for blacklist operations including mode control,
device management, and rate limiting through the commands server.
All functions return (result, error) tuple format.
"""

from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import with_commands_server, handle_commands_errors

logger = get_logger('services.commands_server_operations.blacklist_execute')

base_path = "/api/blacklist"

@with_commands_server
@handle_commands_errors("Get blacklist devices")
def execute_get_blacklist(commands_server, router_id: str, session_id: str) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Execute command to get the current list of blacklisted device IP addresses from router.
    
    Corresponds to: GET /api/blacklist
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (list_of_ip_addresses, error_message)
    """
    endpoint = f"{base_path}"
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "GET", None, None
    )
    
    if error:
        return None, error
    
    if response_data:
        # Extract IP addresses from response
        devices = response_data.get('devices', [])
        ip_addresses = [device.get('ip') for device in devices if device.get('ip')]
        logger.info(f"Retrieved {len(ip_addresses)} blacklisted devices from router {router_id}")
        return ip_addresses, None
    
    return None, "Failed to retrieve blacklist from router"


@with_commands_server
@handle_commands_errors("Add device to blacklist")
def execute_add_device_to_blacklist(commands_server, router_id: str, session_id: str, ip_address: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to add a device to the blacklist on router.
    
    Corresponds to: POST /api/blacklist/add
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        ip_address: Device IP address to blacklist
        
    Returns:
        Tuple of (success_response, error_message)
    """
    endpoint = f"{base_path}/add"
    body = {"ip": ip_address}
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "POST", None, body
    )
    
    if error:
        return None, error
    
    if response_data:
        logger.info(f"Added device {ip_address} to blacklist on router {router_id}")
        return response_data, None
    
    return None, f"Failed to add device {ip_address} to blacklist on router"


@with_commands_server
@handle_commands_errors("Remove device from blacklist")
def execute_remove_device_from_blacklist(commands_server, router_id: str, session_id: str, ip_address: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to remove a device from the blacklist on router.
    
    Corresponds to: POST /api/blacklist/remove
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        ip_address: Device IP address to remove from blacklist
        
    Returns:
        Tuple of (success_response, error_message)
    """
    endpoint = f"{base_path}/remove"
    body = {"ip": ip_address}
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "POST", None, body
    )
    
    if error:
        return None, error
    
    if response_data:
        logger.info(f"Removed device {ip_address} from blacklist on router {router_id}")
        return response_data, None
    
    return None, f"Failed to remove device {ip_address} from blacklist on router"


@with_commands_server
@handle_commands_errors("Set blacklist rate limit")
def execute_set_blacklist_rate_limit(commands_server, router_id: str, session_id: str, rate_mbps: int) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to set the bandwidth limit rate for blacklisted devices.
    
    Corresponds to: POST /api/blacklist/limit-rate
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        rate_mbps: Bandwidth rate in Mbps
        
    Returns:
        Tuple of (success_response, error_message)
    """
    endpoint = f"{base_path}/limit-rate"
    body = {"rate": rate_mbps}
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "POST", None, body
    )
    
    if error:
        return None, error
    
    if response_data:
        logger.info(f"Set blacklist rate limit to {rate_mbps} Mbps on router {router_id}")
        return response_data, None
    
    return None, f"Failed to set blacklist rate limit to {rate_mbps} Mbps on router"


@with_commands_server
@handle_commands_errors("Activate blacklist mode")
def execute_activate_blacklist_mode(commands_server, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to activate blacklist mode on router.
    In blacklist mode, only blacklisted devices get limited access.
    
    Corresponds to: POST /api/blacklist/mode
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (success_response, error_message)
    """
    endpoint = f"{base_path}/mode"
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "POST", None, None
    )
    
    if error:
        return None, error
    
    if response_data:
        logger.info(f"Activated blacklist mode on router {router_id}")
        return response_data, None
    
    return None, f"Failed to activate blacklist mode on router {router_id}"


@with_commands_server
@handle_commands_errors("Deactivate blacklist mode")
def execute_deactivate_blacklist_mode(commands_server, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to deactivate blacklist mode on router.
    Returns to normal network access for all devices.
    
    Corresponds to: DELETE /api/blacklist/mode
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (success_response, error_message)
    """
    endpoint = f"{base_path}/mode"
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "DELETE", None, None
    )
    
    if error:
        return None, error
    
    if response_data:
        logger.info(f"Deactivated blacklist mode on router {router_id}")
        return response_data, None
    
    return None, f"Failed to deactivate blacklist mode on router {router_id}"
