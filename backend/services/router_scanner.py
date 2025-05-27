import socket
import requests
import time
import re
import json
import os
from utils.ssh_client import ssh_manager
from utils.response_helpers import success
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
        return "Unknown Vendor"
    except requests.RequestException as e:
        logger.warning(f"Vendor lookup failed for {mac}: {e}")
        return "Unknown Vendor"

def scan_network_via_router():
    """
    Scans the network using the OpenWrt router's DHCP leases and connected devices.
    Returns a list of devices with their IP, MAC, hostname, and vendor information.
    """
    try:
        # Get router IP from config
        config = config_manager.load_config('router')
        router_ip = config.get('ip')
        if not router_ip:
            raise ValueError("Router IP not configured")

        # Get DHCP leases
        output, error = ssh_manager.execute_command("cat /tmp/dhcp.leases")
        if error:
            raise Exception(f"Failed to get DHCP leases: {error}")

        # Parse DHCP leases
        device_map = {}
        for line in output.splitlines():
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

        # Get connected devices from wireless
        output, error = ssh_manager.execute_command("iwinfo")
        if error:
            raise Exception(f"Failed to get wireless info: {error}")

        # Parse wireless info
        current_interface = None
        for line in output.splitlines():
            if line.startswith("wlan"):
                current_interface = line.split()[0]
            elif current_interface and "Access Point" in line:
                mac = re.search(r"([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})", line)
                if mac:
                    mac = mac.group(1).lower()
                    if mac not in device_map:
                        device_map[mac] = {
                            "ipv4": None,
                            "hostname": "Unknown",
                            "vendor": None
                        }

        # Filter devices to only include those in the router's subnet
        connected_devices = []
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
        return success(data=connected_devices)
    except Exception as e:
        logger.error(f"Error scanning network via router: {str(e)}", exc_info=True)
        raise
