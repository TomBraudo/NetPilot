from utils.logging_config import get_logger
from utils.response_helpers import success
from utils.config_manager import config_manager
from services.mode_state_service import get_current_mode_value, set_current_mode_value
from db.tinydb_client import db_client
from db.whitelist_management import add_to_whitelist, remove_from_whitelist, get_whitelist
from services.reset_rules import reset_all_tc_rules
from tinydb import Query
# Import the new helper
from utils.traffic_control_helpers import setup_traffic_rules
# Import to get hostname from devices table
from db.device_repository import get_device_by_mac

logger = get_logger('services.whitelist')

# Get the whitelist table directly
whitelist_table = db_client.bandwidth_whitelist
Device = Query()

def get_whitelist_devices():
    """Get all devices in the whitelist"""
    try:
        # Get devices from the whitelist table
        devices = get_whitelist()
        
        # Format the response
        formatted_devices = []
        for device in devices:
            # Get the actual hostname from the devices table using MAC address
            device_info = get_device_by_mac(device.get("mac"))
            actual_hostname = device_info.get("hostname", "Unknown") if device_info else "Unknown"
            
            formatted_devices.append({
                "ip": device.get("ip"),
                "mac": device.get("mac"),
                "hostname": actual_hostname,  # Use hostname from devices table
                "last_seen": device.get("added_at")
            })
            
        return success(data=formatted_devices)
    except Exception as e:
        logger.error(f"Error getting whitelist: {str(e)}", exc_info=True)
        raise

def _apply_whitelist_rules():
    """Helper to apply current whitelist rules."""
    logger.info("Applying whitelist TC rules.")
    db_client.flush() 
    raw_whitelist_devices = get_whitelist()
    whitelist_ips = [device['ip'] for device in raw_whitelist_devices]
    
    limit_rate_config = get_whitelist_limit_rate()['data']['rate']
    full_rate_config = get_whitelist_full_rate()['data']['rate']

    setup_traffic_rules(
        mode='whitelist',
        ips_to_target=whitelist_ips,
        limit_rate=limit_rate_config,
        full_rate=full_rate_config
    )
    logger.info("Whitelist TC rules applied successfully.")


def add_device_to_whitelist(ip):
    """Add a device to the whitelist"""
    try:
        device = add_to_whitelist(ip) # This already handles DB interaction and potential ValueError
        
        if get_current_mode_value() == 'whitelist':
            _apply_whitelist_rules()
        
        return success(message=f"Device {ip} added to whitelist")
    except Exception as e:
        logger.error(f"Error adding device to whitelist: {str(e)}", exc_info=True)
        raise

def remove_device_from_whitelist(ip):
    """Remove a device from the whitelist"""
    try:
        # Ensure device exists before attempting DB removal to align with add_to_whitelist logic
        device_info = whitelist_table.get(Device.ip == ip)
        if not device_info:
            raise ValueError(f"Device with IP {ip} not found in whitelist")

        remove_from_whitelist(ip) # DB operation
        
        if get_current_mode_value() == 'whitelist':
            _apply_whitelist_rules()
        
        return success(message=f"Device {ip} removed from whitelist")
    except Exception as e:
        logger.error(f"Error removing device from whitelist: {str(e)}", exc_info=True)
        raise

def clear_whitelist():
    """Clear all devices from the whitelist"""
    try:
        # It's more efficient to clear TC rules once after all DB ops if mode is active
        devices_cleared = False
        current_devices = get_whitelist() # Get IPs before clearing
        
        if not current_devices:
             return success(message="Whitelist is already empty.")

        for device in current_devices:
            remove_from_whitelist(device["ip"]) # Just DB op
            devices_cleared = True
        
        if devices_cleared and get_current_mode_value() == 'whitelist':
            _apply_whitelist_rules() # Apply rules based on the now empty whitelist
        
        return success(message="Whitelist cleared")
    except Exception as e:
        logger.error(f"Error clearing whitelist: {str(e)}", exc_info=True)
        raise

