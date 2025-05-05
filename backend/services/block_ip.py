import subprocess
from utils.ssh_client import ssh_manager
from utils.response_helpers import success, error
from db.device_repository import is_device_protected, get_mac_from_ip, is_critical_device
from services.rule_mode import get_rule_mode, WHITELIST_MODE, BLACKLIST_MODE
from services.admin_protection import get_admin_device_mac

def block_mac_address(target_ip):
    """
    Blocks a device by IP address, with admin device protection.
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

        # Check rule mode
        mode = get_rule_mode()
        
        if mode == BLACKLIST_MODE:
            # In blacklist mode, add the device to deny lists
            return block_mac_blacklist_mode(mac_address, target_ip)
        else:
            # In whitelist mode, remove the device from allow lists
            return block_mac_whitelist_mode(mac_address, target_ip)
            
    except Exception as e:
        return error(f"Error blocking device: {str(e)}")

def block_mac_blacklist_mode(mac_address, target_ip):
    """
    Block a device in blacklist mode using OpenWrt traffic rules.
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
            return success(f"Device {mac_address} ({target_ip}) blocked in blacklist mode using: {methods_str}")
        else:
            return error(f"Failed to block device in blacklist mode")
    except Exception as e:
        return error(f"Error in blacklist blocking: {str(e)}")

def block_mac_whitelist_mode(mac_address, target_ip):
    """
    Block a device in whitelist mode using OpenWrt traffic rules.
    """
    try:
        success_methods = []
        
        # 1. Remove from WiFi allow lists
        get_wifi_ifaces = "uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1"
        ifaces_output, _ = ssh_manager.execute_command(get_wifi_ifaces)
        
        if ifaces_output:
            for iface in ifaces_output.splitlines():
                if iface:
                    # Remove MAC from allowed list
                    cmd = f"uci del_list wireless.{iface}.maclist='{mac_address}'"
                    _, err = ssh_manager.execute_command(cmd)
                    
                    if not err:
                        success_methods.append(f"Removed from WiFi allow list on {iface}")
        
        # 2. Add a specific block rule
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
            return success(f"Device {mac_address} ({target_ip}) blocked in whitelist mode using: {methods_str}")
        else:
            return error(f"Failed to block device in whitelist mode")
    except Exception as e:
        return error(f"Error in whitelist blocking: {str(e)}")

def unblock_mac_address(target_ip):
    """
    Unblocks a device by IP address, following the current rule mode.
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
        
        # Check rule mode
        mode = get_rule_mode()
        
        if mode == BLACKLIST_MODE:
            # In blacklist mode, remove the device from deny lists
            return unblock_mac_blacklist_mode(mac_address, target_ip)
        else:
            # In whitelist mode, add the device to allow lists
            return unblock_mac_whitelist_mode(mac_address, target_ip)
            
    except Exception as e:
        return error(f"Error unblocking device: {str(e)}")

def unblock_mac_blacklist_mode(mac_address, target_ip):
    """
    Unblock a device in blacklist mode (remove from deny lists).
    Uses OpenWrt traffic rules for firewall configuration.
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
            return success(f"Device {mac_address} ({target_ip}) unblocked in blacklist mode using: {methods_str}")
        else:
            return error(f"Failed to unblock device in blacklist mode")
    except Exception as e:
        return error(f"Error in blacklist unblocking: {str(e)}")

