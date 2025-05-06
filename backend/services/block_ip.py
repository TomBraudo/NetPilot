import subprocess
from utils.ssh_client import ssh_manager
from utils.response_helpers import success, error
from db.device_repository import is_device_protected, get_mac_from_ip, is_critical_device
from services.admin_protection import get_admin_device_mac

def block_mac_address(target_ip):
    """
    Blocks a device by IP address using blacklist approach.
    """
    try:
        # Get MAC address from DHCP leases
        command_get_mac = "cat /tmp/dhcp.leases"
        output, error = ssh_manager.execute_command(command_get_mac)
        
        if error:
            return error(f"Failed to fetch connected devices: {error}")

        # Find MAC address of the target IP
        mac_address = None
        for line in output.split("\n"):
            parts = line.split()
            if len(parts) >= 3 and parts[2] == target_ip:
                mac_address = parts[1]
                break

        if not mac_address:
            # Try alternative method to find MAC
            arp_cmd = f"ip neigh show | grep '{target_ip}' | awk '{{print $5}}'"
            mac_output, _ = ssh_manager.execute_command(arp_cmd)
            if mac_output and len(mac_output.strip()) > 0:
                mac_address = mac_output.strip()
            else:
                return error(f"IP {target_ip} not found in connected devices.")
        
        # Check if this is the admin device
        admin_mac = get_admin_device_mac()
        if admin_mac and admin_mac.lower() == mac_address.lower():
            return error(f"Cannot block admin device {mac_address} ({target_ip})")

        # Check for critical devices (router, self, etc.)
        if is_critical_device(mac_address, target_ip):
            return error(f"Cannot block critical device {mac_address} ({target_ip})")

        # Always use blacklist mode
        return block_mac_blacklist_mode(mac_address, target_ip)
            
    except Exception as e:
        return error(f"Error blocking device: {str(e)}")

def block_mac_blacklist_mode(mac_address, target_ip):
    """
    Block a device using blacklist approach with OpenWrt traffic rules.
    """
    try:
        success_methods = []
        
        # 1. Add to WiFi deny lists
        get_wifi_ifaces = "uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1"
        ifaces_output, _ = ssh_manager.execute_command(get_wifi_ifaces)
        
        if ifaces_output:
            for iface in ifaces_output.splitlines():
                if iface:
                    # Set MAC filter to deny mode
                    cmd1 = f"uci set wireless.{iface}.macfilter='deny'"
                    # Add MAC to filter list
                    cmd2 = f"uci add_list wireless.{iface}.maclist='{mac_address}'"
                    
                    _, err1 = ssh_manager.execute_command(cmd1)
                    _, err2 = ssh_manager.execute_command(cmd2)
                    
                    if not err1 and not err2:
                        success_methods.append(f"Added to WiFi deny list on {iface}")
        
        # 2. Add a firewall block rule
        block_commands = [
            f"uci add firewall rule",
            f"uci set firewall.@rule[-1].name='NetPilot Block {mac_address}'",
            f"uci set firewall.@rule[-1].src='lan'", 
            f"uci set firewall.@rule[-1].dest='wan'",
            f"uci set firewall.@rule[-1].proto='all'",
            f"uci set firewall.@rule[-1].src_mac='{mac_address}'",
            f"uci set firewall.@rule[-1].target='REJECT'",
            f"uci set firewall.@rule[-1].enabled='1'"
        ]
        
        for cmd in block_commands:
            _, err = ssh_manager.execute_command(cmd)
            if not err:
                success_methods.append("Added firewall block rule")
        
        # Apply changes
        ssh_manager.execute_command("uci commit wireless")
        ssh_manager.execute_command("uci commit firewall")
        ssh_manager.execute_command("wifi reload")
        ssh_manager.execute_command("/etc/init.d/firewall reload")
        
        if success_methods:
            methods_str = ", ".join(success_methods)
            return success(f"Device {mac_address} ({target_ip}) blocked using: {methods_str}")
        else:
            return error(f"Failed to block device")
    except Exception as e:
        return error(f"Error in blocking: {str(e)}")

