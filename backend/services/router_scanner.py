"""
Router Scanner Service for NetPilot

This service provides device discovery by scanning the router's ARP table.
It only returns devices that are:
1. On the br-lan interface (local network)
2. Have 0x2 flags (reachable/active)
3. Are currently communicating with the router
4. Within the 192.168.1.0/24 subnet

This approach provides reliable device detection without the need for ARP table flushing
or pinging entire IP ranges, while ensuring only devices in the specified subnet are included.
"""

import requests
import time
import re
from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager

logger = get_logger('services.router_scanner')
router_connection_manager = RouterConnectionManager()

def get_mac_vendor(mac):
    """
    Queries macvendors.com to get the vendor for a given MAC address.
    Returns 'Unknown Vendor' if request fails.
    """
    try:
        time.sleep(0.5)
        response = requests.get(f"https://api.macvendors.com/{mac}", timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except requests.RequestException as e:
        logger.warning(f"Vendor lookup failed for {mac}: {e}")
    return "Unknown Vendor"

def _is_in_subnet(ip, subnet):
    """
    Checks if an IP address is within the specified subnet.
    
    Args:
        ip (str): IP address to check (e.g., "192.168.1.100")
        subnet (str): Subnet in CIDR notation (e.g., "192.168.1.0/24")
    
    Returns:
        bool: True if IP is in subnet, False otherwise
    """
    try:
        # Parse subnet
        network, prefix = subnet.split('/')
        prefix = int(prefix)
        
        # Convert IP and network to integers for comparison
        ip_parts = [int(x) for x in ip.split('.')]
        network_parts = [int(x) for x in network.split('.')]
        
        # Calculate subnet mask
        mask = (0xffffffff >> (32 - prefix)) << (32 - prefix)
        
        # Convert to 32-bit integers
        ip_int = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]
        network_int = (network_parts[0] << 24) + (network_parts[1] << 16) + (network_parts[2] << 8) + network_parts[3]
        
        # Check if IP is in subnet
        return (ip_int & mask) == (network_int & mask)
        
    except (ValueError, IndexError) as e:
        logger.warning(f"Error checking subnet membership for {ip} in {subnet}: {e}")
        return False

def get_connected_devices():
    """
    Scans the router's ARP table to find active devices on br-lan with 0x2 flags,
    then uses DHCP leases to enrich the data with hostnames.
    Only returns devices that are currently reachable, active, and within the 192.168.1.0/24 subnet.
    """
    try:
        # Read directly from the kernel's ARP table file for maximum compatibility.
        # This avoids issues with PATH and the 'arp' command not being a real executable.
        arp_cmd = "cat /proc/net/arp"
        arp_output, arp_err = router_connection_manager.execute(arp_cmd)
        if arp_err:
            return None, f"Failed to get ARP table: {arp_err}"

        dhcp_cmd = "cat /tmp/dhcp.leases"
        dhcp_output, dhcp_err = router_connection_manager.execute(dhcp_cmd)
        if dhcp_err:
            logger.warning(f"Could not read DHCP leases: {dhcp_err}. Hostnames may be missing.")
            dhcp_output = ""

        devices = _parse_scan_results(arp_output, dhcp_output)
        return devices, None

    except RuntimeError as e:
        logger.error(f"Connection error scanning for devices: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Error scanning for connected devices: {str(e)}", exc_info=True)
        return None, "An unexpected error occurred while scanning for devices."

def get_router_info():
    """
    Retrieves key information about the router's status and configuration.
    """
    try:
        commands = [
            "uname -a",
            "uci get system.@system[0].hostname",
            "uci get network.lan.ipaddr",
            "uci get network.wan.ipaddr",
            "ifconfig br-lan | grep 'inet addr'",
            "uptime"
        ]
        full_command = " && ".join(f"echo '==={i}==='; {cmd}; echo '===END==='" for i, cmd in enumerate(commands))
        
        output, err = router_connection_manager.execute(full_command)
        
        if err:
            logger.warning(f"Some commands might have failed during router info retrieval: {err}")

        results = {}
        for i, cmd in enumerate(commands):
            pattern = re.compile(f"==={i}===\\n(.*?)\\n===END===", re.DOTALL)
            match = pattern.search(output)
            results[i] = match.group(1).strip() if match else "N/A"

        lan_ip_match = re.search(r'inet addr:(\S+)', results.get(4, ''))
        
        router_info = {
            "kernel_info": results.get(0, "N/A"),
            "hostname": results.get(1, "N/A"),
            "lan_ip": results.get(2, "N/A"),
            "wan_ip": results.get(3, "N/A"),
            "lan_ip_ifconfig": lan_ip_match.group(1) if lan_ip_match else "N/A",
            "uptime": results.get(5, "N/A").split('up ')[-1] if 'up' in results.get(5, '') else "N/A",
        }
        
        return router_info, None

    except RuntimeError as e:
        logger.error(f"Connection error getting router info: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Error getting router info: {str(e)}", exc_info=True)
        return None, "An unexpected error occurred while getting router info"

def _parse_scan_results(arp_data, dhcp_data):
    """
    Parses the raw output from ARP and DHCP lease files to create a structured
    list of connected devices, enriching with vendor information.
    Only includes devices with 0x2 flags (reachable/active) on br-lan interface
    and within the 192.168.1.0/24 subnet.
    """
    dhcp_map = {}
    for line in dhcp_data.strip().split('\n'):
        if not line: continue
        parts = line.split()
        if len(parts) >= 4:
            mac = parts[1].lower()
            hostname = parts[3] if parts[3] != '*' else 'Unknown'
            dhcp_map[mac] = hostname

    devices = []
    # Regex to capture the IP address, HW address (MAC), flags, and device from /proc/net/arp
    # Example line: 192.168.1.194    0x1         0x2         d2:f0:7b:2b:69:15     *        br-lan
    # We only want entries with 0x2 flags (reachable/active) and on br-lan interface
    arp_pattern = re.compile(r'^\s*([^\s]+)\s+0x\d\s+(0x2)\s+([0-9a-fA-F:]+)\s+\*\s+(br-lan)')

    # Skip the header line
    for line in arp_data.strip().split('\n')[1:]:
        if not line: continue
        match = arp_pattern.search(line)
        if match:
            ip, flags, mac, device = match.groups()
            # Only include devices on the LAN bridge with 0x2 flags (reachable/active)
            # and within the 192.168.1.0/24 subnet
            if device == "br-lan" and flags == "0x2" and _is_in_subnet(ip, "192.168.1.0/24"):
                mac = mac.lower()
                hostname = dhcp_map.get(mac, 'Unknown')
                vendor = get_mac_vendor(mac)
                
                devices.append({
                    "ip": ip,
                    "mac": mac,
                    "hostname": hostname,
                    "vendor": vendor,
                    "status": "active",
                    "interface": device
                })

    return devices
