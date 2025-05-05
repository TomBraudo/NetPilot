from tinydb import Query
from db.tinydb_client import db_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TinyDB Query objects
Group = Query()
GroupMember = Query()

def get_all_groups():
    """
    Get all device groups.
    
    Returns:
        list: List of group dictionaries
    """
    try:
        return db_client.device_groups.all()
    except Exception as e:
        logger.error(f"Error getting all groups: {e}")
        return []

def create_group(name, description=None):
    """
    Create a new device group.
    
    Args:
        name: Group name
        description: Optional group description
    
    Returns:
        int: Group ID if successful, None otherwise
    """
    try:
        # Check if group already exists
        existing = db_client.device_groups.get(Group.name == name)
        if existing:
            return existing.doc_id
            
        # Create new group
        group_data = {
            'name': name,
            'description': description,
            'is_blacklist': False,  # Default to whitelist mode
            'enable_internet': True  # Whether internet access is enabled for this group
        }
        
        group_id = db_client.device_groups.insert(group_data)
        return group_id
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        return None

def get_group(name):
    """
    Get group by name.
    
    Args:
        name: Name of the group
    
    Returns:
        dict: Group information or None if not found
    """
    try:
        return db_client.device_groups.get(Group.name == name)
    except Exception as e:
        logger.error(f"Error getting group: {e}")
        return None

def update_group(name, new_name=None, description=None, is_blacklist=None, enable_internet=None):
    """
    Update group information.
    
    Args:
        name: Current group name
        new_name: New group name (optional)
        description: Group description (optional)
        is_blacklist: Whether this is a blacklist (optional)
        enable_internet: Whether internet access is enabled (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Build update dictionary
        update_data = {}
        if new_name:
            update_data['name'] = new_name
        if description is not None:
            update_data['description'] = description
        if is_blacklist is not None:
            update_data['is_blacklist'] = is_blacklist
        if enable_internet is not None:
            update_data['enable_internet'] = enable_internet
            
        if not update_data:
            return True  # Nothing to update
            
        # Update the group
        result = db_client.device_groups.update(update_data, Group.name == name)
        return len(result) > 0
    except Exception as e:
        logger.error(f"Error updating group: {e}")
        return False

def delete_group(name):
    """
    Delete a group. Moves all devices to 'general' group.
    Cannot delete the 'general' group.
    
    Args:
        name: Name of the group to delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Cannot delete 'general' group
        if name.lower() == 'general':
            return False
            
        # Get group to delete
        group = db_client.device_groups.get(Group.name == name)
        if not group:
            return False
            
        # Get 'general' group
        general_group = db_client.device_groups.get(Group.name == 'general')
        if not general_group:
            # Create 'general' group if it doesn't exist
            general_id = create_group('general', 'Default group for all devices')
        else:
            general_id = general_group.doc_id
            
        # Move all devices to 'general' group
        db_client.group_members.update(
            {'group_id': general_id},
            GroupMember.group_id == group.doc_id
        )
        
        # Delete the group
        db_client.device_groups.remove(doc_ids=[group.doc_id])
        return True
    except Exception as e:
        logger.error(f"Error deleting group: {e}")
        return False

def add_device_to_group(mac, group_name):
    """
    Add a device to a group. Removes from current group if any.
    
    Args:
        mac: Device MAC address
        group_name: Name of the group to add to
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get or create group
        group = db_client.device_groups.get(Group.name == group_name)
        if not group:
            group_id = create_group(group_name)
            if not group_id:
                return False
        else:
            group_id = group.doc_id
            
        # Check if device is already in a group
        current_membership = db_client.group_members.get(GroupMember.mac == mac)
        
        if current_membership:
            # Update existing membership
            db_client.group_members.update(
                {'group_id': group_id},
                GroupMember.mac == mac
            )
        else:
            # Create new membership
            db_client.group_members.insert({
                'mac': mac,
                'group_id': group_id
            })
            
        return True
    except Exception as e:
        logger.error(f"Error adding device to group: {e}")
        return False

def remove_device_from_group(mac, group_name=None):
    """
    Remove a device from a group.
    
    Args:
        mac: Device MAC address
        group_name: Name of the group (if None, removes from any group)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if group_name:
            # Remove from specific group
            group = db_client.device_groups.get(Group.name == group_name)
            if not group:
                return False
                
            db_client.group_members.remove(
                (GroupMember.mac == mac) & 
                (GroupMember.group_id == group.doc_id)
            )
        else:
            # Remove from any group
            db_client.group_members.remove(GroupMember.mac == mac)
            
        return True
    except Exception as e:
        logger.error(f"Error removing device from group: {e}")
        return False

