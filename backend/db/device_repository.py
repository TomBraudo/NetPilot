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

def register_device(mac, ip, hostname=None, device_type=None):
    """
    Register a device in the database or update if it exists.
    
    Args:
        mac: Device MAC address
        ip: Device IP address
        hostname: Device hostname (optional)
        device_type: Type of device (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        now = datetime.utcnow().isoformat()
        
        # Check if device exists
        existing = db_client.devices.get(Device.mac == mac)
        
        if existing:
            # Update existing device
            update_data = {
                'ip': ip,
                'last_seen': now
            }
            
            # Only update hostname if provided and meaningful
            if hostname and hostname != "Unknown":
                update_data['hostname'] = hostname
                
            # Only update device_type if provided
            if device_type:
                update_data['device_type'] = device_type
                
            db_client.devices.update(update_data, Device.mac == mac)
        else:
            # Insert new device
            device_data = {
                'mac': mac, 
                'ip': ip,
                'first_seen': now,
                'last_seen': now,
                'block': False,
                'bandwidth_limit': 0,
                'access_schedule': "",
                'qos_priority': 0
            }
            
            # Add optional fields if provided
            if hostname and hostname != "Unknown":
                device_data['hostname'] = hostname
            if device_type:
                device_data['device_type'] = device_type
                
            db_client.devices.insert(device_data)
            
            # Add to general group by default
            from db.group_repository import add_device_to_group
            add_device_to_group(mac, 'general')
        
        return True
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        return False

def update_device_rules(mac, block=None, bandwidth_limit=None, access_schedule=None, qos_priority=None):
    """
    Update device's network rules.
    
    Args:
        mac: Device MAC address
        block: Boolean indicating if device is blocked
        bandwidth_limit: Bandwidth limit in Mbps
        access_schedule: Schedule string for time-based access
        qos_priority: QoS priority (1-5)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Build update dictionary with only provided values
        update_data = {}
        if block is not None:
            update_data['block'] = block
        if bandwidth_limit is not None:
            update_data['bandwidth_limit'] = bandwidth_limit
        if access_schedule is not None:
            update_data['access_schedule'] = access_schedule
        if qos_priority is not None:
            update_data['qos_priority'] = qos_priority
            
        if not update_data:
            return True  # Nothing to update
            
        # Update the device
        result = db_client.devices.update(update_data, Device.mac == mac)
        return len(result) > 0
    except Exception as e:
        logger.error(f"Error updating device rules: {e}")
        return False

