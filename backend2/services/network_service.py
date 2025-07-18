# Stub implementation for network service
# This is a placeholder that returns mock data

from utils.command_server_proxy import send_command_server_request

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

def scan_network_via_router(router_id):
    """
    Scan the network via router by proxying to the Command Server.
    Args:
        router_id (str): The router's unique ID
    Returns:
        tuple: (result, error) where result is the device list or None, error is error message or None
    """
    # The Command Server expects routerId as a query param
    payload = {"routerId": router_id}
    response = send_command_server_request("/network/scan", method="GET", payload=payload)
    if response.get("success"):
        # The Command Server should return the device list in response["data"]
        return response["data"], None
    else:
        return None, response.get("error", "Unknown error from Command Server") 