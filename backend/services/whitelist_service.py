from utils.logging_config import get_logger
from utils.response_helpers import success
from utils.config_manager import config_manager
from services.bandwidth_mode import get_current_mode_value, set_current_mode_value
from services.reset_rules import reset_all_tc_rules
from utils.traffic_control_helpers import setup_traffic_rules
from datetime import datetime

logger = get_logger('services.whitelist')

# In-memory whitelist storage (will be replaced with session-based storage in Phase 1)
_whitelist_devices = {}

def get_whitelist_devices():
    """Get all devices in the whitelist"""
    formatted_devices = []
    for ip, device_info in _whitelist_devices.items():
        formatted_devices.append({
            "ip": ip,
            "mac": device_info.get("mac", "Unknown"),
            "hostname": device_info.get("hostname", "Unknown"),
            "last_seen": device_info.get("added_at", "Unknown")
        })
        
    return success(data=formatted_devices)

def _apply_whitelist_rules():
    """Helper to apply current whitelist rules."""
    logger.info("Applying whitelist TC rules.")
    whitelist_ips = list(_whitelist_devices.keys())
    
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
    """Add a device to the whitelist - upstream validation ensures this is valid"""
    _whitelist_devices[ip] = {
        "ip": ip,
        "mac": "Unknown",
        "hostname": "Unknown",
        "added_at": datetime.now().isoformat()
    }
    
    if get_current_mode_value() == 'whitelist':
        _apply_whitelist_rules()
    
    return success(message=f"Device {ip} added to whitelist")

def remove_device_from_whitelist(ip):
    """Remove a device from the whitelist - upstream validation ensures device exists"""
    del _whitelist_devices[ip]
    
    if get_current_mode_value() == 'whitelist':
        _apply_whitelist_rules()
    
    return success(message=f"Device {ip} removed from whitelist")

def clear_whitelist():
    """Clear all devices from the whitelist"""
    _whitelist_devices.clear()
    
    if get_current_mode_value() == 'whitelist':
        _apply_whitelist_rules()
    
    return success(message="Whitelist cleared")

def get_whitelist_limit_rate():
    """Get the current whitelist bandwidth limit rate"""
    config = config_manager.load_config('whitelist')
    return success(data={"rate": config.get('Limit_Rate', "50mbit")})

def format_rate(rate):
    """Format rate value to include units if not present"""
    if isinstance(rate, (int, float)) and not isinstance(rate, bool):
        return f"{rate}mbit"
    if isinstance(rate, str) and rate.isnumeric():
        return f"{rate}mbit"
    return str(rate)

def set_whitelist_limit_rate(rate):
    """Set the whitelist bandwidth limit rate"""
    formatted_r = format_rate(rate)
    config = config_manager.load_config('whitelist')
    config['Limit_Rate'] = formatted_r
    config_manager.save_config('whitelist', config)
    logger.info(f"Updated whitelist limit rate to {formatted_r}")
    
    if get_current_mode_value() == 'whitelist':
        _apply_whitelist_rules()
    
    return success(data={"rate": formatted_r})

def get_whitelist_full_rate():
    """Get the current whitelist full bandwidth rate"""
    config = config_manager.load_config('whitelist')
    return success(data={"rate": config.get('Full_Rate', "1000mbit")})

def set_whitelist_full_rate(rate):
    """Set the whitelist full bandwidth rate"""
    formatted_r = format_rate(rate)
    config = config_manager.load_config('whitelist')
    config['Full_Rate'] = formatted_r
    config_manager.save_config('whitelist', config)
    logger.info(f"Updated whitelist full rate to {formatted_r}")
    
    if get_current_mode_value() == 'whitelist':
        _apply_whitelist_rules()
        
    return success(data={"rate": formatted_r})

def activate_whitelist_mode():
    """Activate whitelist mode"""
    set_current_mode_value('whitelist')
    _apply_whitelist_rules()
    return success(message="Whitelist mode activated")

def deactivate_whitelist_mode():
    """Deactivate whitelist mode"""
    reset_all_tc_rules() 
    set_current_mode_value('none')
    return success(message="Whitelist mode deactivated")

def is_whitelist_mode():
    """Check if whitelist mode is active"""
    is_active = get_current_mode_value() == 'whitelist'
    return success(data={"active": is_active}) 