def get_devices_in_group(group_name):
    """
    Get all devices in a group.
    
    Args:
        group_name: Name of the group
    
    Returns:
        list: List of device dictionaries in the group
    """
    try:
        # Get group
        group = db_client.device_groups.get(Group.name == group_name)
        if not group:
            return []
            
        # Get device memberships
        members = db_client.group_members.search(GroupMember.group_id == group.doc_id)
        if not members:
            return []
            
        # Get device details
        result = []
        Device = Query()
        for member in members:
            mac = member.get('mac')
            device = db_client.devices.get(Device.mac == mac)
            if device:
                # Include group name in device
                device['group_name'] = group_name
                result.append(device)
                
        return result
    except Exception as e:
        logger.error(f"Error getting devices in group: {e}")
        return []

def get_device_group(mac):
    """
    Get the group a device belongs to.
    
    Args:
        mac: Device MAC address
    
    Returns:
        dict: Group information or None if not found
    """
    try:
        # Get device membership
        membership = db_client.group_members.get(GroupMember.mac == mac)
        if not membership:
            return None
            
        # Get group
        group_id = membership.get('group_id')
        group = db_client.device_groups.get(doc_id=group_id)
        return group
    except Exception as e:
        logger.error(f"Error getting device group: {e}")
        return None

def apply_rules_to_group(group_name, rules):
    """
    Apply rules to all devices in a group.
    
    Args:
        group_name: Name of the group
        rules: Dictionary of rule_name: value pairs
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get devices in group
        devices = get_devices_in_group(group_name)
        
        # Import here to avoid circular import
        from db.device_repository import update_device_rules
        
        # Apply rules to each device
        for device in devices:
            mac = device.get('mac')
            update_device_rules(
                mac,
                block=rules.get('block'),
                bandwidth_limit=rules.get('bandwidth_limit'),
                access_schedule=rules.get('access_schedule'),
                qos_priority=rules.get('qos_priority')
            )
            
        return True
    except Exception as e:
        logger.error(f"Error applying rules to group: {e}")
        return False

def set_group_blacklist_mode(group_name, is_blacklist):
    """
    Set a group to blacklist or whitelist mode.
    
    Args:
        group_name: Name of the group
        is_blacklist: True for blacklist, False for whitelist
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        Group = Query()
        group = db_client.device_groups.get(Group.name == group_name)
        
        if not group:
            logger.error(f"Group not found: {group_name}")
            return False
            
        db_client.device_groups.update({'is_blacklist': bool(is_blacklist)}, doc_ids=[group.doc_id])
        return True
    except Exception as e:
        logger.error(f"Error setting group blacklist mode: {e}")
        return False

def get_group_blacklist_mode(group_name):
    """
    Get the blacklist/whitelist mode of a group.
    
    Args:
        group_name: Name of the group
        
    Returns:
        bool: True if blacklist, False if whitelist, None if error or group not found
    """
    try:
        Group = Query()
        group = db_client.device_groups.get(Group.name == group_name)
        
        if not group:
            logger.error(f"Group not found: {group_name}")
            return None
            
        return group.get('is_blacklist', False)
    except Exception as e:
        logger.error(f"Error getting group blacklist mode: {e}")
        return None 