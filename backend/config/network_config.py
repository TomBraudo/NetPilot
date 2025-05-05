import os
from utils.ssh_client import ssh_manager

# Get router information once at startup
def get_router_info():
    try:
        router_mac_cmd = "cat /sys/class/net/br-lan/address 2>/dev/null || ifconfig br-lan | grep -o -E '([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}'"
        router_mac, _ = ssh_manager.execute_command(router_mac_cmd)
        
        return {
            "ip": "192.168.1.1",  # Default router IP
            "mac": router_mac.strip().lower() if router_mac else None
        }
    except:
        return {
            "ip": "192.168.1.1",
            "mac": None
        }

# Router info - initialize once
ROUTER_INFO = get_router_info() 