def get_whitelist_limit_rate():
    """Get the current whitelist bandwidth limit rate"""
    try:
        config = config_manager.load_config('whitelist')
        return success(data={"rate": config.get('Limit_Rate', "50mbit")}) # Default if not set
    except Exception as e:
        logger.error(f"Error getting whitelist limit rate: {str(e)}", exc_info=True)
        raise

def format_rate(rate): # Keep format_rate here as it's used by set_whitelist_limit_rate etc.
    """Format rate value to include units if not present"""
    if isinstance(rate, (int, float)) and not isinstance(rate, bool): # Ensure not bool
        return f"{rate}mbit"
    if isinstance(rate, str) and rate.isnumeric(): # "100" -> "100mbit"
        return f"{rate}mbit"
    return str(rate) # "100mbit" -> "100mbit"


def set_whitelist_limit_rate(rate):
    """Set the whitelist bandwidth limit rate"""
    try:
        formatted_r = format_rate(rate)
        config = config_manager.load_config('whitelist')
        config['Limit_Rate'] = formatted_r
        config_manager.save_config('whitelist', config)
        logger.info(f"Updated whitelist limit rate to {formatted_r}")
        
        if get_current_mode_value() == 'whitelist':
            _apply_whitelist_rules()
        
        return success(data={"rate": formatted_r})
    except Exception as e:
        logger.error(f"Error setting whitelist limit rate: {str(e)}", exc_info=True)
        raise

def get_whitelist_full_rate():
    """Get the current whitelist full bandwidth rate"""
    try:
        config = config_manager.load_config('whitelist')
        return success(data={"rate": config.get('Full_Rate', "1000mbit")}) # Default if not set
    except Exception as e:
        logger.error(f"Error getting whitelist full rate: {str(e)}", exc_info=True)
        raise

def set_whitelist_full_rate(rate):
    """Set the whitelist full bandwidth rate"""
    try:
        formatted_r = format_rate(rate)
        config = config_manager.load_config('whitelist')
        config['Full_Rate'] = formatted_r
        config_manager.save_config('whitelist', config)
        logger.info(f"Updated whitelist full rate to {formatted_r}")
        
        if get_current_mode_value() == 'whitelist':
            _apply_whitelist_rules()
            
        return success(data={"rate": formatted_r})
    except Exception as e:
        logger.error(f"Error setting whitelist full rate: {str(e)}", exc_info=True)
        raise

def activate_whitelist_mode():
    """Activate whitelist mode"""
    try:
        set_current_mode_value('whitelist')
        _apply_whitelist_rules()
        return success(message="Whitelist mode activated")
    except Exception as e:
        logger.error(f"Error activating whitelist mode: {str(e)}", exc_info=True)
        # Attempt to revert mode if TC setup fails
        set_current_mode_value('none') 
        reset_all_tc_rules() # Clean up any partial rules
        logger.info("Reverted mode to 'none' due to activation error.")
        raise

def deactivate_whitelist_mode():
    """Deactivate whitelist mode"""
    try:
        reset_all_tc_rules() 
        set_current_mode_value('none')
        return success(message="Whitelist mode deactivated")
    except Exception as e:
        logger.error(f"Error deactivating whitelist mode: {str(e)}", exc_info=True)
        raise

def is_whitelist_mode_internal(): # Not used externally, can be removed if not needed
    """Check if whitelist mode is active (internal use)"""
    return get_current_mode_value() == 'whitelist'

def is_whitelist_mode():
    """Check if whitelist mode is active (API response)"""
    try:
        is_active = get_current_mode_value() == 'whitelist'
        return success(data={"active": is_active})
    except Exception as e:
        logger.error(f"Error checking whitelist mode: {str(e)}", exc_info=True)
        raise

# Removed get_all_network_interfaces, run_command, 
# setup_tc_on_interface, setup_tc_with_iptables as they are now in helpers 