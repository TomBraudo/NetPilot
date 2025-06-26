from utils.ssh_client import ssh_manager
from utils.logging_config import get_logger
from utils.response_helpers import success

logger = get_logger('services.block_ip')

def _get_device_mac_from_router(target_ip):
    """
    Get device MAC address from router's ARP table.
    Upstream validation ensures device exists, so simplified error handling.
    """
    # Get ARP table from router
    arp_output, arp_error = ssh_manager.execute_command("ip neigh show")
    if arp_error:
        raise Exception(f"Failed to get ARP table: {arp_error}")
    
    # Parse ARP table to find MAC for the target IP
    for line in arp_output.split('\n'):
        if target_ip in line and 'lladdr' in line:
            parts = line.split()
            if len(parts) >= 5:
                ip = parts[0]
                mac = parts[4]  # MAC is typically at index 4 in 'ip neigh show' output
                return {"ip": ip, "mac": mac, "hostname": "Unknown"}
    
    # If not found, try ping once and check again (simplified)
    ssh_manager.execute_command(f"ping -c 1 {target_ip}")
    arp_output, _ = ssh_manager.execute_command("ip neigh show")
    for line in arp_output.split('\n'):
        if target_ip in line and 'lladdr' in line:
            parts = line.split()
            if len(parts) >= 5:
                ip = parts[0]
                mac = parts[4]
                return {"ip": ip, "mac": mac, "hostname": "Unknown"}
    
    # If still not found, upstream validation failed - this shouldn't happen
    raise Exception(f"Failed to find MAC for {target_ip} in ARP table")

def block_device_by_ip(target_ip):
    """Block a device by IP address - upstream validation ensures device exists"""
    # Get device MAC from router's ARP table
    device = _get_device_mac_from_router(target_ip)

    commands_block = [
        "uci add_list wireless.@wifi-iface[1].maclist='{mac_address}'",
        "uci set wireless.@wifi-iface[1].macfilter='deny'",
        "uci commit wireless",
        "wifi"
    ]

    # Execute blocking commands
    for cmd in commands_block:
        cmd = cmd.format(mac_address=device['mac'])
        output, error = ssh_manager.execute_command(cmd)
        if error:
            raise Exception(f"Failed to execute command: {cmd}, Error: {error}")

    return success(message=f"Device {target_ip} (MAC {device['mac']}) blocked")

def unblock_device_by_ip(target_ip):
    """Unblock a device by IP address - upstream validation ensures device exists"""
    # Get device MAC from router's ARP table
    device = _get_device_mac_from_router(target_ip)

    commands_unblock = [
        "uci del_list wireless.@wifi-iface[1].maclist='{mac_address}'",
        "uci commit wireless",
        "wifi"
    ]

    # Execute unblocking commands
    for cmd in commands_unblock:
        cmd = cmd.format(mac_address=device['mac'])
        output, error = ssh_manager.execute_command(cmd)
        if error:
            raise Exception(f"Failed to execute command: {cmd}, Error: {error}")

    return success(message=f"Device {target_ip} (MAC {device['mac']}) unblocked")

def get_blocked_devices():
    """Get a list of all currently blocked devices"""
    # Get the list of blocked MAC addresses
    output, error = ssh_manager.execute_command("uci get wireless.@wifi-iface[1].maclist")
    if error:
        # If no maclist configured, return empty list
        if "Entry not found" in error or "uci: Entry not found" in error:
            return success(data=[])
        raise Exception(f"Failed to get blocked devices: {error}")

    # Parse the output
    blocked_macs = output.strip().split() if output.strip() else []
    
    # Return simplified device info
    blocked_devices = []
    for mac in blocked_macs:
        blocked_devices.append({
            "ip": "Unknown",  # Reverse lookup not needed for commands-server
            "mac": mac,
            "hostname": "Unknown"
        })

    return success(data=blocked_devices)
