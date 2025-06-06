import requests
import time
import re
from utils.ssh_client import ssh_manager
from utils.response_helpers import success
from db.device_repository import register_device
import ipaddress
from utils.logging_config import get_logger

logger = get_logger('services.router_scanner')

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
    Only returns devices in the router's subnet, and includes the router itself.
    """
    # Get router IP and subnet
    router_ip = ssh_manager.router_ip
    # Assume /24 subnet for typical home routers; adjust if you want to detect dynamically
    router_network = ipaddress.ip_network(router_ip + '/24', strict=False)

    # Get DHCP leases for hostname information
    dhcp_command = "cat /tmp/dhcp.leases"
    dhcp_output, dhcp_error = ssh_manager.execute_command(dhcp_command)

    if dhcp_error:
        raise Exception("Failed to fetch DHCP leases")

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
    
    # Log DHCP scan results
    logger.info(f"DHCP leases found: {len(dhcp_info)} devices")

    # Get ARP table to find ACTIVE devices
    arp_command = "ip neigh show | grep -v FAILED"
    arp_output, arp_error = ssh_manager.execute_command(arp_command)

    if arp_error:
        raise Exception("Failed to fetch ARP table")
    
    # Log basic ARP scan info
    logger.info(f"ARP scan completed, processing {len(arp_output.split(chr(10)))} entries")

    # Process active devices from ARP table - group by MAC address
    device_map = {}
    for line in arp_output.split("\n"):
        if not line.strip():
            continue
            
        parts = line.split()
        if len(parts) >= 4:
            ip = parts[0]
            mac_idx = next((i for i, part in enumerate(parts) if re.match(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', part)), -1)
            if mac_idx == -1:
                continue
                
            mac = parts[mac_idx].lower()
            state = parts[-1]
            
            # Include devices in active states (connected but may be in various ARP states)
            if state in ["REACHABLE", "DELAY", "PROBE"]:
                # If this MAC is already in our map, we'll update it
                if mac not in device_map:
                    device_map[mac] = {
                        "mac": mac,
                        "ipv4": None,
                        "ipv6": [],
                        "hostname": "Unknown",
                        "vendor": None
                    }
                
                # Prioritize IPv4 addresses and DHCP hostnames
                if ":" not in ip:  # This is an IPv4 address
                    # Prioritize subnet IPs over link-local IPs
                    current_ip = device_map[mac]["ipv4"]
                    try:
                        # Check if this IP is in the router's subnet
                        is_in_subnet = ipaddress.ip_address(ip) in router_network
                        current_is_in_subnet = current_ip and ipaddress.ip_address(current_ip) in router_network
                        
                        # Only update if we don't have an IP yet, or if the new IP is in subnet and current isn't
                        if not current_ip or (is_in_subnet and not current_is_in_subnet):
                            device_map[mac]["ipv4"] = ip
                            logger.debug(f"Prioritized subnet IP for {mac}: {current_ip} -> {ip}")
                    except ValueError:
                        # If IP parsing fails, just use it if we don't have one yet
                        if not current_ip:
                            device_map[mac]["ipv4"] = ip
                else:  # This is an IPv6 address
                    device_map[mac]["ipv6"].append(ip)
                
                # Get hostname from DHCP info if available
                if mac in dhcp_info and device_map[mac]["hostname"] == "Unknown":
                    device_map[mac]["hostname"] = dhcp_info[mac]["hostname"]

    # Add devices from DHCP leases that weren't found in ARP table (fallback)
    for mac, dhcp_device in dhcp_info.items():
        if mac not in device_map:
            # Check if IP is in our subnet
            try:
                if ipaddress.ip_address(dhcp_device["ip"]) in router_network:
                    device_map[mac] = {
                        "mac": mac,
                        "ipv4": dhcp_device["ip"],
                        "ipv6": [],
                        "hostname": dhcp_device["hostname"],
                        "vendor": None
                    }
                    logger.debug(f"Added DHCP-only device: {mac} -> {dhcp_device['ip']}")
            except ValueError:
                continue

    # Convert the device map to a list and add vendor information
    connected_devices = []
    
    # Add the router itself
    connected_devices.append({
        "ip": router_ip,
        "mac": "router",  # You could fetch the router's MAC if needed
        "hostname": "Router",
        "vendor": "Router"
    })

    for mac, device in device_map.items():
        # Only include devices that have an IPv4 address in the router's subnet
        if device["ipv4"]:
            try:
                if ipaddress.ip_address(device["ipv4"]) not in router_network:
                    continue
            except ValueError:
                continue
            # Get vendor info once per device
            if not device["vendor"]:
                device["vendor"] = get_mac_vendor(mac)
            
            if device["hostname"] != "Unknown":
                connected_devices.append({
                    "ip": device["ipv4"],  # Always use IPv4 address
                    "mac": mac,
                    "hostname": device["hostname"],
                    "vendor": device["vendor"]
                })

    
    # Register active devices in database (only one entry per MAC)
    for device in connected_devices:
        register_device(device["ip"], device["mac"], device["hostname"])

    return success(message="Active devices fetched", data=connected_devices)