def unblock_mac_address(target_ip):
    """
    Unblocks a device by IP address using blacklist approach.
    """
    try:
        # Get MAC address from DHCP leases
        command_get_mac = "cat /tmp/dhcp.leases"
        output, error = ssh_manager.execute_command(command_get_mac)
        
        if error:
            return error(f"Failed to fetch connected devices: {error}")

        # Find MAC address of the target IP
        mac_address = None
        for line in output.split("\n"):
            parts = line.split()
            if len(parts) >= 3 and parts[2] == target_ip:
                mac_address = parts[1]
                break

        if not mac_address:
            # Try alternative method to find MAC
            arp_cmd = f"ip neigh show | grep '{target_ip}' | awk '{{print $5}}'"
            mac_output, _ = ssh_manager.execute_command(arp_cmd)
            if mac_output and len(mac_output.strip()) > 0:
                mac_address = mac_output.strip()
            else:
                return error(f"IP {target_ip} not found in connected devices.")
        
        # Always use blacklist mode
        return unblock_mac_blacklist_mode(mac_address, target_ip)
            
    except Exception as e:
        return error(f"Error unblocking device: {str(e)}")

def unblock_mac_blacklist_mode(mac_address, target_ip):
    """
    Unblock a device using blacklist approach.
    """
    try:
        success_methods = []
        
        # 1. Remove from WiFi deny lists
        get_wifi_ifaces = "uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1"
        ifaces_output, _ = ssh_manager.execute_command(get_wifi_ifaces)
        
        if ifaces_output:
            for iface in ifaces_output.splitlines():
                if iface:
                    # Remove MAC from deny list
                    cmd = f"uci del_list wireless.{iface}.maclist='{mac_address}'"
                    _, err = ssh_manager.execute_command(cmd)
                    
                    if not err:
                        success_methods.append(f"Removed from WiFi deny list on {iface}")
        
        # 2. Find and remove any block rules from firewall
        block_rule_check = f"uci show firewall | grep -i 'NetPilot Block' | grep -i '{mac_address}'"
        block_rule_output, _ = ssh_manager.execute_command(block_rule_check)
        
        if block_rule_output:
            # Parse rule section from output and delete it
            for line in block_rule_output.splitlines():
                if "=" in line:
                    try:
                        rule_section = line.split(".")[1].split(".")[0]
                        delete_cmd = f"uci delete firewall.{rule_section}"
                        _, err = ssh_manager.execute_command(delete_cmd)
                        if not err:
                            success_methods.append("Removed firewall block rule")
                    except:
                        pass
        
        # 3. Apply all changes
        ssh_manager.execute_command("uci commit wireless")
        ssh_manager.execute_command("uci commit firewall")
        ssh_manager.execute_command("wifi reload")
        ssh_manager.execute_command("/etc/init.d/firewall reload")
        
        if success_methods:
            methods_str = ", ".join(success_methods)
            return success(f"Device {mac_address} ({target_ip}) unblocked using: {methods_str}")
        else:
            return error(f"Failed to unblock device")
    except Exception as e:
        return error(f"Error in unblocking: {str(e)}")

def get_blocked_devices():
    """
    Retrieves a list of all blocked devices with IP, MAC, and hostname.
    """
    blocked_macs = set()
    blocked_devices = []

    # Retrieve Wi-Fi blocked MACs
    command_get_blocked_wifi = "uci show wireless | grep maclist"
    wifi_output, error = ssh_manager.execute_command(command_get_blocked_wifi)
    
    if not error and wifi_output.strip():
        for line in wifi_output.split("\n"):
            if "'" in line:  # Extract MAC addresses
                start = line.find("'")
                end = line.rfind("'")
                if start != -1 and end != -1 and start < end:
                    mac = line[start+1:end].lower()
                    blocked_macs.add(mac)

    # Retrieve firewall-blocked MACs
    # Try UCI first (more reliable in OpenWrt)
    fw_cmd = "uci show firewall | grep -i 'NetPilot Block'"
    fw_output, _ = ssh_manager.execute_command(fw_cmd)
    
    if fw_output:
        for line in fw_output.split("\n"):
            if "'src_mac'" in line and "=" in line:
                parts = line.split("=")
                if len(parts) > 1 and "'" in parts[1]:
                    start = parts[1].find("'")
                    end = parts[1].rfind("'")
                    if start != -1 and end != -1 and start < end:
                        mac = parts[1][start+1:end].lower()
                        blocked_macs.add(mac)

    if not blocked_macs:
        return success("No devices are currently blocked.")

    # Retrieve DHCP leases to match MACs with IPs and hostnames
    command_get_dhcp = "cat /tmp/dhcp.leases"
    dhcp_output, error = ssh_manager.execute_command(command_get_dhcp)

    if error:
        return error(f"Failed to fetch DHCP leases: {error}")

    # Parse DHCP leases to map MAC -> IP & Hostname
    dhcp_map = {}
    for line in dhcp_output.split("\n"):
        parts = line.split()
        if len(parts) >= 4:  # Format: <lease_time> <MAC> <IP> <Hostname>
            lease_mac = parts[1].lower()  # Normalize MAC address
            lease_ip = parts[2]
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

    return success(data=blocked_devices)

