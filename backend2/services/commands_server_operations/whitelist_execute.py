"""
Whitelist Commands Server Operations

This service handles all router command executions for whitelist functionality.
It provides command execution for whitelist operations including mode control,
device management, and rate limiting through the commands server.
All functions return (result, error) tuple format.
"""

from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import with_commands_server, handle_commands_errors

logger = get_logger('services.commands_server_operations.whitelist_execute')

base_path = "/api/whitelist"

@with_commands_server
@handle_commands_errors("Get whitelist devices")
def execute_get_whitelist(commands_server, router_id: str, session_id: str) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Execute command to get the current list of whitelisted device IP addresses from router.
    
    Corresponds to: GET /api/whitelist
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (list_of_ip_addresses, error_message)
    """
    endpoint = f"{base_path}"
    query_params = {"router_id": router_id, "session_id": session_id}
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "GET", query_params, None
    )
    
    if response_data and response_data.get('success'):
        # Extract IP addresses from response
        devices = response_data.get('data', {}).get('devices', [])
        ip_addresses = [device.get('ip') for device in devices if device.get('ip')]
        logger.info(f"Retrieved {len(ip_addresses)} whitelisted devices from router {router_id}")
        return ip_addresses, None
    
    return None, error or "Failed to retrieve whitelist from router"


@with_commands_server
@handle_commands_errors("Add device to whitelist")
def execute_add_device_to_whitelist(commands_server, router_id: str, session_id: str, ip_address: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to add a device to the whitelist on router.
    
    Corresponds to: POST /api/whitelist/add
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        ip_address: Device IP address to whitelist
        
    Returns:
        Tuple of (success_response, error_message)
    """
    endpoint = f"{base_path}/add"
    query_params = {"router_id": router_id, "session_id": session_id}
    body = {"ip": ip_address}
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "POST", query_params, body
    )
    
    if response_data and response_data.get('success'):
        logger.info(f"Added device {ip_address} to whitelist on router {router_id}")
        return response_data, None
    
    return None, error or f"Failed to add device {ip_address} to whitelist on router"


@with_commands_server
@handle_commands_errors("Remove device from whitelist")
def execute_remove_device_from_whitelist(commands_server, router_id: str, session_id: str, ip_address: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to remove a device from the whitelist on router.
    
    Corresponds to: POST /api/whitelist/remove
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        ip_address: Device IP address to remove from whitelist
        
    Returns:
        Tuple of (success_response, error_message)
    """
    endpoint = f"{base_path}/remove"
    query_params = {"router_id": router_id, "session_id": session_id}
    body = {"ip": ip_address}
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "POST", query_params, body
    )
    
    if response_data and response_data.get('success'):
        logger.info(f"Removed device {ip_address} from whitelist on router {router_id}")
        return response_data, None
    
    return None, error or f"Failed to remove device {ip_address} from whitelist on router"


@with_commands_server
@handle_commands_errors("Set whitelist rate limit")
def execute_set_whitelist_rate_limit(commands_server, router_id: str, session_id: str, rate_mbps: int) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to set the bandwidth limit rate for whitelisted devices.
    
    Corresponds to: POST /api/whitelist/limit-rate
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        rate_mbps: Bandwidth rate in Mbps
        
    Returns:
        Tuple of (success_response, error_message)
    """
    endpoint = f"{base_path}/limit-rate"
    query_params = {"router_id": router_id, "session_id": session_id}
    body = {"rate": rate_mbps}
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "POST", query_params, body
    )
    
    if response_data and response_data.get('success'):
        logger.info(f"Set whitelist rate limit to {rate_mbps} Mbps on router {router_id}")
        return response_data, None
    
    return None, error or f"Failed to set whitelist rate limit to {rate_mbps} Mbps on router"


@with_commands_server
@handle_commands_errors("Activate whitelist mode")
def execute_activate_whitelist_mode(commands_server, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to activate whitelist mode on router.
    In whitelist mode, only whitelisted devices get unlimited access.
    
    Corresponds to: POST /api/whitelist/mode
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (success_response, error_message)
    """
    endpoint = f"{base_path}/mode"
    query_params = {"router_id": router_id, "session_id": session_id}
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "POST", query_params, None
    )
    
    if response_data and response_data.get('success'):
        logger.info(f"Activated whitelist mode on router {router_id}")
        return response_data, None
    
    return None, error or f"Failed to activate whitelist mode on router {router_id}"


@with_commands_server
@handle_commands_errors("Deactivate whitelist mode")
def execute_deactivate_whitelist_mode(commands_server, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to deactivate whitelist mode on router.
    Returns to normal network access for all devices.
    
    Corresponds to: DELETE /api/whitelist/mode
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (success_response, error_message)
    """
    endpoint = f"{base_path}/mode"
    query_params = {"router_id": router_id, "session_id": session_id}
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "DELETE", query_params, None
    )
    
    if response_data and response_data.get('success'):
        logger.info(f"Deactivated whitelist mode on router {router_id}")
        return response_data, None
    
    return None, error or f"Failed to deactivate whitelist mode on router {router_id}"
