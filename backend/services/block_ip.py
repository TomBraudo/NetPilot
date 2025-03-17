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
        return {"success": "No devices are currently blocked."}

    # Retrieve DHCP leases to match MACs with IPs and hostnames
    command_get_dhcp = "cat /tmp/dhcp.leases"
    dhcp_output, error = ssh_manager.execute_command(command_get_dhcp)

    if error:
        return {"error": f"Failed to fetch DHCP leases: {error}"}

    # Parse DHCP leases to map MAC -> IP & Hostname
    dhcp_map = {}
    for line in dhcp_output.split("\n"):
        parts = line.split()
        if len(parts) >= 4:  # Format: <lease_time> <IP> <MAC> <Hostname>
            lease_ip = parts[1]
            lease_mac = parts[2].lower()  # Normalize MAC address
            lease_hostname = parts[3] if len(parts) > 3 else "Unknown"
            dhcp_map[lease_mac] = {"ip": lease_ip, "hostname": lease_hostname}

    # Compile list of blocked devices with IPs & Hostnames
    for mac in blocked_macs:
        mac_lower = mac.lower()
        if mac_lower in dhcp_map:
            blocked_devices.append({
                "ip": dhcp_map[mac_lower]["ip"],
                "mac": mac,
                "hostname": dhcp_map[mac_lower]["hostname"]
            })
        else:
            blocked_devices.append({"ip": "Unknown", "mac": mac, "hostname": "Unknown"})

    return {"blocked_devices": blocked_devices}
