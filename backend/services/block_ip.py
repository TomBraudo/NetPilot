import subprocess
from utils.ssh_client import ssh_manager
from utils.response_helpers import success, error
from db.device_repository import get_mac_from_ip

def block_mac_address(target_ip):
    """
    Blocks a device by IP address (translates IP to MAC and blocks it)
    """
    # Get MAC address from database
    mac_address = get_mac_from_ip(target_ip)
    if not mac_address:
        return error(f"IP {target_ip} not found in network.")

    commands_block = [
        "uci add_list wireless.@wifi-iface[1].maclist='{mac_address}'",
        "uci set wireless.@wifi-iface[1].macfilter='deny'",
        "uci commit wireless",
        "wifi"
    ]

    # Block the MAC address
    for cmd in commands_block:
        cmd = cmd.format(mac_address=mac_address)
        ssh_manager.execute_command(cmd)

    return success(f"Device with IP {target_ip} (MAC {mac_address}) is blocked.")

def unblock_mac_address(target_ip):
    """
    Unblocks a device by removing its MAC address from the blocklist.
    """
    # Get MAC address from database
    mac_address = get_mac_from_ip(target_ip)
    if not mac_address:
        return error(f"IP {target_ip} not found in network.")

    commands_unblock = [
        "uci del_list wireless.@wifi-iface[1].maclist='{mac_address}'",
        "uci commit wireless",
        "wifi"
    ]

    # Unblock the MAC address
    for cmd in commands_unblock:
        cmd = cmd.format(mac_address=mac_address)
        ssh_manager.execute_command(cmd)

    return success(f"Device with IP {target_ip} (MAC {mac_address}) is unblocked.")

def get_blocked_devices():
    """
    Retrieves a list of all blocked devices (Wi-Fi & LAN) with IP, MAC, and hostname.
    """
    blocked_macs = set()
    blocked_devices = []

    # Retrieve Wi-Fi blocked MACs
    command_get_blocked_wifi = "uci show wireless | grep maclist"
    wifi_output, error = ssh_manager.execute_command(command_get_blocked_wifi)
    
    if not error and wifi_output.strip():
        for line in wifi_output.split("\n"):
            parts = line.split("=")
            if len(parts) == 2:
                macs = parts[1].strip().replace("'", "").split()
                blocked_macs.update(macs)

    # Retrieve MACs blocked at the firewall level
    command_get_blocked_fw = "iptables -L | grep MAC"
    fw_output, error = ssh_manager.execute_command(command_get_blocked_fw)

    if not error and fw_output.strip():
        for line in fw_output.split("\n"):
            parts = line.split()
            for i, part in enumerate(parts):
                if part.lower() == "mac":
                    blocked_macs.add(parts[i+2])  # MAC address is the next value

    if not blocked_macs:
        return success("No devices are currently blocked.")

    # Get device information from database
    from db.device_repository import get_device_by_mac
    for mac in blocked_macs:
        device = get_device_by_mac(mac)
        if device:
            blocked_devices.append({
                "ip": device.get('ip', 'Unknown'),
                "mac": mac,
                "hostname": device.get('hostname', 'Unknown')
            })
        else:
            blocked_devices.append({
                "ip": "Unknown",
                "mac": mac,
                "hostname": "Unknown"
            })

    return success(data=blocked_devices)
