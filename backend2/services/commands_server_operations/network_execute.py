"""
Network Commands Server Operations

This service handles all router command executions for network functionality.
It provides command execution for network operations including network scanning
through the commands server.
All functions return (result, error) tuple format.
"""

from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import with_commands_server, handle_commands_errors

logger = get_logger('services.commands_server_operations.network_execute')

base_path = "/api/network"

@with_commands_server
@handle_commands_errors("Scan network")
def execute_scan_network(commands_server, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Execute command to scan the network via router to find connected devices.
    
    Corresponds to: GET /api/network/scan
    Expected Query Params: ?sessionId=<session_id>&routerId=<router_id>
    Expected Response Body: Array of device objects with ip, mac, hostname properties
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (list_of_devices, error_message)
    """
    endpoint = f"{base_path}/scan"
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "GET", None, None
    )
    
    # If there was a communication error
    if error:
        return None, error
    
    # If no response received
    if not response_data:
        return None, "No response from commands server"
    
    # The manager already unpacked the response - if we have response_data and no error, it was successful
    if response_data and not error:
        # The response_data is already the device list (data section from commands server)
        devices = response_data if isinstance(response_data, list) else []
        logger.info(f"Network scan completed successfully for router {router_id}, found {len(devices)} devices")
        return devices, None
    else:
        # This should not happen as error would be set, but keeping for safety
        return None, "Scan network failed: 'list' object has no attribute 'get'"
