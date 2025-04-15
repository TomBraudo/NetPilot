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
    Uses SSH to retrieve ACTIVE connected devices from the OpenWrt router.
    Combines ARP table with DHCP lease information for accurate results.
    """
    # Get DHCP leases for hostname information
    dhcp_command = "cat /tmp/dhcp.leases"
    dhcp_output, dhcp_error = ssh_manager.execute_command(dhcp_command)

    if dhcp_error:
        return error("Failed to fetch DHCP leases", dhcp_error)

    # Create a lookup dictionary from DHCP leases
    dhcp_info = {}
    for line in dhcp_output.split("\n"):
        parts = line.split()
        if len(parts) >= 4:
            mac = parts[1].lower()
            ip = parts[2]
            raw_hostname = parts[3] if len(parts) >= 4 else "Unknown"
            hostname = raw_hostname if raw_hostname not in ["*", "Unknown"] else "Unknown"
            dhcp_info[mac] = {"ip": ip, "hostname": hostname}

    # Get ARP table to find ACTIVE devices
    arp_command = "ip neigh show | grep -v FAILED"
    arp_output, arp_error = ssh_manager.execute_command(arp_command)

    if arp_error:
        return error("Failed to fetch ARP table", arp_error)

    # Process active devices from ARP table
    connected_devices = []
    for line in arp_output.split("\n"):
        if not line.strip():
            continue
            
        parts = line.split()
        if len(parts) >= 4:
            ip = parts[0]
            mac_idx = next((i for i, part in enumerate(parts) if ":" in part), -1)
            if mac_idx == -1:
                continue
                
            mac = parts[mac_idx].lower()
            state = parts[-1]
            
            # Only include devices in REACHABLE or STALE state (recently active)
            if state in ["REACHABLE", "STALE", "DELAY"]:
                # Get hostname from DHCP info if available
                hostname = dhcp_info.get(mac, {}).get("hostname", "Unknown")
                vendor = get_mac_vendor(mac)
                
                connected_devices.append({
                    "ip": ip,
                    "mac": mac,
                    "hostname": hostname,
                    "vendor": vendor
                })

    # Register active devices in database
    for device in connected_devices:
        register_device(device["ip"], device["mac"], device["hostname"])

    return success(message="Active devices fetched", data=connected_devices)
