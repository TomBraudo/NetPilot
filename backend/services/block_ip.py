import subprocess
from utils.ssh_client import ssh_manager
from utils.logging_config import get_logger
from db.device_repository import get_device_by_ip, get_device_by_mac

logger = get_logger('services.block_ip')

def block_mac_address(target_ip):
    """
    Blocks a device by IP address (translates IP to MAC and blocks it)
    """
    # Get device info from database
    device = get_device_by_ip(target_ip)
    if not device or not device.get('mac'):
        raise ValueError(f"IP {target_ip} not found in network.")

    commands_block = [
        "uci add_list wireless.@wifi-iface[1].maclist='{mac_address}'",
        "uci set wireless.@wifi-iface[1].macfilter='deny'",
        "uci commit wireless",
        "wifi"
    ]

    # Block the MAC address
    for cmd in commands_block:
        cmd = cmd.format(mac_address=device['mac'])
        ssh_manager.execute_command(cmd)

    return {"status": "success", "message": f"Device with IP {target_ip} (MAC {device['mac']}) is blocked."}

def unblock_mac_address(target_ip):
    """
    Unblocks a device by removing its MAC address from the blocklist.
    """
    # Get device info from device service
    device = get_device_by_ip(target_ip)
    if not device or not device.get('mac'):
        raise ValueError(f"IP {target_ip} not found in network.")

    commands_unblock = [
        "uci del_list wireless.@wifi-iface[1].maclist='{mac_address}'",
        "uci commit wireless",
        "wifi"
    ]

    # Unblock the MAC address
    for cmd in commands_unblock:
        cmd = cmd.format(mac_address=device['mac'])
        ssh_manager.execute_command(cmd)

    return {"status": "success", "message": f"Device with IP {target_ip} (MAC {device['mac']}) is unblocked."}

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
        return {"status": "success", "message": "No devices are currently blocked."}

    # Get device information from device service
    for mac in blocked_macs:
        try:
            device = get_device_by_mac(mac)
            blocked_devices.append({
                "ip": device.get('ip', 'Unknown'),
                "mac": mac,
                "hostname": device.get('hostname', 'Unknown')
            })
        except ValueError:
            blocked_devices.append({
                "ip": "Unknown",
                "mac": mac,
                "hostname": "Unknown"
            })

    return {"status": "success", "data": blocked_devices}
