from utils.logging_config import get_logger
from utils.response_helpers import success
from utils.config_manager import config_manager
from services.bandwidth_mode import get_current_mode_value, set_current_mode_value
from services.reset_rules import reset_all_tc_rules
from utils.traffic_control_helpers import setup_traffic_rules
from datetime import datetime

logger = get_logger('services.blacklist')

# In-memory blacklist storage (will be replaced with session-based storage in Phase 1)
_blacklist_devices = {}

def get_blacklist_devices():
    """Get all devices in the blacklist"""
    formatted_devices = []
    for ip, device_info in _blacklist_devices.items():
        formatted_devices.append({
            "ip": ip,
            "mac": device_info.get("mac", "Unknown"),
            "hostname": device_info.get("hostname", "Unknown"),
            "last_seen": device_info.get("added_at", "Unknown")
        })
    return success(data=formatted_devices)

def _apply_blacklist_rules():
    """Helper to apply current blacklist rules."""
    logger.info("Applying blacklist TC rules.")
    blacklist_ips = list(_blacklist_devices.keys())
    
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
    """Add a device to the blacklist - upstream validation ensures this is valid"""
    _blacklist_devices[ip] = {
        "ip": ip,
        "mac": "Unknown",
        "hostname": "Unknown",
        "added_at": datetime.now().isoformat()
    }
    
    if get_current_mode_value() == 'blacklist':
        _apply_blacklist_rules()
    
    return success(message=f"Device {ip} added to blacklist")

def remove_device_from_blacklist(ip):
    """Remove a device from the blacklist - upstream validation ensures device exists"""
    del _blacklist_devices[ip]
    
    if get_current_mode_value() == 'blacklist':
        _apply_blacklist_rules()
    
    return success(message=f"Device {ip} removed from blacklist")

def clear_blacklist():
    """Clear all devices from the blacklist"""
    _blacklist_devices.clear()
    
    if get_current_mode_value() == 'blacklist':
        _apply_blacklist_rules()
    
    return success(message="Blacklist cleared")

def get_blacklist_limit_rate():
    """Get the current blacklist bandwidth limit rate"""
    config = config_manager.load_config('blacklist')
    return success(data={"rate": config.get('Limit_Rate', "2mbit")})

def format_rate(rate):
    """Format rate value to include units if not present"""
    if isinstance(rate, (int, float)) and not isinstance(rate, bool):
        return f"{rate}mbit"
    if isinstance(rate, str) and rate.isnumeric():
        return f"{rate}mbit"
    return str(rate)

def set_blacklist_limit_rate(rate):
    """Set the blacklist bandwidth limit rate"""
    formatted_r = format_rate(rate)
    config = config_manager.load_config('blacklist')
    config['Limit_Rate'] = formatted_r
    config_manager.save_config('blacklist', config)
    logger.info(f"Updated blacklist limit rate to {formatted_r}")
    
    if get_current_mode_value() == 'blacklist':
        _apply_blacklist_rules()
    
    return success(data={"rate": formatted_r})

def get_blacklist_full_rate():
    """Get the current blacklist full bandwidth rate"""
    config = config_manager.load_config('blacklist')
    return success(data={"rate": config.get('Full_Rate', "1000mbit")})

def set_blacklist_full_rate(rate):
    """Set the blacklist full bandwidth rate"""
    formatted_r = format_rate(rate)
    config = config_manager.load_config('blacklist')
    config['Full_Rate'] = formatted_r
    config_manager.save_config('blacklist', config)
    logger.info(f"Updated blacklist full rate to {formatted_r}")
    
    if get_current_mode_value() == 'blacklist':
        _apply_blacklist_rules()
        
    return success(data={"rate": formatted_r})

def activate_blacklist_mode():
    """Activate blacklist mode"""
    set_current_mode_value('blacklist')
    _apply_blacklist_rules()
    return success(message="Blacklist mode activated")

def deactivate_blacklist_mode():
    """Deactivate blacklist mode"""
    reset_all_tc_rules()
    set_current_mode_value('none')
    return success(message="Blacklist mode deactivated")

def is_blacklist_mode():
    """Check if blacklist mode is active"""
    is_active = get_current_mode_value() == 'blacklist'
    return success(data={"active": is_active}) 