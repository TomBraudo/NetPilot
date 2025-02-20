import subprocess
from utils.ssh_client import ssh_manager

def block_mac_address(target_ip):
    """
    Blocks a device by IP address (translates IP to MAC and blocks it).
    """
    command_get_mac = "cat /tmp/dhcp.leases"
    commands_block = [
        "uci add_list wireless.@wifi-iface[1].maclist='{mac_address}'",
        "uci set wireless.@wifi-iface[1].macfilter='deny'",
        "uci commit wireless",
        "wifi"
    ]

    output, error = ssh_manager.execute_command(command_get_mac)
    
    if error:
        return {"error": f"Failed to fetch connected devices: {error}"}

    # Find MAC address of the target IP
    mac_address = None
    for line in output.split("\n"):
        parts = line.split()
        if len(parts) >= 3 and parts[2] == target_ip:
            mac_address = parts[1]
            break

    if not mac_address:
        return {"error": f"IP {target_ip} not found in connected devices."}

    # Block the MAC address
    for cmd in commands_block:
        cmd = cmd.format(mac_address=mac_address)
        ssh_manager.execute_command(cmd)

    return {"success": f"Device with IP {target_ip} (MAC {mac_address}) is blocked."}



def unblock_mac_address(target_ip):
    """
    Unblocks a device by removing its MAC address from the blocklist.
    """
    command_get_mac = "cat /tmp/dhcp.leases"
    commands_unblock = [
        "uci del_list wireless.@wifi-iface[1].maclist='{mac_address}'",
        "uci commit wireless",
        "wifi"
    ]

    output, error = ssh_manager.execute_command(command_get_mac)
    
    if error:
        return {"error": f"Failed to fetch connected devices: {error}"}

    # Find MAC address of the target IP
    mac_address = None
    for line in output.split("\n"):
        parts = line.split()
        if len(parts) >= 3 and parts[2] == target_ip:
            mac_address = parts[1]
            break

    if not mac_address:
        return {"error": f"IP {target_ip} not found in connected devices."}

    # Unblock the MAC address
    for cmd in commands_unblock:
        cmd = cmd.format(mac_address=mac_address)
        ssh_manager.execute_command(cmd)

    return {"success": f"Device with IP {target_ip} (MAC {mac_address}) has been unblocked."}
