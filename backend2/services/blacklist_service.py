# Stub implementation for blacklist service
# This is a placeholder that returns mock data

def add_device_to_blacklist(mac):
    """Adds a device to the blacklist if it's not already there."""
    if not mac: 
        return None, "MAC address is required."
    return f"Device {mac} added to blacklist.", None

def remove_device_from_blacklist(mac):
    """Removes a device from the blacklist if it exists."""
    if not mac: 
        return None, "MAC address is required."
    return f"Device {mac} removed from blacklist.", None

def activate_blacklist_mode():
    """Activates blacklist mode if not already active."""
    return "Blacklist mode activated.", None

def deactivate_blacklist_mode():
    """Deactivates any active mode."""
    return "Blacklist mode deactivated.", None

def set_blacklist_limit_rate(rate):
    """Sets the blacklist limited rate."""
    formatted_rate = f"{rate}kbit"
    return {"rate": formatted_rate}, None 