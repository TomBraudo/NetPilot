from utils.logging_config import get_logger
from utils.response_helpers import success
from utils.config_manager import config_manager
from services.mode_state_service import get_current_mode_value, set_current_mode_value
from db.tinydb_client import db_client
from db.blacklist_management import add_to_blacklist, remove_from_blacklist, get_blacklist
from services.reset_rules import reset_all_tc_rules
from tinydb import Query
# Import the new helper
from utils.traffic_control_helpers import setup_traffic_rules
# Import to get hostname from devices table
from db.device_repository import get_device_by_mac

logger = get_logger('services.blacklist')

# Get the blacklist table directly
blacklist_table = db_client.bandwidth_blacklist
Device = Query()

def get_blacklist_devices():
    """Get all devices in the blacklist"""
    try:
        devices = get_blacklist()
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
        logger.error(f"Error getting blacklist: {str(e)}", exc_info=True)
        raise

def _apply_blacklist_rules():
    """Helper to apply current blacklist rules."""
    logger.info("Applying blacklist TC rules.")
    db_client.flush()
    raw_blacklist_devices = get_blacklist()
    blacklist_ips = [device['ip'] for device in raw_blacklist_devices]
    
    limit_rate_config = get_blacklist_limit_rate()['data']['rate']
    full_rate_config = get_blacklist_full_rate()['data']['rate']

    setup_traffic_rules(
        mode='blacklist',
        ips_to_target=blacklist_ips,
        limit_rate=limit_rate_config,
        full_rate=full_rate_config
    )
    logger.info("Blacklist TC rules applied successfully.")

def add_device_to_blacklist(ip):
    """Add a device to the blacklist"""
    try:
        device = add_to_blacklist(ip)
        
        if get_current_mode_value() == 'blacklist':
            _apply_blacklist_rules()
        
        return success(message=f"Device {ip} added to blacklist")
    except Exception as e:
        logger.error(f"Error adding device to blacklist: {str(e)}", exc_info=True)
        raise

def remove_device_from_blacklist(ip):
    """Remove a device from the blacklist"""
    try:
        device_info = blacklist_table.get(Device.ip == ip)
        if not device_info:
            raise ValueError(f"Device with IP {ip} not found in blacklist")

        remove_from_blacklist(ip)
        
        if get_current_mode_value() == 'blacklist':
            _apply_blacklist_rules()
        
        return success(message=f"Device {ip} removed from blacklist")
    except Exception as e:
        logger.error(f"Error removing device from blacklist: {str(e)}", exc_info=True)
        raise

def clear_blacklist():
    """Clear all devices from the blacklist"""
    try:
        devices_cleared = False
        current_devices = get_blacklist()

        if not current_devices:
            return success(message="Blacklist is already empty.")

        for device in current_devices:
            remove_from_blacklist(device["ip"])
            devices_cleared = True
        
        if devices_cleared and get_current_mode_value() == 'blacklist':
            _apply_blacklist_rules() # Apply rules based on the now empty blacklist
        
        return success(message="Blacklist cleared")
    except Exception as e:
        logger.error(f"Error clearing blacklist: {str(e)}", exc_info=True)
        raise

def get_blacklist_limit_rate():
    """Get the current blacklist bandwidth limit rate"""
    try:
        config = config_manager.load_config('blacklist')
        return success(data={"rate": config.get('Limit_Rate', "2mbit")}) # Default if not set
    except Exception as e:
        logger.error(f"Error getting blacklist limit rate: {str(e)}", exc_info=True)
        raise

def format_rate(rate):
    """Format rate value to include units if not present"""
    if isinstance(rate, (int, float)) and not isinstance(rate, bool):
        return f"{rate}mbit"
    if isinstance(rate, str) and rate.isnumeric():
        return f"{rate}mbit"
    return str(rate)

def set_blacklist_limit_rate(rate):
    """Set the blacklist bandwidth limit rate"""
    try:
        formatted_r = format_rate(rate)
        config = config_manager.load_config('blacklist')
        config['Limit_Rate'] = formatted_r
        config_manager.save_config('blacklist', config)
        logger.info(f"Updated blacklist limit rate to {formatted_r}")
        
        if get_current_mode_value() == 'blacklist':
            _apply_blacklist_rules()
        
        return success(data={"rate": formatted_r})
    except Exception as e:
        logger.error(f"Error setting blacklist limit rate: {str(e)}", exc_info=True)
        raise

def get_blacklist_full_rate():
    """Get the current blacklist full bandwidth rate"""
    try:
        config = config_manager.load_config('blacklist')
        return success(data={"rate": config.get('Full_Rate', "1000mbit")}) # Default if not set
    except Exception as e:
        logger.error(f"Error getting blacklist full rate: {str(e)}", exc_info=True)
        raise

def set_blacklist_full_rate(rate):
    """Set the blacklist full bandwidth rate"""
    try:
        formatted_r = format_rate(rate)
        config = config_manager.load_config('blacklist')
        config['Full_Rate'] = formatted_r
        config_manager.save_config('blacklist', config)
        logger.info(f"Updated blacklist full rate to {formatted_r}")
        
        if get_current_mode_value() == 'blacklist':
            _apply_blacklist_rules()
            
        return success(data={"rate": formatted_r})
    except Exception as e:
        logger.error(f"Error setting blacklist full rate: {str(e)}", exc_info=True)
        raise

def activate_blacklist_mode():
    """Activate blacklist mode"""
    try:
        set_current_mode_value('blacklist')
        _apply_blacklist_rules()
        return success(message="Blacklist mode activated")
    except Exception as e:
        logger.error(f"Error activating blacklist mode: {str(e)}", exc_info=True)
        set_current_mode_value('none') 
        reset_all_tc_rules()
        logger.info("Reverted mode to 'none' due to activation error.")
        raise

def deactivate_blacklist_mode():
    """Deactivate blacklist mode"""
    try:
        reset_all_tc_rules()
        set_current_mode_value('none')
        return success(message="Blacklist mode deactivated")
    except Exception as e:
        logger.error(f"Error deactivating blacklist mode: {str(e)}", exc_info=True)
        raise

def is_blacklist_mode():
    """Check if blacklist mode is active (API response)"""
    try:
        is_active = get_current_mode_value() == 'blacklist'
        return success(data={"active": is_active})
    except Exception as e:
        logger.error(f"Error checking blacklist mode: {str(e)}", exc_info=True)
        raise

# Removed get_all_network_interfaces, run_command, 
# setup_tc_on_interface, setup_tc_with_iptables as they are now in helpers 