from flask import Blueprint, request, jsonify
from services.admin_protection import register_admin_device, get_admin_device_mac, ensure_admin_device_protected, get_mac_from_ip
from utils.response_helpers import success, error
from utils.ssh_client import ssh_manager

admin_bp = Blueprint('admin', __name__)

'''
    API endpoint to register the current device as admin device
'''
@admin_bp.route("/api/admin/register", methods=["POST"])
def register_admin_endpoint():
    # Get client IP from request
    client_ip = request.remote_addr
    
    # Register this device as admin
    result = register_admin_device(ip_address=client_ip)
    return jsonify(result)

'''
    API endpoint to get admin device info
'''
@admin_bp.route("/api/admin/status", methods=["GET"])
def admin_status_endpoint():
    admin_mac = get_admin_device_mac()
    
    if not admin_mac:
        return jsonify({"status": "no_admin", "message": "No admin device registered"})
        
    # Ensure admin device is protected
    ensure_admin_device_protected(admin_mac)
    
    return jsonify(success(data={"admin_mac": admin_mac}))

@admin_bp.route("/api/admin/emergency_reset", methods=["POST"])
def emergency_reset_endpoint():
    """
    Emergency endpoint to reset all filtering.
    """
    try:
        # Reset wireless filtering
        reset_cmds = [
            # Reset wireless
            "for iface in $(uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1); do "
            "uci set wireless.$iface.macfilter='disable'; "
            "uci delete wireless.$iface.maclist; done",
            
            # Commit wireless changes
            "uci commit wireless",
            
            # Reset firewall - remove all NetPilot rules instead of using iptables
            "for rule in $(uci show firewall | grep '@rule' | grep 'NetPilot' | cut -d. -f2 | cut -d= -f1); do "
            "uci delete firewall.$rule; done",
            
            # Commit firewall changes
            "uci commit firewall",
            
            # Apply changes
            "wifi reload",
            "/etc/init.d/firewall reload"
        ]
        
        for cmd in reset_cmds:
            ssh_manager.execute_command(cmd)
            
        # Reset rule mode to blacklist
        from services.rule_mode import set_rule_mode, BLACKLIST_MODE
        set_rule_mode(BLACKLIST_MODE)
        
        return jsonify(success("All filtering reset. System in blacklist mode with no rules."))
    except Exception as e:
        return jsonify(error(f"Emergency reset failed: {str(e)}"))

@admin_bp.route("/api/admin/auto_register", methods=["GET"])
def auto_register_admin_endpoint():
    """
    API endpoint to automatically register the device accessing this endpoint as admin
    Returns detailed information about the process for troubleshooting
    """
    # Get client IP from request
    client_ip = request.remote_addr
    
    # Get detailed info
    diagnostics = {}
    diagnostics["client_ip"] = client_ip
    
    # Check if we can map this IP to MAC
    client_mac = get_mac_from_ip(client_ip)
    diagnostics["mac_address"] = client_mac if client_mac else "Not found"
    
    # Try to register
    if client_mac:
        result = register_admin_device(mac_address=client_mac)
        diagnostics["registration_result"] = result
        
        # Verify protection
        # Check WiFi lists
        wifi_cmd = f"uci show wireless | grep maclist | grep -i '{client_mac}'"
        wifi_output, _ = ssh_manager.execute_command(wifi_cmd)
        diagnostics["in_wifi_lists"] = bool(wifi_output)
        
        # Check firewall rules using uci instead of iptables
        fw_cmd = f"uci show firewall | grep '@rule' | grep -i '{client_mac}'"
        fw_output, _ = ssh_manager.execute_command(fw_cmd)
        diagnostics["in_firewall"] = bool(fw_output)
        diagnostics["firewall_details"] = fw_output.strip() if fw_output else "No firewall rules found"
        
        # Get current mode
        from services.rule_mode import get_rule_mode
        diagnostics["current_mode"] = get_rule_mode()
        
        return jsonify(success(data=diagnostics))
    else:
        return jsonify(error(f"Could not find MAC address for IP {client_ip}", data=diagnostics))

