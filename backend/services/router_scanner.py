import socket
import requests
import time
import re
import json
import os
from utils.ssh_client import ssh_manager
from utils.response_helpers import error, success
from utils.config_manager import config_manager
from db.device_repository import register_device
from db.tinydb_client import TinyDBClient
import ipaddress
from utils.logging_config import get_logger
from datetime import datetime

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
    Scans the network for active devices using the router's DHCP leases and ARP table.
    Returns a list of connected devices with their IP, MAC, hostname, and vendor information.
    """
    connected_devices = []
    device_map = {}

    # Get DHCP leases
    dhcp_cmd = "cat /tmp/dhcp.leases"
    dhcp_output, dhcp_error = ssh_manager.execute_command(dhcp_cmd)
    
    if not dhcp_error and dhcp_output.strip():
        for line in dhcp_output.split("\n"):
            parts = line.split()
            if len(parts) >= 4:
                mac = parts[1]
                ip = parts[2]
                hostname = parts[3]
                
                device_map[mac] = {
                    "ipv4": ip,
                    "hostname": hostname,
                    "vendor": None
                }

    # Get ARP table
    arp_cmd = "cat /proc/net/arp"
    arp_output, arp_error = ssh_manager.execute_command(arp_cmd)
    
    if not arp_error and arp_output.strip():
        for line in arp_output.split("\n")[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 4:
                ip = parts[0]
                mac = parts[3]
                
                if mac != "00:00:00:00:00:00":  # Skip incomplete entries
                    if mac not in device_map:
                        device_map[mac] = {
                            "ipv4": ip,
                            "hostname": None,
                            "vendor": None
                        }
                    elif not device_map[mac]["ipv4"]:
                        device_map[mac]["ipv4"] = ip

    # Get router's network
    router_ip_cmd = "uci get network.lan.ipaddr"
    router_ip_output, router_ip_error = ssh_manager.execute_command(router_ip_cmd)
    
    if router_ip_error:
        return error("Failed to get router IP address")
        
    router_ip = router_ip_output.strip()
    router_network = ipaddress.ip_network(f"{router_ip}/24", strict=False)

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
            
            connected_devices.append({
                "ip": device["ipv4"],  # Always use IPv4 address
                "mac": mac,
                "hostname": device["hostname"],
                "vendor": device["vendor"]
            })

    # Register active devices through device management service and save to database
    db_client = TinyDBClient()
    
    # Get existing devices to determine next ID
    existing_devices = db_client.devices.all()
    next_id = str(len(existing_devices) + 1)
    
    # Clear existing devices table
    db_client.devices.truncate()
    
    # Save devices with numeric IDs
    devices_dict = {}
    for i, device in enumerate(connected_devices, 1):
        # Register device in the device repository
        register_device(device["ip"], device["mac"], device["hostname"])
        
        # Save to devices table in TinyDB with numeric ID
        devices_dict[str(i)] = {
            "ip": device["ip"],
            "mac": device["mac"],
            "hostname": device["hostname"],
            "last_seen": datetime.now().isoformat()
        }
    
    # Save all devices at once
    db_client.devices.insert({"devices": devices_dict})
    
    # Ensure changes are persisted
    db_client.flush()
    logger.info(f"Successfully saved {len(connected_devices)} devices to database")

    return success(message="Active devices fetched", data=connected_devices)
