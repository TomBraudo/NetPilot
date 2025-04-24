import socket
import requests
import time
from utils.ssh_client import ssh_manager
from utils.response_helpers import error, success
from db.device_repository import register_device

def get_mac_vendor(mac):
    """
    Queries macvendors.com to get the vendor for a given MAC address.
    Returns 'Unknown Vendor' if request fails.
    """
    try:
        time.sleep(0.5)  # Rate limit to avoid overwhelming the API
        response = requests.get(f"https://api.macvendors.com/{mac}", timeout=3)
        if response.status_code == 200:
            return response.text.strip()
    except requests.RequestException as e:
        print(f"[WARN] Vendor lookup failed for {mac}: {e}")
    return "Unknown Vendor"

def scan_network_via_router():
    """
    Uses SSH to retrieve connected devices from the OpenWrt router.
    Fetches vendor info from macvendors.com.
    """
    command = "cat /tmp/dhcp.leases"
    output, exec_error = ssh_manager.execute_command(command)

    if exec_error:
        return error("Failed to fetch connected devices", exec_error)

    connected_devices = []
    connected_devices.append({
        "ip": "192.168.1.1",
        "mac": "00:00:00:00:00:00",
        "hostname": "Router",
        "vendor": "Router Manufacturer"
    })
    
    for line in output.split("\n"):
        parts = line.split()
        if len(parts) >= 3:
            mac_address = parts[1]
            ip_address = parts[2]
            raw_hostname = parts[3] if len(parts) >= 4 else "Unknown"

            hostname = raw_hostname if raw_hostname not in ["*", "Unknown"] else "Unknown"
            vendor = get_mac_vendor(mac_address)

            connected_devices.append({
                "ip": ip_address,
                "mac": mac_address,
                "hostname": hostname,
                "vendor": vendor
            })

    for device in connected_devices:
        register_device(device["ip"], device["mac"], device["hostname"])

    return success(message="Connected devices fetched", data=connected_devices)