@admin_bp.route("/api/admin/emergency_recover", methods=["GET"])
def emergency_recover_endpoint():
    """
    Emergency endpoint to recover access if whitelist mode blocks access.
    This switches to blacklist mode and registers the current device as admin.
    Compatible with OpenWrt traffic rules approach.
    """
    try:
        # Get client IP
        client_ip = request.remote_addr
        
        # Special handling for localhost
        if client_ip == "127.0.0.1":
            # Try to get a real LAN IP
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(('10.255.255.255', 1))
                real_ip = s.getsockname()[0]
                client_ip = real_ip if real_ip != "127.0.0.1" else None
            except:
                client_ip = None
            finally:
                s.close()
        
        # First, try to register this device as admin
        from services.admin_protection import get_mac_from_ip, register_admin_device
        client_mac = get_mac_from_ip(client_ip) if client_ip else None
        
        if client_mac:
            register_admin_device(mac_address=client_mac)
        
        # Emergency commands - clear all NetPilot firewall rules
        commands = [
            # Clear all NetPilot rules
            "for rule in $(uci show firewall | grep '@rule' | grep 'NetPilot' | cut -d. -f2 | cut -d= -f1); do "
            "uci delete firewall.$rule; done",
            
            # Disable WiFi filtering
            "for iface in $(uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1); do "
            "uci set wireless.$iface.macfilter='disable'; done",
            
            # Commit changes
            "uci commit wireless",
            "uci commit firewall",
            
            # Apply changes
            "wifi reload",
            "/etc/init.d/firewall reload"
        ]
        
        for cmd in commands:
            ssh_manager.execute_command(cmd)
        
        # Switch back to blacklist mode permanently
        from services.rule_mode import set_rule_mode, BLACKLIST_MODE
        set_rule_mode(BLACKLIST_MODE)
        
        return jsonify(success("EMERGENCY RECOVERY: Switched to blacklist mode and your device has been registered as admin if possible."))
    except Exception as e:
        return jsonify(error(f"Emergency recovery failed: {str(e)}"))

