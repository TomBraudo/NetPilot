# Stub implementation for network service
# This is a placeholder that returns mock data

from flask import g
from managers.commands_server_manager import commands_server_manager
from utils.logging_config import get_logger

logger = get_logger('services.network')

def get_blocked_devices_list():
    """Get all currently blocked devices"""
    return [
        {"ip": "192.168.1.100", "mac": "00:11:22:33:44:55", "hostname": "blocked-device-1"},
        {"ip": "192.168.1.101", "mac": "AA:BB:CC:DD:EE:FF", "hostname": "blocked-device-2"}
    ], None

def block_device(ip):
    """Block a device by IP address"""
    if not ip:
        return None, "IP address is required."
    return f"Device {ip} blocked successfully.", None

def unblock_device(ip):
    """Unblock a device by IP address"""
    if not ip:
        return None, "IP address is required."
    return f"Device {ip} unblocked successfully.", None

def reset_network_rules():
    """Reset all network rules"""
    return "All network rules reset successfully.", None

def scan_network(router_id):
    """
    Scan the network via router to find connected devices.
    
    Args:
        router_id (str): The router's unique ID
        
    Returns:
        tuple: (result, error) where result is the list of devices or None, error is error message or None
    """
    # Get session_id from Flask's g object (set by authentication middleware)
    session_id = getattr(g, 'user_id', None)
    if not session_id:
        return None, "User not authenticated"
    
    if not router_id:
        return None, "router_id is required"
    
    try:
        # Call the commands server with the scan endpoint
        response, error = commands_server_manager.execute_router_command(
            router_id=router_id,
            session_id=session_id,
            endpoint="/api/network/scan",
            method="GET",
            query_params={
                "sessionId": session_id,
                "routerId": router_id
            }
        )
        
        if error:
            logger.error(f"Network scan failed: {error}")
            return None, error
        
        # Unpack the response - expect an array of devices
        if response and isinstance(response, dict):
            # Check if response has the expected structure
            if 'success' in response and response['success']:
                # Extract data from the response
                data = response.get('data', [])
                if isinstance(data, list):
                    return data, None
                else:
                    return None, "Invalid response format: expected array of devices"
            else:
                # Handle error response
                error_msg = response.get('error', 'Unknown error from commands server')
                return None, error_msg
        elif isinstance(response, list):
            # Direct array response
            return response, None
        else:
            return None, "Invalid response format from commands server"
            
    except Exception as e:
        error_msg = f"Unexpected error during network scan: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg 