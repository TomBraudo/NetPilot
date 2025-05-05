from tinydb import Query
from db.tinydb_client import db_client
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TinyDB Query objects
Group = Query()
GroupMember = Query()
Rule = Query()
DeviceRule = Query()

# This function is no longer needed with TinyDB but kept as a no-op for compatibility
def init_group_tables():
    """No-op function for compatibility with existing code."""
    pass

# Assign a rule to a device, ensuring device and rule exist
def set_rule_for_device(mac, ip, rule_name, rule_value="0"):
    """Set a rule for a device."""
    try:
        # Check if device exists
        Device = Query()
        device = db_client.devices.get((Device.mac == mac) & (Device.ip == ip))
        
        if not device:
            # Import here to avoid circular import
            from db.device_repository import register_device
            registration_success = register_device(ip, mac, "unknown")
            if not registration_success:
                raise ValueError(f"Failed to register device with MAC {mac} and IP {ip}")
        
        # Check if rule exists
        rule = db_client.rules.get(Rule.name == rule_name)
        if not rule:
            raise ValueError(f"Rule '{rule_name}' is not defined")
        
        # Update or insert rule
        existing_rule = db_client.device_rules.get(
            (DeviceRule.mac == mac) & 
            (DeviceRule.ip == ip) & 
            (DeviceRule.rule_name == rule_name)
        )
        
        if existing_rule:
            db_client.device_rules.update(
                {'rule_value': rule_value}, 
                (DeviceRule.mac == mac) & 
                (DeviceRule.ip == ip) & 
                (DeviceRule.rule_name == rule_name)
            )
        else:
            db_client.device_rules.insert({
                'mac': mac,
                'ip': ip,
                'rule_name': rule_name,
                'rule_value': rule_value
            })
        
        return True
    except Exception as e:
        logger.error(f"Error setting rule for device: {e}")
        return False

# Remove a rule from a device
def remove_rule_from_device(mac, ip, rule_name):
    """Remove a rule from a device."""
    try:
        db_client.device_rules.remove(
            (DeviceRule.mac == mac) & 
            (DeviceRule.ip == ip) & 
            (DeviceRule.rule_name == rule_name)
        )
        return True
    except Exception as e:
        logger.error(f"Error removing rule from device: {e}")
        return False

# Assign a rule to all members of a group
def set_rule_for_group(group_name, rule_name, rule_value):
    """Set a rule for all devices in a group."""
    try:
        # Get group ID
        group = db_client.device_groups.get(Group.name == group_name)
        if not group:
            raise ValueError("Group not found")
        
        # Get all group members
        group_members = db_client.group_members.search(GroupMember.group_id == group.doc_id)
        
        # Apply rule to each device
        for member in group_members:
            set_rule_for_device(member['mac'], member['ip'], rule_name, rule_value)
        
        return True
    except Exception as e:
        logger.error(f"Error setting rule for group: {e}")
        return False

# Define a new rule type
def create_rule_type(rule_name, rule_type, default_value=None, description=None):
    """Create a new rule type."""
    try:
        # Check if rule exists
        existing_rule = db_client.rules.get(Rule.name == rule_name)
        
        if not existing_rule:
            db_client.rules.insert({
                'name': rule_name,
                'type': rule_type,
                'default': default_value,
                'desc': description
            })
        
        return True
    except Exception as e:
        logger.error(f"Error creating rule type: {e}")
        return False

# Create a new group with a unique name
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

# Rename an existing group
def rename_group(old_name, new_name):
    """Rename a device group."""
    try:
        db_client.device_groups.update(
            {'name': new_name}, 
            Group.name == old_name
        )
        return True
    except Exception as e:
        logger.error(f"Error renaming group: {e}")
        return False

# Move a device to a different group
def move_device_to_group(mac, ip, group_name):
    """Move a device to a different group."""
    try:
        # Check if device exists
        Device = Query()
        device = db_client.devices.get((Device.mac == mac) & (Device.ip == ip))
        if not device:
            raise ValueError(f"Device with MAC {mac} and IP {ip} does not exist")
        
        # Get target group
        group = db_client.device_groups.get(Group.name == group_name)
        if not group:
            raise ValueError("Target group not found")
        
        # Check if device is already in a group
        member = db_client.group_members.get(
            (GroupMember.mac == mac) & (GroupMember.ip == ip)
        )
        
        if member:
            # Update group membership
            db_client.group_members.update(
                {'group_id': group.doc_id}, 
                (GroupMember.mac == mac) & (GroupMember.ip == ip)
            )
        else:
            # Create new group membership
            db_client.group_members.insert({
                'mac': mac,
                'ip': ip,
                'group_id': group.doc_id
            })
        
        return True
    except Exception as e:
        logger.error(f"Error moving device to group: {e}")
        return False

def get_rules_for_device(mac, ip):
    """Get all rules for a device."""
    try:
        rules = db_client.device_rules.search(
            (DeviceRule.mac == mac) & (DeviceRule.ip == ip)
        )
        # Return dictionary format for consistency
        return [{'rule_name': rule.get('rule_name', ''), 
                 'rule_value': rule.get('rule_value', '')} 
                for rule in rules]
    except Exception as e:
        logger.error(f"Error getting rules for device: {e}")
        return []

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
    
def get_group_members(group_name):
    """Get all members of a group."""
    try:
        # Get group ID
        group = db_client.device_groups.get(Group.name == group_name)
        if not group:
            return []
        
        # Get all members
        members = db_client.group_members.search(GroupMember.group_id == group.doc_id)
        
        # Get device details for each member
        Device = Query()
        result = []
        for member in members:
            mac = member.get('mac')
            device = db_client.devices.get(Device.mac == mac)
            if device:
                # Return dictionary format for consistency
                result.append({
                    'mac': device.get('mac', ''),
                    'ip': device.get('ip', ''),
                    'hostname': device.get('hostname', 'Unknown')
                })
        
        return result
    except Exception as e:
        logger.error(f"Error getting group members: {e}")
        return []
    
def delete_group(group_name):
    """
    Delete a group. Moves all devices to 'general' group.
    Cannot delete the 'general' group.
    
    Args:
        group_name: Name of the group to delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Cannot delete 'general' group
        if group_name.lower() == 'general':
            return False
            
        # Get group to delete
        group = db_client.device_groups.get(Group.name == group_name)
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

def get_group(group_name):
    """
    Get group by name.
    
    Args:
        group_name: Name of the group
    
    Returns:
        dict: Group information or None if not found
    """
    try:
        return db_client.device_groups.get(Group.name == group_name)
    except Exception as e:
        logger.error(f"Error getting group: {e}")
        return None

def update_group(group_name, new_name=None, description=None, is_blacklist=None, enable_internet=None):
    """
    Update group information.
    
    Args:
        group_name: Current group name
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
        result = db_client.device_groups.update(update_data, Group.name == group_name)
        return len(result) > 0
    except Exception as e:
        logger.error(f"Error updating group: {e}")
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
                device['group'] = group_name
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
    

