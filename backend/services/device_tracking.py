def track_device_macs(device_name, primary_mac):
    """
    Track multiple MAC addresses for a device with randomization.
    Call this whenever a new device connects.
    
    Args:
        device_name: Human-readable name of the device
        primary_mac: Primary MAC address of the device
    """
    # Implementation to store in DB...
    
def get_all_device_macs(primary_mac):
    """
    Get all known MAC addresses for a device.
    
    Args:
        primary_mac: Primary MAC address of the device
        
    Returns:
        list: All known MAC addresses for this device
    """
    # Implementation to retrieve from DB... 