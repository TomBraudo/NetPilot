import socket
import requests
import time
import re
from utils.ssh_client import ssh_manager
from utils.response_helpers import error, success
from db.device_repository import register_device
import json
import logging
import ipaddress

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    Scan the network using the OpenWrt router capabilities.
    Only returns devices that are:
    1. Actively connected at scan time
    2. On the same subnet as the router
    3. Includes the router itself in the device list
    
    Returns:
        Dictionary with success/error status and list of discovered devices
    """
    try:
        # First, determine the router's own subnet and details
        router_subnet, router_device = get_router_info()
        if not router_subnet:
            return error("Could not determine router subnet")
            
        logger.info(f"Router subnet detected as {router_subnet}")
        
        all_devices = {}
        active_macs = set()
        
        # Add the router itself to the device list
        if router_device:
            mac = router_device.get('mac', '').lower()
            if mac:
                all_devices[mac] = router_device
                all_devices[mac]['source'] = 'router'
                all_devices[mac]['is_router'] = True
                all_devices[mac]['active'] = True
                active_macs.add(mac)
        
        # 1. First, identify all CURRENTLY ACTIVE devices from ARP table
        # This will be our authoritative list of connected devices
        arp_devices = get_devices_from_arp(router_subnet)
        for device in arp_devices:
            mac = device.get('mac', '').lower()
            if mac:
                active_macs.add(mac)
                all_devices[mac] = device
                all_devices[mac]['source'] = 'arp_table'
                all_devices[mac]['active'] = True
        
        # 2. Add WiFi clients that are currently connected
        wifi_devices = get_wifi_clients(router_subnet)
        for device in wifi_devices:
            mac = device.get('mac', '').lower()
            if mac:
                active_macs.add(mac)
                if mac in all_devices:
                    all_devices[mac]['wifi_connected'] = True
                    all_devices[mac]['signal'] = device.get('signal')
                    all_devices[mac]['source'] = f"{all_devices[mac]['source']},wifi"
                else:
                    all_devices[mac] = device
                    all_devices[mac]['source'] = 'wifi'
                    all_devices[mac]['active'] = True
        
        # 3. Add devices with current active connections from conntrack
        conntrack_devices = get_devices_from_conntrack(router_subnet)
        for device in conntrack_devices:
            mac = device.get('mac', '').lower()
            if mac:
                active_macs.add(mac)
                if mac in all_devices:
                    all_devices[mac]['source'] = f"{all_devices[mac]['source']},conntrack"
                    if 'last_connection' in device:
                        all_devices[mac]['last_connection'] = device['last_connection']
                else:
                    all_devices[mac] = device
                    all_devices[mac]['source'] = 'conntrack'
                    all_devices[mac]['active'] = True
        
        # 4. Now get hostnames from DHCP leases but ONLY for active devices
        dhcp_devices = get_dhcp_leases(router_subnet)
        for device in dhcp_devices:
            mac = device.get('mac', '').lower()
            if mac and mac in active_macs:  # Only include if device is active
                if mac in all_devices:
                    # Only update hostname info
                    if device.get('hostname') and device.get('hostname') != 'Unknown':
                        all_devices[mac]['hostname'] = device['hostname']
                    all_devices[mac]['source'] = f"{all_devices[mac]['source']},dhcp"
        
        # Convert dictionary to list, including ONLY active devices
        device_list = [device for mac, device in all_devices.items() if mac in active_macs]
        
        # Register all discovered active devices in the database
        for device in device_list:
            register_device(
                device.get('mac', 'Unknown'),
                device.get('ip', 'Unknown'),
                device.get('hostname', 'Unknown'),
                device.get('device_type', 'Router' if device.get('is_router') else 'Unknown')
            )
        
        # Add a timestamp and subnet info to the scan results
        scan_result = {
            'timestamp': time.time(),
            'subnet': str(router_subnet),
            'devices': device_list
        }
        
        return success(data=scan_result)
    except Exception as e:
        logger.error(f"Error scanning network via router: {str(e)}")
        return error(f"Failed to scan network: {str(e)}")

def get_router_info():
    """
    Get the router's subnet and device information
    
    Returns:
        tuple: (IPv4Network subnet, dict router device info)
    """
    router_ip = None
    router_mac = None
    subnet = None
    hostname = "Router"
    
    try:
        # Get router's LAN IP
        output, _ = ssh_manager.execute_command("uci get network.lan.ipaddr")
        router_ip = output.strip()
        
        # Get router's netmask
        output, _ = ssh_manager.execute_command("uci get network.lan.netmask")
        netmask = output.strip()
        
        # Get router's hostname
        output, _ = ssh_manager.execute_command("uci get system.@system[0].hostname")
        if output and output.strip():
            hostname = output.strip()
        
        # Get router's MAC address
        output, _ = ssh_manager.execute_command("ip link show br-lan | grep link/ether | awk '{print $2}'")
        router_mac = output.strip()
        
        # If we couldn't get the info from UCI, try IP command
        if not router_ip or not netmask:
            output, _ = ssh_manager.execute_command("ip -o -f inet addr show br-lan | awk '/scope global/ {print $4}'")
            if output and '/' in output:
                cidr = output.strip()
                subnet = ipaddress.IPv4Network(cidr, strict=False)
                # Extract the IP from CIDR notation
                router_ip = cidr.split('/')[0]
        else:
            # Create subnet from router IP and netmask
            subnet = ipaddress.IPv4Network(f"{router_ip}/{netmask}", strict=False)
        
        # Fallback method using IP addr command if previous methods failed
        if not subnet:
            output, _ = ssh_manager.execute_command("ip addr | grep 'inet ' | grep -v '127.0.0.1' | head -n 1")
            if output:
                parts = output.strip().split()
                for part in parts:
                    if '/' in part and part.startswith('inet'):
                        cidr = part.replace('inet', '').strip()
                        subnet = ipaddress.IPv4Network(cidr, strict=False)
                        # Extract the IP from CIDR notation
                        if not router_ip:
                            router_ip = cidr.split('/')[0]
        
        # If we still don't have a MAC address, try another method
        if not router_mac:
            output, _ = ssh_manager.execute_command("cat /sys/class/net/br-lan/address")
            if output and output.strip():
                router_mac = output.strip()
        
        # Last resort for MAC - get the first ethernet device MAC
        if not router_mac:
            output, _ = ssh_manager.execute_command("cat /sys/class/net/eth0/address")
            if output and output.strip():
                router_mac = output.strip()
    except Exception as e:
        logger.error(f"Error determining router info: {str(e)}")
    
    # Last resort fallback - assume a standard class C subnet
    if not subnet:
        subnet = ipaddress.IPv4Network('192.168.1.0/24')
        router_ip = '192.168.1.1'
    
    # Create the router device information
    router_device = None
    if router_ip and router_mac:
        router_device = {
            "ip": router_ip,
            "mac": router_mac,
            "hostname": hostname,
            "device_type": "Router",
            "is_router": True
        }
    
    return subnet, router_device

def is_ip_in_subnet(ip, subnet):
    """
    Check if an IP address is within a particular subnet
    
    Args:
        ip: IP address to check
        subnet: IPv4Network object representing the subnet
    
    Returns:
        bool: True if the IP is in the subnet, False otherwise
    """
    try:
        return ipaddress.IPv4Address(ip) in subnet
    except:
        return False

def get_devices_from_arp(subnet):
    """
    Get actively connected devices from OpenWrt ARP table
    Only returns devices with state REACHABLE, DELAY, or STALE (all active states)
    and only those in the specified subnet
    """
    devices = []
    
    # Try JSON format first (newer OpenWrt)
    output, err = ssh_manager.execute_command("ip -j neighbor")
    if not err and output and output.strip():
        try:
            neighbors = json.loads(output)
            for neighbor in neighbors:
                ip = neighbor.get("dst")
                mac = neighbor.get("lladdr")
                state = neighbor.get("state", "")
                
                # Skip non-IPv4 addresses and only include active entries in our subnet
                if (ip and mac and ":" not in ip and 
                    any(s in state for s in ["REACHABLE", "DELAY", "STALE", "PERMANENT"]) and
                    is_ip_in_subnet(ip, subnet)):
                    device = {
                        "ip": ip,
                        "mac": mac,
                        "hostname": "Unknown"
                    }
                    devices.append(device)
            
            # If we found devices, return them
            if devices:
                return devices
        except:
            # Fall back to traditional format
            pass
    
    # Traditional format (works on all OpenWrt versions)
    output, _ = ssh_manager.execute_command("ip neighbor show | grep -v FAILED | grep -v INCOMPLETE")
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 5:
            ip = parts[0]
            if ":" in ip:  # Skip IPv6
                continue
            if any(s in line for s in ["REACHABLE", "DELAY", "STALE", "PERMANENT"]):
                # Only include IPs in our subnet
                if is_ip_in_subnet(ip, subnet):
                    mac = None
                    for i, part in enumerate(parts):
                        if part == "lladdr":
                            mac = parts[i+1]
                            break
                    
                    if mac:
                        device = {
                            "ip": ip,
                            "mac": mac,
                            "hostname": "Unknown"
                        }
                        devices.append(device)
    
    return devices

def get_dhcp_leases(subnet):
    """
    Get DHCP leases with hostname information
    Only for devices within the specified subnet
    """
    devices = []
    
    # Try ubus method first (newer OpenWrt)
    output, err = ssh_manager.execute_command("ubus call dhcp leases")
    if not err and output and output.strip():
        try:
            data = json.loads(output)
            for lease in data.get("leases", []):
                ip = lease.get("ipaddr")
                mac = lease.get("macaddr")
                hostname = lease.get("hostname", "Unknown")
                
                if ip and mac and is_ip_in_subnet(ip, subnet):
                    device = {
                        "ip": ip,
                        "mac": mac,
                        "hostname": hostname if hostname else "Unknown"
                    }
                    devices.append(device)
            
            # If we got valid data, return it
            if devices:
                return devices
        except:
            pass  # Fall back to file parsing
    
    # Parse DHCP leases file (works on all OpenWrt versions)
    output, _ = ssh_manager.execute_command("cat /tmp/dhcp.leases")
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 4:
            # Format: lease_time MAC IP hostname *
            mac = parts[1]
            ip = parts[2]
            hostname = parts[3] if parts[3] != "*" else "Unknown"
            
            if is_ip_in_subnet(ip, subnet):
                device = {
                    "ip": ip,
                    "mac": mac,
                    "hostname": hostname
                }
                devices.append(device)
    
    return devices

def get_devices_from_conntrack(subnet):
    """
    Get devices with current active connections from connection tracking table
    Only includes devices with ESTABLISHED connections and in the specified subnet
    """
    devices = []
    seen_ips = set()
    
    # Query the connection tracking table for ESTABLISHED connections only
    output, _ = ssh_manager.execute_command(
        "cat /proc/net/nf_conntrack | grep -v '127.0.0.1' | grep ESTABLISHED"
    )
    
    # Process each connection
    for line in output.splitlines():
        # Extract IPs from the connection
        src_ip = None
        dst_ip = None
        
        if "src=" in line and "dst=" in line:
            parts = line.split()
            for part in parts:
                if part.startswith("src="):
                    src_ip = part.split("=")[1]
                elif part.startswith("dst="):
                    dst_ip = part.split("=")[1]
            
            # Determine which IP is on the local subnet
            local_ip = None
            
            for ip in [src_ip, dst_ip]:
                if ip and is_ip_in_subnet(ip, subnet) and ip not in seen_ips:
                    local_ip = ip
                    seen_ips.add(ip)
                    break
            
            if local_ip:
                # Get MAC address for this IP
                arp_cmd = f"ip neighbor show {local_ip} | awk '{{print $5}}'"
                mac_output, _ = ssh_manager.execute_command(arp_cmd)
                mac = mac_output.strip()
                
                if mac:
                    device = {
                        "ip": local_ip,
                        "mac": mac,
                        "hostname": "Unknown",
                        "last_connection": int(time.time())
                    }
                    
                    devices.append(device)
    
    return devices

def get_wifi_clients(subnet):
    """
    Get currently connected WiFi clients
    Only for devices within the specified subnet
    """
    devices = []
    
    # Try to get associated WiFi clients using hostapd_cli
    output, _ = ssh_manager.execute_command(
        "for i in $(ls /var/run/hostapd-*); do hostapd_cli -p $(dirname $i) -i $(basename $i | cut -d'-' -f2) all_sta; done"
    )
    
    wifi_macs = set()
    if output and output.strip():
        for line in output.splitlines():
            if "=" in line and "dot11RSNAStatsSTAAddress" in line:
                mac = line.split('=')[1].strip()
                wifi_macs.add(mac)
                
                # Try to get signal strength
                signal_cmd = f"iw dev wlan0 station get {mac} | grep signal | awk '{{print $2}}'"
                signal_output, _ = ssh_manager.execute_command(signal_cmd)
                signal = signal_output.strip() if signal_output else None
                
                # Get IP for this MAC
                ip_cmd = f"ip -4 neigh show | grep -i {mac} | awk '{{print $1}}'"
                ip_output, _ = ssh_manager.execute_command(ip_cmd)
                ip = ip_output.strip() if ip_output else None
                
                if ip and is_ip_in_subnet(ip, subnet):
                    device = {
                        "ip": ip,
                        "mac": mac,
                        "hostname": "Unknown",
                        "wifi_connected": True,
                        "signal": signal
                    }
                    devices.append(device)
    
    # If the above method didn't find any clients, try the traditional iwinfo method
    if not devices:
        output, _ = ssh_manager.execute_command("iwinfo | grep -A 1 'STA'")
        for line in output.splitlines():
            if ":" in line and len(line.split()) >= 1:
                for part in line.split():
                    if ":" in part and len(part) == 17:  # MAC address format
                        mac = part
                        if mac not in wifi_macs:  # Avoid duplicates
                            wifi_macs.add(mac)
                            
                            # Get IP for this MAC
                            ip_cmd = f"ip -4 neigh show | grep -i {mac} | awk '{{print $1}}'"
                            ip_output, _ = ssh_manager.execute_command(ip_cmd)
                            ip = ip_output.strip() if ip_output else None
                            
                            if ip and is_ip_in_subnet(ip, subnet):
                                device = {
                                    "ip": ip,
                                    "mac": mac,
                                    "hostname": "Unknown",
                                    "wifi_connected": True
                                }
                                devices.append(device)
    
    return devices