def update_device_info(mac, device_name=None, notes=None, hostname=None, device_type=None):
    """
    Update device information fields.
    
    Args:
        mac: Device MAC address
        device_name: User-assigned name for the device
        notes: Additional notes about the device
        hostname: Device's network hostname
        device_type: Type of device
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Build update dictionary with only provided values
        update_data = {}
        if device_name is not None:
            update_data['device_name'] = device_name
        if notes is not None:
            update_data['notes'] = notes
        if hostname is not None and hostname != "Unknown":
            update_data['hostname'] = hostname
        if device_type is not None:
            update_data['device_type'] = device_type
            
        if not update_data:
            return True  # Nothing to update
            
        # Update the device
        result = db_client.devices.update(update_data, Device.mac == mac)
        return len(result) > 0
    except Exception as e:
        logger.error(f"Error updating device info: {e}")
        return False

def get_device(mac):
    """
    Get detailed device information by MAC address.
    
    Args:
        mac: Device MAC address
    
    Returns:
        dict: Device information or None if not found
    """
    try:
        device = db_client.devices.get(Device.mac == mac)
        
        if not device:
            return None
            
        # Get device group information
        GroupMember = Query()
        membership = db_client.group_members.get(GroupMember.mac == mac)
        
        if membership:
            group_id = membership.get('group_id')
            Group = Query()
            group = db_client.device_groups.get(doc_id=group_id)
            if group:
                device['group_name'] = group.get('name')
        
        return device
    except Exception as e:
        logger.error(f"Error getting device: {e}")
        return None

def get_all_devices(with_groups=False):
    """
    Get all devices with optional group information.
    
    Args:
        with_groups: Whether to include group information
    
    Returns:
        list: List of device dictionaries
    """
    try:
        devices = db_client.devices.all()
        
        if with_groups:
            # Get all group memberships
            memberships = db_client.group_members.all()
            membership_by_mac = {}
            for m in memberships:
                membership_by_mac[m.get('mac')] = m.get('group_id')
            
            # Get all groups
            groups = db_client.device_groups.all()
            group_by_id = {}
            for g in groups:
                group_by_id[g.doc_id] = g.get('name')
            
            # Add group to each device
            for device in devices:
                mac = device.get('mac')
                group_id = membership_by_mac.get(mac)
                if group_id:
                    device['group_name'] = group_by_id.get(group_id, 'Unknown')
                else:
                    device['group_name'] = 'Ungrouped'
        
        return devices
    except Exception as e:
        logger.error(f"Error getting all devices: {e}")
        return []

def mark_device_activity(mac):
    """
    Update the last_seen timestamp for a device.
    
    Args:
        mac: Device MAC address
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        now = datetime.utcnow().isoformat()
        result = db_client.devices.update({'last_seen': now}, Device.mac == mac)
        return len(result) > 0
    except Exception as e:
        logger.error(f"Error marking device activity: {e}")
        return False

def delete_device(mac):
    """
    Delete a device and all associated data.
    
    Args:
        mac: Device MAC address
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Remove device from groups
        GroupMember = Query()
        db_client.group_members.remove(GroupMember.mac == mac)
        
        # Delete device
        db_client.devices.remove(Device.mac == mac)
        return True
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        return False

def get_blocked_devices():
    """
    Get all devices that are currently blocked.
    
    Returns:
        list: List of blocked device dictionaries
    """
    try:
        return db_client.devices.search(Device.block == True)
    except Exception as e:
        logger.error(f"Error getting blocked devices: {e}")
        return []

def get_devices_with_rules():
    """
    Get all devices that have any rule applied.
    
    Returns:
        list: List of device dictionaries with rules
    """
    try:
        devices = []
        all_devices = db_client.devices.all()
        
        for device in all_devices:
            has_rules = False
            # Check if any rule is non-default
            if device.get('block', False):
                has_rules = True
            if device.get('bandwidth_limit', 0) > 0:
                has_rules = True
            if device.get('access_schedule'):
                has_rules = True
            if device.get('qos_priority', 0) > 0:
                has_rules = True
                
            if has_rules:
                devices.append(device)
                
        return devices
    except Exception as e:
        logger.error(f"Error getting devices with rules: {e}")
        return []

def get_device_by_ip(ip):
    """
    Find a device by IP address.
    
    Args:
        ip: Device IP address
    
    Returns:
        dict: Device information or None if not found
    """
    try:
        return db_client.devices.get(Device.ip == ip)
    except Exception as e:
        logger.error(f"Error getting device by IP: {e}")
        return None

# Update device name by MAC address
def update_device_name(mac, device_name):
    """Update a device's name by MAC address."""
    try:
        result = db_client.devices.update(
            {'device_name': device_name}, 
            Device.mac == mac
        )
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
        return True
    except Exception as e:
        logger.error(f"Error clearing devices: {e}")
        return False

# Get mac address from IP
def get_mac_from_ip(ip):
    """Get MAC address for a given IP address."""
    try:
        device = db_client.devices.get(Device.ip == ip)
        return device['mac'] if device else None
    except Exception as e:
        logger.error(f"Error getting MAC from IP: {e}")
        return None

# Get device by MAC address
def get_device_by_mac(mac):
    """
    Retrieves a device record by its MAC address.
    If multiple records exist for the same MAC, returns the most recently seen.
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