def verify_block_status(mac_address):
    """
    Verify if a device is properly blocked in the system.
    
    Args:
        mac_address: MAC address to check
        
    Returns:
        dict: Status information about the block
    """
    try:
        status = {
            "wifi_filters": False,
            "firewall_rules": False,
            "is_connected": False
        }
        
        # Check WiFi deny lists
        wifi_cmd = f"uci show wireless | grep maclist | grep '{mac_address}'"
        wifi_output, _ = ssh_manager.execute_command(wifi_cmd)
        
        if wifi_output and mac_address.lower() in wifi_output.lower():
            status["wifi_filters"] = True
        
        # Check firewall rules 
        fw_cmd = f"uci show firewall | grep -i 'NetPilot Block' | grep -i '{mac_address}'"
        fw_output, _ = ssh_manager.execute_command(fw_cmd)
        
        if fw_output and mac_address.lower() in fw_output.lower():
            status["firewall_rules"] = True
        
        # Check if device is still connected
        conn_cmd = f"ip neigh show | grep '{mac_address}'"
        conn_output, _ = ssh_manager.execute_command(conn_cmd)
        
        status["is_connected"] = bool(conn_output and len(conn_output.strip()) > 0)
        
        return status
    except Exception as e:
        logger.error(f"Error verifying block status: {e}")
        return {}

def debug_blocking(mac_address):
    """
    Diagnose why blocking might not be working for a device.
    
    Args:
        mac_address: MAC address to check
        
    Returns:
        dict: Diagnostic information
    """
    try:
        diagnostics = {}
        
        # Check if device is connected
        conn_cmd = f"ip neigh show | grep -i '{mac_address}'"
        conn_output, _ = ssh_manager.execute_command(conn_cmd)
        
        diagnostics["connected"] = bool(conn_output and len(conn_output.strip()) > 0)
        if conn_output:
            diagnostics["connection_details"] = conn_output.strip()
        
        # Check MAC filters
        mac_cmd = f"uci show wireless | grep macfilter"
        mac_output, _ = ssh_manager.execute_command(mac_cmd)
        
        diagnostics["mac_filter_config"] = mac_output.strip() if mac_output else "No MAC filters configured"
        
        # Check if MAC is in filter lists
        list_cmd = f"uci show wireless | grep maclist | grep -i '{mac_address}'"
        list_output, _ = ssh_manager.execute_command(list_cmd)
        
        diagnostics["in_mac_lists"] = bool(list_output and len(list_output.strip()) > 0)
        
        # Check firewall rules
        fw_cmd = f"uci show firewall | grep -i 'NetPilot Block' | grep -i '{mac_address}'"
        fw_output, _ = ssh_manager.execute_command(fw_cmd)
        
        diagnostics["in_firewall"] = bool(fw_output and len(fw_output.strip()) > 0)
        if fw_output:
            diagnostics["firewall_rules"] = fw_output.strip()
        
        # Check for MAC randomization
        random_cmd = "iwinfo | grep -A 10 'STA' | grep -i mac"
        random_output, _ = ssh_manager.execute_command(random_cmd)
        
        diagnostics["connected_macs"] = random_output.strip() if random_output else "No wireless clients found"
        
        return diagnostics
    except Exception as e:
        logger.error(f"Error diagnosing blocking: {e}")
        return {"error": str(e)}
