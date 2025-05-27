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
    """Register a new device or update an existing one"""
    try:
        Device = Query()
        device = db_client.devices.get((Device.ip == ip) | (Device.mac == mac))
        
        if device:
            # Update existing device
            db_client.devices.update({
                'ip': ip,
                'mac': mac,
                'hostname': hostname,
                'last_seen': datetime.now().isoformat()
            }, (Device.ip == ip) | (Device.mac == mac))
        else:
            # Add new device
            db_client.devices.insert({
                'ip': ip,
                'mac': mac,
                'hostname': hostname,
                'last_seen': datetime.now().isoformat()
            })
        
        return True
    except Exception as e:
        logger.error(f"Error registering device {ip}: {str(e)}", exc_info=True)
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
        # Delete device rules
        db_client.device_rules.remove(Device.mac == mac)
        
        # Delete group memberships
        GroupMember = Query()
        db_client.group_members.remove(GroupMember.mac == mac)
        
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
        # Clear related tables first
        db_client.device_rules.truncate()
        db_client.group_members.truncate()
        
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