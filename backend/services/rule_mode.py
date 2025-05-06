import logging
from db.config_repository import set_system_config, get_system_config
from utils.response_helpers import success, error
from utils.ssh_client import ssh_manager
from services.admin_protection import ensure_admin_device_protected

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants - only blacklist mode is supported now
RULE_MODE_KEY = "rule_mode"
BLACKLIST_MODE = "blacklist"

def get_rule_mode():
    """
    Get the current rule mode (always returns blacklist).
    
    Returns:
        str: "blacklist"
    """
    return BLACKLIST_MODE

def set_rule_mode(mode, client_ip=None):
    """
    Set the rule mode (now always defaults to blacklist).
    
    Args:
        mode: Ignored, always sets to blacklist
        client_ip: Ignored, no longer used
        
    Returns:
        Dictionary with success status
    """
    try:
        # Always set to blacklist mode
        set_system_config(RULE_MODE_KEY, BLACKLIST_MODE)
        
        # Setup blacklist mode
        setup_blacklist_mode()
        
        # Ensure admin device is protected
        ensure_admin_device_protected()
        
        return success(f"Rule mode set to {BLACKLIST_MODE}")
    except Exception as e:
        logger.error(f"Error setting rule mode: {str(e)}")
        return error(f"Error setting rule mode: {str(e)}")

def setup_blacklist_mode():
    """
    Setup OpenWrt for blacklist mode.
    """
    try:
        # First, remove any existing NetPilot rules
        ssh_manager.execute_command(
            "for rule in $(uci show firewall | grep '@rule' | grep 'NetPilot' | cut -d. -f2 | cut -d= -f1); do "
            "uci delete firewall.$rule; done"
        )
        
        # Setup WiFi interfaces for blacklist mode (deny specific MACs)
        ssh_manager.execute_command(
            "for iface in $(uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1); do "
            "uci set wireless.$iface.macfilter='deny'; done"
        )
        
        # Apply changes
        ssh_manager.execute_command("uci commit wireless")
        ssh_manager.execute_command("uci commit firewall")
        ssh_manager.execute_command("wifi reload")
        ssh_manager.execute_command("/etc/init.d/firewall reload")
        
        logger.info("Blacklist mode setup completed")
        return True
    except Exception as e:
        logger.error(f"Error setting up blacklist mode: {str(e)}")
        return False 