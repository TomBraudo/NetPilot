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

# Register or update a new device
def register_device(ip, mac, hostname):
    """
    Register a device in the database using MAC as the primary key.
    If the device exists, update its IP and last_seen timestamp.
    
    Args:
        ip (str): The device's IP address
        mac (str): The device's MAC address (primary key)
        hostname (str): The device's hostname
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        now = datetime.utcnow().isoformat()
        
        # Check if device exists by MAC only
        existing = db_client.devices.get(Device.mac == mac)
        
        if existing:
            # Update existing device with new IP and timestamp
            db_client.devices.update({
                'ip': ip,
                'hostname': hostname,
                'last_seen': now
            }, Device.mac == mac)
            logger.info(f"Updated device {mac} with new IP {ip}")
        else:
            # Insert new device
            db_client.devices.insert({
                'mac': mac,
                'ip': ip,
                'hostname': hostname,
                'device_name': None,
                'first_seen': now,
                'last_seen': now
            })
            logger.info(f"Registered new device {mac} with IP {ip}")
            
            # Check if device is in any group
            GroupMember = Query()
            already_grouped = db_client.group_members.get(GroupMember.mac == mac)
            
            if not already_grouped:
                # Add to general group
                Group = Query()
                general_group = db_client.device_groups.get(Group.name == 'general')
                
                if general_group:
                    db_client.group_members.insert({
                        'mac': mac,
                        'ip': ip,
                        'group_id': general_group.doc_id
                    })
                    logger.info(f"Added device {mac} to general group")
        
        return True
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        return False

# Remove a device and all related data
def delete_device(mac, ip):
    """Delete a device and all its related data."""
    try:
        # Delete device rules
        db_client.device_rules.remove(Device.mac == mac)
        
        # Delete group memberships
        GroupMember = Query()
        db_client.group_members.remove(GroupMember.mac == mac)
        
        # Delete device
        db_client.devices.remove(Device.mac == mac)
        logger.info(f"Deleted device {mac} and all related data")
        return True
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        return False

# Get all devices
def get_all_devices():
    """Get all devices as a list of dictionaries."""
    try:
        return db_client.devices.all()
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return []

# Update device name by MAC address
def update_device_name(mac, ip, device_name):
    """Update a device's name by MAC address."""
    try:
        result = db_client.devices.update(
            {'device_name': device_name}, 
            Device.mac == mac
        )
        logger.info(f"Updated device name for {mac} to {device_name}")
        return len(result) > 0
    except Exception as e:
        logger.error(f"Error updating device name: {e}")
        return False

# Clear all devices from the database
def clear_devices():
    """Clear all devices and related data."""
    try:
        # Clear related tables first
        db_client.device_rules.truncate()
        db_client.group_members.truncate()
        
        # Then clear devices
        db_client.devices.truncate()
        logger.info("Cleared all devices and related data")
        return True
    except Exception as e:
        logger.error(f"Error clearing devices: {e}")
        return False

# Get device by MAC address
def get_device_by_mac(mac):
    """
    Retrieves a device record by its MAC address.
    Returns the most recently seen record if multiple exist.
    """
    try:
        # Get all devices with this MAC
        devices = db_client.devices.search(Device.mac == mac)
        
        if not devices:
            return None
            
        # Sort by last_seen (descending) and return the most recent
        return sorted(devices, key=lambda x: x.get('last_seen', ''), reverse=True)[0]
    except Exception as e:
        logger.error(f"Error getting device by MAC: {e}")
        return None

# Get MAC address from IP
def get_mac_from_ip(ip):
    """
    Retrieves the MAC address for a given IP address.
    Returns the most recently seen MAC if multiple exist.
    """
    try:
        # Get all devices with this IP
        devices = db_client.devices.search(Device.ip == ip)
        
        if not devices:
            return None
            
        # Sort by last_seen (descending) and return the most recent
        most_recent = sorted(devices, key=lambda x: x.get('last_seen', ''), reverse=True)[0]
        return most_recent.get('mac')
    except Exception as e:
        logger.error(f"Error getting MAC from IP: {e}")
        return None