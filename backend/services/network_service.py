"""
Network Service - Simplified commands-server routing
Maps API endpoints to appropriate SSH-based services
"""
from services.block_ip import (
    get_blocked_ips,
    block_ip,
    unblock_ip
)
from services.router_scanner import get_connected_devices
from services.reset_rules import reset_all_rules
from utils.response_helpers import success

def get_blocked_devices_list():
    """Get list of blocked devices"""
    return get_blocked_ips()

def block_device(ip):
    """Block a device by IP"""
    return block_ip(ip)

def unblock_device(ip):
    """Unblock a device by IP"""
    return unblock_ip(ip)

def reset_network_rules():
    """Reset all network rules"""
    return reset_all_rules()

def scan_network():
    """Scan network - simplified to use router scanning"""
    return get_connected_devices()

def scan_network_via_router():
    """Scan network via router"""
    return get_connected_devices()

def run_ookla_speedtest():
    """Run speedtest - simplified implementation"""
    # For commands-server, we'll use a simple placeholder
    # The actual speedtest implementation would be router-based
    return success(message="Speedtest not implemented in commands-server mode") 