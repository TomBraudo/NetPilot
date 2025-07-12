# Stub implementation for network service
# This is a placeholder that returns mock data

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

def scan_network_via_router():
    """Scan the network via router"""
    return {
        "devices": [
            {"ip": "192.168.1.1", "mac": "00:11:22:33:44:55", "hostname": "router"},
            {"ip": "192.168.1.100", "mac": "AA:BB:CC:DD:EE:FF", "hostname": "device-1"},
            {"ip": "192.168.1.101", "mac": "11:22:33:44:55:66", "hostname": "device-2"}
        ],
        "total_devices": 3
    }, None 