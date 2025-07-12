# Stub implementation for whitelist service
# This is a placeholder that returns mock data

def add_device_to_whitelist(mac):
    """Adds a device to the whitelist if it's not already there."""
    if not mac: 
        return None, "MAC address is required."
    return f"Device {mac} added to whitelist.", None

def remove_device_from_whitelist(mac):
    """Removes a device from the whitelist if it exists."""
    if not mac: 
        return None, "MAC address is required."
    return f"Device {mac} removed from whitelist.", None

def activate_whitelist_mode():
    """Activates whitelist mode if not already active."""
    return "Whitelist mode activated.", None

def deactivate_whitelist_mode():
    """Deactivates any active mode."""
    return "Whitelist mode deactivated.", None

def set_whitelist_limit_rate(rate):
    """Sets the whitelist limited rate."""
    formatted_rate = f"{rate}kbit"
    return {"rate": formatted_rate}, None

def set_whitelist_full_rate(rate):
    """Sets the whitelist full rate."""
    formatted_rate = f"{rate}mbit"
    return {"rate": formatted_rate}, None

def get_whitelist():
    """Gets the current whitelist state."""
    return {
        "devices": ["00:11:22:33:44:55", "AA:BB:CC:DD:EE:FF"],
        "active_mode": "whitelist",
        "rates": {
            "limited_rate": "100kbit",
            "full_rate": "10mbit"
        }
    }, None 