@admin_bp.route("/api/admin/diagnose_device", methods=["GET"])
def diagnose_device_endpoint():
    """
    Comprehensive diagnostic endpoint to troubleshoot device connectivity issues.
    Use with ?ip=x.x.x.x parameter to specify the device IP.
    """
    try:
        # Get the device IP from query parameter
        device_ip = request.args.get("ip")
        if not device_ip:
            return jsonify(error("Missing 'ip' query parameter"))
        
        # Collect comprehensive diagnostic information
        diagnostics = {}
        
        # 1. Check system mode
        from services.rule_mode import get_rule_mode, WHITELIST_MODE
        mode = get_rule_mode()
        diagnostics["system_mode"] = mode
        diagnostics["is_whitelist_mode"] = mode == WHITELIST_MODE
        
        # 2. Get device MAC
        from services.admin_protection import get_mac_from_ip
        device_mac = get_mac_from_ip(device_ip)
        diagnostics["device_mac"] = device_mac
        diagnostics["device_ip"] = device_ip
        
        if not device_mac:
            return jsonify(error(f"Could not find MAC address for IP {device_ip}"))
        
        # 3. Check WiFi configuration
        # First check the MAC filter mode on each interface
        wifi_modes = {}
        get_wifi_ifaces = "uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1"
        ifaces_output, _ = ssh_manager.execute_command(get_wifi_ifaces)
        
        if ifaces_output:
            for iface in ifaces_output.splitlines():
                if iface and iface.strip():
                    # Get MAC filter mode
                    mode_cmd = f"uci get wireless.{iface}.macfilter"
                    mode_output, _ = ssh_manager.execute_command(mode_cmd)
                    wifi_modes[iface] = mode_output.strip() if mode_output else "unknown"
                    
                    # Check if device is in the MAC list
                    list_cmd = f"uci show wireless.{iface}.maclist | grep -i '{device_mac}'"
                    list_output, _ = ssh_manager.execute_command(list_cmd)
                    wifi_modes[f"{iface}_has_device"] = bool(list_output and device_mac.lower() in list_output.lower())
        
        diagnostics["wifi_configuration"] = wifi_modes
        
        # 4. Check firewall rules for the device using uci
        # First check for explicit allow rules
        allow_cmd = f"uci show firewall | grep '@rule' | grep -i 'NetPilot Allow' | grep -i '{device_mac}'"
        allow_output, _ = ssh_manager.execute_command(allow_cmd)
        diagnostics["has_allow_rule"] = bool(allow_output and device_mac.lower() in allow_output.lower())
        
        # Check for block rules
        block_cmd = f"uci show firewall | grep '@rule' | grep -i 'NetPilot Block' | grep -i '{device_mac}'"
        block_output, _ = ssh_manager.execute_command(block_cmd)
        diagnostics["has_block_rule"] = bool(block_output and device_mac.lower() in block_output.lower())
        
        # 5. Check all firewall rules using uci instead of iptables
        fw_rules_cmd = f"uci show firewall | grep '@rule' | grep -i '{device_mac}'"
        fw_rules_output, _ = ssh_manager.execute_command(fw_rules_cmd)
        diagnostics["firewall_rules"] = fw_rules_output.strip() if fw_rules_output else "No rules found"
        
        # Check for ACCEPT and DROP rules separately using uci
        fw_accept_cmd = f"uci show firewall | grep '@rule' | grep -i '{device_mac}' | grep -i 'target=ACCEPT'"
        fw_accept_output, _ = ssh_manager.execute_command(fw_accept_cmd)
        diagnostics["has_accept_rule"] = bool(fw_accept_output)
        
        fw_drop_cmd = f"uci show firewall | grep '@rule' | grep -i '{device_mac}' | grep -i 'target=DROP'"
        fw_drop_output, _ = ssh_manager.execute_command(fw_drop_cmd)
        diagnostics["has_drop_rule"] = bool(fw_drop_output)
        
        # 6. Check DHCP lease
        dhcp_cmd = f"cat /tmp/dhcp.leases | grep -i '{device_mac}'"
        dhcp_output, _ = ssh_manager.execute_command(dhcp_cmd)
        diagnostics["dhcp_lease"] = dhcp_output.strip() if dhcp_output else "No DHCP lease found"
        
        # 7. Check connection status
        conn_cmd = f"ip neigh show | grep -i '{device_ip}'"
        conn_output, _ = ssh_manager.execute_command(conn_cmd)
        diagnostics["connection_status"] = conn_output.strip() if conn_output else "Not connected"
        
        # 8. Check if the device can be pinged from the router
        ping_cmd = f"ping -c 1 -W 1 {device_ip}"
        ping_output, _ = ssh_manager.execute_command(ping_cmd)
        diagnostics["ping_result"] = "Reachable" if "1 received" in ping_output else "Unreachable"
        
        # 9. Check current firewall rules
        fw_rules_cmd = "uci show firewall | grep '@rule'"
        fw_rules_output, _ = ssh_manager.execute_command(fw_rules_cmd)
        diagnostics["all_firewall_rules"] = fw_rules_output.strip() if fw_rules_output else "No rules found"
        
        # 10. Execute emergency fixes
        
        # Fix: Make sure no block rules exist
        ssh_manager.execute_command(f"for rule in $(uci show firewall | grep '@rule' | grep 'Block' | grep -i '{device_mac}' | cut -d. -f2 | cut -d= -f1); do uci delete firewall.$rule; done")
        
        # Fix: Create a explicit allow rule with high priority
        fix_commands = [
            f"uci add firewall rule",
            f"uci set firewall.@rule[-1].name='EMERGENCY Allow {device_mac}'",
            f"uci set firewall.@rule[-1].src='lan'",
            f"uci set firewall.@rule[-1].dest='wan'",
            f"uci set firewall.@rule[-1].proto='all'",
            f"uci set firewall.@rule[-1].src_mac='{device_mac}'",
            f"uci set firewall.@rule[-1].target='ACCEPT'",
            f"uci set firewall.@rule[-1].enabled='1'",
            f"uci set firewall.@rule[-1].priority='1'" # Highest possible priority
        ]
        
        for cmd in fix_commands:
            ssh_manager.execute_command(cmd)
        
        # Ensure device is in WiFi allow lists
        wifi_fix_cmd = f"for iface in $(uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1); do uci add_list wireless.$iface.maclist='{device_mac}'; done"
        ssh_manager.execute_command(wifi_fix_cmd)
        
        # Apply all changes
        ssh_manager.execute_command("uci commit wireless")
        ssh_manager.execute_command("uci commit firewall")
        ssh_manager.execute_command("wifi reload")
        ssh_manager.execute_command("/etc/init.d/firewall reload")
        
        return jsonify(success("Emergency device fixes applied", data=diagnostics))
        
    except Exception as e:
        return jsonify(error(f"Diagnostic error: {str(e)}"))

