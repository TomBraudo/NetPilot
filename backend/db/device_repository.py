from tinydb import Query
from db.tinydb_client import db_client
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TinyDB Query object
Device = Query()

# This function is no longer needed with TinyDB but kept as a no-op for compatibility
def init_db():
    """No-op function for compatibility with existing code."""
    pass

def get_mac_from_ip(ip):
    """
    Get the MAC address for a given IP address from the devices table.
    
    Args:
        ip (str): The IP address to look up
        
    Returns:
        str: The MAC address if found, None otherwise
    """
    try:
        device = db_client.devices.get(Device.ip == ip)
        if device:
            return device.get('mac')
        return None
    except Exception as e:
        logger.error(f"Error getting MAC for IP {ip}: {e}")
        return None

def register_device(ip, mac, hostname="Unknown"):
    """Register a new device or update an existing one based on MAC address."""
    try:
        Device = Query()
        existing_device_by_mac = db_client.devices.get(Device.mac == mac)

        if existing_device_by_mac:
            # Device with this MAC already exists.
            updates = {'last_seen': datetime.now().isoformat()}
            
            # Check if IP address has changed or was not set before
            if existing_device_by_mac.get('ip') != ip:
                updates['ip'] = ip
                # If IP changes, update hostname from the current scan as well
                updates['hostname'] = hostname 
            # Else (IP is the same), hostname is NOT updated, preserving any existing name.
            
            db_client.devices.update(updates, Device.mac == mac)
            logger.info(f"Updated existing device (MAC: {mac}) - IP: {ip}, Hostname: {existing_device_by_mac.get('hostname') if updates.get('hostname') is None else updates.get('hostname')}")
        else:
            # No device with this MAC exists - it's a new device.
            logger.info(f"Registering new device (MAC: {mac}) - IP: {ip}, Hostname: {hostname}")
            db_client.devices.insert({
                'ip': ip,
                'mac': mac,
                'hostname': hostname,
                'first_seen': datetime.now().isoformat(), # Add first_seen for new devices
                'last_seen': datetime.now().isoformat()
            })
        
        db_client.flush()
        return True
    except Exception as e:
        logger.error(f"Error registering device {ip} (MAC: {mac}): {str(e)}", exc_info=True)
        return False

def delete_device(mac, ip):
    """
    Delete a device and all its related data.
    
    Args:
        mac (str): The device's MAC address
        ip (str): The device's IP address
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Delete device
        db_client.devices.remove(Device.mac == mac)
        db_client.flush()  # Ensure changes are persisted
        
        logger.info(f"Deleted device {mac} and all related data")
        return True
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        return False

def get_all_devices():
    """
    Get all devices as a list of dictionaries.
    
    Returns:
        list: List of device dictionaries
    """
    try:
        devices = db_client.devices.all()
        db_client.flush()  # Ensure we have the latest data
        return devices
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return []

def update_device_name(mac, ip, device_name):
    """
    Update a device's name by MAC address.
    
    Args:
        mac (str): The device's MAC address
        ip (str): The device's IP address
        device_name (str): The new device name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        result = db_client.devices.update(
            {'device_name': device_name}, 
            Device.mac == mac
        )
        db_client.flush()  # Ensure changes are persisted
        logger.info(f"Updated device name for {mac} to {device_name}")
        return len(result) > 0
    except Exception as e:
        logger.error(f"Error updating device name: {e}")
        return False

def clear_devices():
    """
    Clear all devices and related data.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Then clear devices
        db_client.devices.truncate()
        db_client.flush()  # Ensure changes are persisted
        
        logger.info("Cleared all devices and related data")
        return True
    except Exception as e:
        logger.error(f"Error clearing devices: {e}")
        return False

def get_device_by_mac(mac):
    """
    Retrieves a device record by its MAC address.
    Returns the most recently seen record if multiple exist.
    
    Args:
        mac (str): The device's MAC address
        
    Returns:
        dict: The device record if found, None otherwise
    """
    try:
        device = db_client.devices.get(Device.mac == mac)
        db_client.flush()  # Ensure we have the latest data
        return device
    except Exception as e:
        logger.error(f"Error getting device by MAC {mac}: {e}")
        return None

def get_device_by_ip(ip):
    """
    Retrieves a device record by its IP address.
    Returns the most recently seen record if multiple exist.
    
    Args:
        ip (str): The device's IP address
        
    Returns:
        dict: The device record if found, None otherwise
    """
    try:
        device = db_client.devices.get(Device.ip == ip)
        db_client.flush()  # Ensure we have the latest data
        return device
    except Exception as e:
        logger.error(f"Error getting device by IP {ip}: {e}")
        return None