def unblock_mac_whitelist_mode(mac_address, target_ip):
    """
    Unblock a device in whitelist mode (add to allow lists).
    Uses a comprehensive approach to ensure device has internet access.
    """
    try:
        success_methods = []
        
        # 1. First remove any block rules
        # Find and remove any block rules from firewall
        block_rule_check = f"uci show firewall | grep '@rule' | grep -i '{mac_address}' | grep -i 'Block'"
        block_rule_output, _ = ssh_manager.execute_command(block_rule_check)
        
        if block_rule_output:
            # Parse rule section from output and delete it
            for line in block_rule_output.splitlines():
                if "=" in line and "." in line:
                    try:
                        rule_section = line.split(".")[1].split(".")[0]
                        delete_cmd = f"uci delete firewall.{rule_section}"
                        _, err = ssh_manager.execute_command(delete_cmd)
                        if not err:
                            success_methods.append("Removed firewall block rule")
                    except:
                        pass
        
        # 2. Add to WiFi allow lists on all interfaces
        get_wifi_ifaces = "uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1"
        ifaces_output, _ = ssh_manager.execute_command(get_wifi_ifaces)
        
        if ifaces_output:
            for iface in ifaces_output.splitlines():
                if iface:
                    # Ensure MAC filter is in allow mode
                    cmd1 = f"uci set wireless.{iface}.macfilter='allow'"
                    # Add MAC to allowed list
                    cmd2 = f"uci add_list wireless.{iface}.maclist='{mac_address}'"
                    
                    _, err1 = ssh_manager.execute_command(cmd1)
                    _, err2 = ssh_manager.execute_command(cmd2)
                    
                    if not err1 and not err2:
                        success_methods.append(f"Added to WiFi allow list on {iface}")
        
        # 3. Remove any existing allow rules (to avoid duplicates)
        allow_rule_check = f"uci show firewall | grep '@rule' | grep -i '{mac_address}' | grep -i 'Allow'"
        allow_rule_output, _ = ssh_manager.execute_command(allow_rule_check)
        
        if allow_rule_output:
            for line in allow_rule_output.splitlines():
                if "=" in line and "." in line:
                    try:
                        rule_section = line.split(".")[1].split(".")[0]
                        delete_cmd = f"uci delete firewall.{rule_section}"
                        ssh_manager.execute_command(delete_cmd)
                    except:
                        pass
        
        # 4. Add a high-priority allow rule
        allow_commands = [
            f"uci add firewall rule",
            f"uci set firewall.@rule[-1].name='NetPilot Allow {mac_address}'",
            f"uci set firewall.@rule[-1].src='lan'",
            f"uci set firewall.@rule[-1].dest='wan'",
            f"uci set firewall.@rule[-1].proto='all'",
            f"uci set firewall.@rule[-1].src_mac='{mac_address}'",
            f"uci set firewall.@rule[-1].target='ACCEPT'",
            f"uci set firewall.@rule[-1].enabled='1'",
            f"uci set firewall.@rule[-1].priority='10'" # High priority
        ]
        
        for cmd in allow_commands:
            _, err = ssh_manager.execute_command(cmd)
            if err:
                logger.error(f"Error adding allow rule: {err}")
            else:
                success_methods.append("Added high-priority firewall allow rule")
        
        # 5. Also ensure any direct iptables rules are cleaned up
        ssh_manager.execute_command(f"iptables -D FORWARD -m mac --mac-source {mac_address} -j DROP 2>/dev/null")
        ssh_manager.execute_command(f"iptables -D FORWARD -m mac --mac-source {mac_address} -j REJECT 2>/dev/null")
        
        # 6. Add direct iptables accept rule for immediate effect
        ssh_manager.execute_command(f"iptables -I FORWARD 1 -m mac --mac-source {mac_address} -j ACCEPT")
        success_methods.append("Added direct iptables ACCEPT rule")
        
        # 7. Apply all changes
        ssh_manager.execute_command("uci commit wireless")
        ssh_manager.execute_command("uci commit firewall")
        ssh_manager.execute_command("wifi reload")
        ssh_manager.execute_command("/etc/init.d/firewall reload")
        ssh_manager.execute_command("iptables-save > /etc/firewall.user")
        
        if success_methods:
            methods_str = ", ".join(success_methods)
            return success(f"Device {mac_address} ({target_ip}) unblocked in whitelist mode using: {methods_str}")
        else:
            return error(f"Failed to unblock device in whitelist mode")
    except Exception as e:
        return error(f"Error in whitelist unblocking: {str(e)}")

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

    return success(data=blocked_devices)

def block_device_with_mode(mac, is_blacklist):
    """
    Block a device considering blacklist/whitelist mode.
    
    Args:
        mac: MAC address of device
        is_blacklist: True for blacklist (block this device), 
                     False for whitelist (block all except this)
    """
    if is_blacklist:
        # In blacklist mode, block this specific device
        cmd = f"iptables -I FORWARD -m mac --mac-source {mac} -j DROP"
    else:
        # In whitelist mode, allow only this device
        # First, ensure we have a rule to allow this device
        cmd1 = f"iptables -I FORWARD -m mac --mac-source {mac} -j ACCEPT"
        # Then ensure we have a default deny rule at the end
        cmd2 = "iptables -A FORWARD -j DROP"
        
        ssh_manager.execute_command(cmd1)
        return ssh_manager.execute_command(cmd2)
        
    return ssh_manager.execute_command(cmd)

def verify_block_status(mac_address):
    """
    Verify if a device is effectively blocked.
    
    Args:
        mac_address: MAC address to check
        
    Returns:
        dict: Status of each blocking method
    """
    try:
        status = {
            "wifi_filters": False,
            "firewall_rules": False,
            "is_connected": True,  # Default to assume it's still connected
        }
        
        # Check WiFi filters
        wifi_cmd = f"uci show wireless | grep maclist | grep '{mac_address}'"
        wifi_output, _ = ssh_manager.execute_command(wifi_cmd)
        
        if wifi_output and mac_address.lower() in wifi_output.lower():
            status["wifi_filters"] = True
        
        # Check firewall rules
        fw_cmd = f"iptables-save | grep '{mac_address}'"
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
        fw_cmd = f"iptables -L -n | grep -i '{mac_address}'"
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
