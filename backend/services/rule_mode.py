import logging
from db.config_repository import set_system_config, get_system_config
from utils.response_helpers import success, error
from utils.ssh_client import ssh_manager
from services.admin_protection import ensure_admin_device_protected

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
RULE_MODE_KEY = "rule_mode"
BLACKLIST_MODE = "blacklist"
WHITELIST_MODE = "whitelist"

def get_rule_mode():
    """
    Get the current rule mode (blacklist or whitelist).
    
    Returns:
        str: "blacklist" or "whitelist"
    """
    mode = get_system_config(RULE_MODE_KEY, BLACKLIST_MODE)
    return mode

def set_rule_mode(mode, client_ip=None):
    """
    Set the rule mode with admin device protection.
    Compatible with OpenWrt traffic rules approach.
    
    Args:
        mode: "blacklist" or "whitelist"
        client_ip: IP address of the client making the request (to protect from lockout)
        
    Returns:
        Dictionary with success/error status and message
    """
    try:
        if mode not in [BLACKLIST_MODE, WHITELIST_MODE]:
            return error(f"Invalid mode: {mode}. Must be '{BLACKLIST_MODE}' or '{WHITELIST_MODE}'")
            
        current_mode = get_rule_mode()
        
        # If mode is already set, just return success
        if current_mode == mode:
            return success(f"Rule mode is already set to {mode}")
        
        # CRITICAL: If switching to whitelist mode, first protect the client device
        if mode == WHITELIST_MODE and client_ip:
            logger.info(f"Pre-protecting client device with IP {client_ip} before switching to whitelist mode")
            
            # Get MAC from IP
            from services.admin_protection import get_mac_from_ip, register_admin_device
            client_mac = get_mac_from_ip(client_ip)
            
            if client_mac:
                # Register this device as admin for maximum protection
                register_admin_device(ip_address=client_ip, mac_address=client_mac)
                
                # Double-check: immediately protect this device in firewall and WiFi
                # Protect in WiFi
                wifi_cmd = f"for iface in $(uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1); do " \
                           f"uci set wireless.$iface.macfilter='allow'; " \
                           f"uci add_list wireless.$iface.maclist='{client_mac}'; done"
                ssh_manager.execute_command(wifi_cmd)
                ssh_manager.execute_command("uci commit wireless")
                
                # Protect in firewall - clear existing rules and add protection
                ssh_manager.execute_command("iptables -F FORWARD")
                ssh_manager.execute_command(f"iptables -I FORWARD 1 -m mac --mac-source {client_mac} -j ACCEPT")
                ssh_manager.execute_command("iptables-save > /etc/firewall.user")
                
                logger.info(f"Successfully pre-protected client device {client_mac} ({client_ip})")
            else:
                logger.warning(f"Could not find MAC for client IP {client_ip}, proceeding with caution")
                # Since we can't protect by MAC, create a safety switch back
                import threading
                
                def safety_switch_back():
                    logger.warning("Safety timer activated - switching back to blacklist mode")
                    set_system_config(RULE_MODE_KEY, BLACKLIST_MODE)
                    setup_blacklist_mode()
                
                # Set a 60-second timer to switch back if the client doesn't confirm access
                timer = threading.Timer(60.0, safety_switch_back)
                timer.daemon = True
                timer.start()
                logger.info("Set safety timer: will revert to blacklist in 60 seconds if not cancelled")
            
        # Set the new mode in configuration
        if set_system_config(RULE_MODE_KEY, mode):
            # Apply the new mode to OpenWrt
            if mode == WHITELIST_MODE:
                # For whitelist mode, we default to blocking all, with exceptions
                setup_whitelist_mode(client_ip=client_ip)
            else:
                # For blacklist mode, we default to allowing all, with exceptions
                setup_blacklist_mode()
                
            # After setting up the new mode, ensure admin device is protected
            from services.admin_protection import ensure_admin_device_protected
            ensure_admin_device_protected()
            
            return success(f"Rule mode set to {mode}, admin device protected")
        else:
            return error(f"Failed to set rule mode to {mode}")
            
    except Exception as e:
        logger.error(f"Error setting rule mode: {str(e)}")
        return error(f"Error setting rule mode: {str(e)}")

