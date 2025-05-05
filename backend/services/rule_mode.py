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

def set_rule_mode(mode):
    """
    Set the rule mode with admin device protection.
    
    Args:
        mode: "blacklist" or "whitelist"
        
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
            
        # Set the new mode
        if set_system_config(RULE_MODE_KEY, mode):
            # Apply the new mode to OpenWrt
            if mode == WHITELIST_MODE:
                # For whitelist mode, we default to blocking all, with exceptions
                # Update the WiFi settings to block all by default
                setup_whitelist_mode()
            else:
                # For blacklist mode, we default to allowing all, with exceptions
                setup_blacklist_mode()
                
            # After setting up the new mode, ensure admin device is protected
            ensure_admin_device_protected()
            
            return success(f"Rule mode set to {mode}, admin device protected")
        else:
            return error(f"Failed to set rule mode to {mode}")
            
    except Exception as e:
        logger.error(f"Error setting rule mode: {str(e)}")
        return error(f"Error setting rule mode: {str(e)}")

def setup_whitelist_mode():
    """
    Setup OpenWrt for whitelist mode with admin protection.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get admin MAC
        from services.admin_protection import get_admin_device_mac
        admin_mac = get_admin_device_mac()
        
        # For whitelist mode, we switch the MAC filter to 'allow' and ensure blocklist is initially empty
        commands = [
            # For each wireless interface, set to 'allow' mode with empty list
            "for iface in $(uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1); do "
            "uci set wireless.$iface.macfilter='allow'; "
            "uci delete wireless.$iface.maclist; done",
            
            # Commit changes
            "uci commit wireless",
            
            # Add firewall default rule to block all
            "iptables -F FORWARD", # Clear existing forward rules
            "iptables -A FORWARD -j DROP", # Default to dropping all traffic
            
            # Save firewall changes
            "iptables-save > /etc/firewall.user",
            
            # Apply changes
            "wifi reload"
        ]
        
        # Add admin device to allowed list if available
        if admin_mac:
            commands.insert(0, 
                f"for iface in $(uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1); do "
                f"uci add_list wireless.$iface.maclist='{admin_mac}'; done"
            )
            # And add firewall exception
            commands.append(f"iptables -I FORWARD 1 -m mac --mac-source {admin_mac} -j ACCEPT")
        
        for cmd in commands:
            _, err = ssh_manager.execute_command(cmd)
            if err:
                logger.error(f"Error setting up whitelist mode: {err}")
                return False
                
        return True
    except Exception as e:
        logger.error(f"Error setting up whitelist mode: {e}")
        return False

def setup_blacklist_mode():
    """
    Setup OpenWrt for blacklist mode - allow all by default, block exceptions.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # For blacklist mode, we switch the MAC filter to 'deny'
        commands = [
            # For each wireless interface, set to 'deny' mode
            "for iface in $(uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1); do "
            "uci set wireless.$iface.macfilter='deny'; done",
            
            # Commit changes
            "uci commit wireless",
            
            # Remove any default block rules from firewall
            "iptables -F FORWARD", # Clear existing forward rules
            "iptables -P FORWARD ACCEPT", # Default to accepting
            
            # Save firewall changes
            "iptables-save > /etc/firewall.user",
            
            # Apply changes
            "wifi reload"
        ]
        
        for cmd in commands:
            _, err = ssh_manager.execute_command(cmd)
            if err:
                logger.error(f"Error setting up blacklist mode: {err}")
                return False
                
        return True
    except Exception as e:
        logger.error(f"Error setting up blacklist mode: {e}")
        return False 