@admin_bp.route("/api/admin/emergency_unblock", methods=["GET"])
def emergency_unblock_endpoint():
    """
    Emergency endpoint to unblock a specific device.
    Use with ?ip=x.x.x.x parameter to specify the device IP.
    """
    try:
        # Get the device IP from query parameter
        device_ip = request.args.get("ip")
        if not device_ip:
            return jsonify(error("Missing 'ip' query parameter"))
            
        # Get the device MAC
        from services.admin_protection import get_mac_from_ip
        device_mac = get_mac_from_ip(device_ip)
        
        if not device_mac:
            return jsonify(error(f"Could not find MAC address for IP {device_ip}"))
            
        # Execute emergency unblock measures
        
        # 1. Remove any block rules
        ssh_manager.execute_command(f"for rule in $(uci show firewall | grep '@rule' | grep -i '{device_mac}' | grep -i 'Block' | cut -d. -f2 | cut -d= -f1); do uci delete firewall.$rule; done")
        
        # 2. Add to WiFi allow lists
        ssh_manager.execute_command(f"for iface in $(uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1); do uci set wireless.$iface.macfilter='allow'; uci add_list wireless.$iface.maclist='{device_mac}'; done")
        
        # 3. Add high-priority firewall rule
        ssh_manager.execute_command(f"uci add firewall rule")
        ssh_manager.execute_command(f"uci set firewall.@rule[-1].name='EMERGENCY Allow {device_mac}'")
        ssh_manager.execute_command(f"uci set firewall.@rule[-1].src='lan'")
        ssh_manager.execute_command(f"uci set firewall.@rule[-1].dest='wan'")
        ssh_manager.execute_command(f"uci set firewall.@rule[-1].proto='all'")
        ssh_manager.execute_command(f"uci set firewall.@rule[-1].src_mac='{device_mac}'")
        ssh_manager.execute_command(f"uci set firewall.@rule[-1].target='ACCEPT'")
        ssh_manager.execute_command(f"uci set firewall.@rule[-1].enabled='1'")
        ssh_manager.execute_command(f"uci set firewall.@rule[-1].priority='1'") # Highest priority
        
        # Apply all changes
        ssh_manager.execute_command("uci commit wireless")
        ssh_manager.execute_command("uci commit firewall")
        ssh_manager.execute_command("wifi reload")
        ssh_manager.execute_command("/etc/init.d/firewall reload")
        
        # Verify that the rule was added
        verify_cmd = f"uci show firewall | grep -i 'EMERGENCY Allow {device_mac}'"
        verify_output, _ = ssh_manager.execute_command(verify_cmd)
        rule_added = bool(verify_output and device_mac.lower() in verify_output.lower())
        
        return jsonify(success(f"Emergency unblock applied for device {device_mac} ({device_ip}). Rule added: {rule_added}"))
        
    except Exception as e:
        return jsonify(error(f"Emergency unblock failed: {str(e)}")) 