def setup_whitelist_mode(client_ip=None):
    """
    Setup OpenWrt for whitelist mode using OpenWrt's built-in traffic rules.
    
    Args:
        client_ip: IP address of the client making the request (to protect from lockout)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get admin MAC and also the client's MAC if available
        from services.admin_protection import get_admin_device_mac, get_mac_from_ip
        admin_mac = get_admin_device_mac()
        client_mac = get_mac_from_ip(client_ip) if client_ip else None
        
        # Log info
        logger.info(f"Setting up whitelist mode using OpenWrt traffic rules. Admin MAC: {admin_mac}, Client MAC: {client_mac}")
        
        # Critical safety check: If no admin MAC and no client MAC, don't enable whitelist mode
        if not admin_mac and not client_mac:
            logger.error("Aborting whitelist mode setup: No admin device registered and no client device identified")
            return False
        
        # Prepare protected MACs list
        protected_macs = []
        if admin_mac:
            protected_macs.append(admin_mac)
        if client_mac and client_mac != admin_mac:
            protected_macs.append(client_mac)
            # If client isn't admin, register for protection
            from db.device_repository import mark_device_as_protected
            mark_device_as_protected(client_mac, True)
        
        # First, remove any existing NetPilot rules
        cleanup_commands = [
            # Find and delete all NetPilot rules
            "for rule in $(uci show firewall | grep '@rule' | grep 'NetPilot' | cut -d. -f2 | cut -d= -f1); do "
            "uci delete firewall.$rule; done",
        ]
        
        for cmd in cleanup_commands:
            ssh_manager.execute_command(cmd)
        
        # Add traffic rules using UCI
        rule_commands = []
        
        # For each protected MAC, add a rule to allow traffic
        for idx, mac in enumerate(protected_macs):
            rule_name = f"netpilot_allow_{idx}"
            rule_commands.extend([
                f"uci add firewall rule",
                f"uci set firewall.@rule[-1].name='NetPilot Allow {mac}'",
                f"uci set firewall.@rule[-1].src='lan'",
                f"uci set firewall.@rule[-1].dest='wan'",
                f"uci set firewall.@rule[-1].proto='all'",
                f"uci set firewall.@rule[-1].src_mac='{mac}'",
                f"uci set firewall.@rule[-1].target='ACCEPT'",
                f"uci set firewall.@rule[-1].enabled='1'"
            ])
        
        # Add a rule to allow local network traffic
        rule_commands.extend([
            f"uci add firewall rule",
            f"uci set firewall.@rule[-1].name='NetPilot Allow Local'",
            f"uci set firewall.@rule[-1].src='lan'",
            f"uci set firewall.@rule[-1].dest='lan'",
            f"uci set firewall.@rule[-1].proto='all'",
            f"uci set firewall.@rule[-1].target='ACCEPT'",
            f"uci set firewall.@rule[-1].enabled='1'"
        ])
        
        # Add a default deny rule for everything else (whitelist mode)
        rule_commands.extend([
            f"uci add firewall rule",
            f"uci set firewall.@rule[-1].name='NetPilot Default Deny'",
            f"uci set firewall.@rule[-1].src='lan'",
            f"uci set firewall.@rule[-1].dest='wan'",
            f"uci set firewall.@rule[-1].proto='all'",
            f"uci set firewall.@rule[-1].target='REJECT'",
            f"uci set firewall.@rule[-1].enabled='1'"
        ])
        
        # Execute all rule commands
        for cmd in rule_commands:
            _, err = ssh_manager.execute_command(cmd)
            if err:
                logger.error(f"Error setting up traffic rule: {err}")
        
        # Setup WiFi filtering
        wifi_commands = []
        
        # Get all WiFi interfaces
        get_wifi_ifaces = "uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1"
        ifaces_output, _ = ssh_manager.execute_command(get_wifi_ifaces)
        
        if ifaces_output:
            for iface in ifaces_output.splitlines():
                if iface and iface.strip():
                    # Set to allow mode
                    wifi_commands.append(f"uci set wireless.{iface}.macfilter='allow'")
                    # Clear existing list
                    wifi_commands.append(f"uci delete wireless.{iface}.maclist 2>/dev/null")
                    # Add each protected MAC
                    for mac in protected_macs:
                        wifi_commands.append(f"uci add_list wireless.{iface}.maclist='{mac}'")
        
        # Apply WiFi commands
        for cmd in wifi_commands:
            _, err = ssh_manager.execute_command(cmd)
            if err:
                logger.error(f"Error setting up WiFi for whitelist mode: {err}")
        
        # Commit and apply all changes
        ssh_manager.execute_command("uci commit wireless")
        ssh_manager.execute_command("uci commit firewall")
        ssh_manager.execute_command("wifi reload")
        ssh_manager.execute_command("/etc/init.d/firewall reload")
        
        # Verify protection - check if rules were added
        for mac in protected_macs:
            verify_cmd = f"uci show firewall | grep -i '{mac}'"
            verify_output, _ = ssh_manager.execute_command(verify_cmd)
            
            if not verify_output or mac.lower() not in verify_output.lower():
                logger.error(f"CRITICAL: Device protection verification failed for {mac} in whitelist mode!")
                setup_blacklist_mode()  # Roll back to blacklist
                return False
        
        logger.info(f"Whitelist mode setup completed successfully using OpenWrt traffic rules")
        return True
    except Exception as e:
        logger.error(f"Error setting up whitelist mode: {e}")
        # Emergency fallback to blacklist mode
        try:
            setup_blacklist_mode()
        except:
            pass
        return False

def setup_blacklist_mode():
    """
    Setup OpenWrt for blacklist mode using OpenWrt's built-in traffic rules.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Setting up blacklist mode using OpenWrt traffic rules")
        
        # First, remove any existing NetPilot rules
        cleanup_commands = [
            # Find and delete all NetPilot rules
            "for rule in $(uci show firewall | grep '@rule' | grep 'NetPilot' | cut -d. -f2 | cut -d= -f1); do "
            "uci delete firewall.$rule; done",
        ]
        
        for cmd in cleanup_commands:
            ssh_manager.execute_command(cmd)
        
        # Configure WiFi interfaces for blacklist mode
        wifi_commands = [
            # For each wireless interface, set to 'deny' mode with empty list
            "for iface in $(uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1); do "
            "uci set wireless.$iface.macfilter='deny'; "
            "uci delete wireless.$iface.maclist 2>/dev/null; done",
        ]
        
        for cmd in wifi_commands:
            _, err = ssh_manager.execute_command(cmd)
            if err:
                logger.error(f"Error setting up WiFi for blacklist mode: {err}")
        
        # Commit and apply all changes
        ssh_manager.execute_command("uci commit wireless")
        ssh_manager.execute_command("wifi reload")
        ssh_manager.execute_command("uci commit firewall")
        ssh_manager.execute_command("/etc/init.d/firewall reload")
        
        logger.info("Blacklist mode setup completed successfully using OpenWrt traffic rules")
        return True
    except Exception as e:
        logger.error(f"Error setting up blacklist mode: {e}")
        return False 