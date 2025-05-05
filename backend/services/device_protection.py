import logging
from db.device_repository import mark_device_as_protected, is_device_protected
from utils.ssh_client import ssh_manager
from utils.response_helpers import success, error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_protected_devices():
    """
    Automatically protect critical devices like the router.
    Should be called during system initialization.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get router MAC address
        router_mac_cmd = "cat /sys/class/net/br-lan/address"
        router_mac, err = ssh_manager.execute_command(router_mac_cmd)
        
        if err or not router_mac:
            logger.error(f"Failed to get router MAC address: {err}")
            # Try alternate method
            router_mac_cmd = "ifconfig br-lan | grep -o -E '([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}'"
            router_mac, err = ssh_manager.execute_command(router_mac_cmd)
            
            if err or not router_mac:
                logger.error(f"Failed to get router MAC address (alternate method): {err}")
                return False
                
        router_mac = router_mac.strip().lower()
        
        # Mark router as protected
        if not is_device_protected(router_mac):
            success = mark_device_as_protected(router_mac, True)
            if success:
                logger.info(f"Router ({router_mac}) marked as protected")
            else:
                logger.error(f"Failed to mark router ({router_mac}) as protected")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error setting up protected devices: {str(e)}")
        return False

def protect_device(mac, protected=True):
    """
    Mark a device as protected or unprotected.
    
    Args:
        mac: MAC address of the device
        protected: True to protect, False to remove protection
        
    Returns:
        Dictionary with success/error status and message
    """
    try:
        if not mac:
            return error("MAC address is required")
            
        success = mark_device_as_protected(mac, protected)
        
        if success:
            action = "protected" if protected else "unprotected"
            return success(f"Device {mac} is now {action}")
        else:
            return error(f"Failed to {'protect' if protected else 'unprotect'} device {mac}")
            
    except Exception as e:
        logger.error(f"Error {'protecting' if protected else 'unprotecting'} device: {str(e)}")
        return error(f"Error {'protecting' if protected else 'unprotecting'} device: {str(e)}") 