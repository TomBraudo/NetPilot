from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import with_commands_server, handle_commands_errors

# Fix the logger name
logger = get_logger('services.commands_server_operations.settings_execute')

base_path = "/api/wifi"

@with_commands_server
@handle_commands_errors("Get WiFi Name")
def execute_get_wifi_name(commands_server, router_id: str, session_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Execute command to get the WiFi's name.

    Corresponds to: GET /api/wifi/ssid
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (ssid, error_message)
    """
    endpoint = f"{base_path}/ssid"
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "GET", None, None
    )
    
    if error:
        return None, error
    
    if response_data:
        ssid = response_data.get('ssid')
        logger.info(f"Retrieved SSID '{ssid}' for router {router_id}")
        return ssid, None

    return None, "Failed to retrieve SSID from router"

@with_commands_server
@handle_commands_errors("Update WiFi Name")
def execute_update_wifi_name(commands_server, router_id: str, session_id: str, wifi_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Execute command to update the WiFi's name.

    Corresponds to: POST /api/wifi/ssid
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        wifi_name: New WiFi name to set
        
    Returns:
        Tuple of (success_message, error_message)
    """
    endpoint = f"{base_path}/ssid"
    
    request_body = {
        "ssid": wifi_name
    }
    
    logger.info(f"Updating WiFi SSID to '{wifi_name}' for router {router_id}")
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "POST", None, request_body
    )
    
    if error:
        return None, error
    
    if response_data:
        logger.info(f"Successfully updated SSID to '{wifi_name}' for router {router_id}")
        return f"WiFi name updated to '{wifi_name}'", None

    return None, "Failed to update SSID on router"


@with_commands_server
@handle_commands_errors("Set WiFi Password")
def execute_set_wifi_password(commands_server, router_id: str, session_id: str, wifi_password: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Execute command to set the WiFi password.

    Corresponds to: POST /api/wifi/password
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        wifi_password: New WiFi password to set
        
    Returns:
        Tuple of (success_message, error_message)
    """
    endpoint = f"{base_path}/password"
    
    request_body = {
        "password": wifi_password
    }
    
    logger.info(f"Setting WiFi password for router {router_id}")
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "POST", None, request_body
    )
    
    if error:
        return None, error
    
    if response_data:
        logger.info(f"Successfully set WiFi password for router {router_id}")
        return "WiFi password updated successfully", None

    return None, "Failed to update WiFi password on router"