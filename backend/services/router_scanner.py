from utils.ssh_client import ssh_manager
from db.device_repository import upsert_device
from utils.response_helpers import error, success

def scan_network_via_router():
    """
    Uses SSH to retrieve connected devices from the OpenWrt router.
    """
    command = "cat /tmp/dhcp.leases"
    output, error = ssh_manager.execute_command(command)

    if error:
        return error("Failed to fetch connected devices", error)

    connected_devices = []
    for line in output.split("\n"):
        parts = line.split()
        if len(parts) >= 3:
            mac_address = parts[1]
            ip_address = parts[2]
            hostname = parts[3] if len(parts) >= 4 else "Unknown"
            connected_devices.append({
                "ip": ip_address,
                "mac": mac_address,
                "hostname": hostname
            })

    # Save to database
    for device in connected_devices:
        upsert_device(device["ip"], device["mac"], device["hostname"])

    return success(message="Connected devices fetched", data=connected_devices)
