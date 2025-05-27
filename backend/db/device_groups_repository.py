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
    """Set a rule for a device using MAC as the primary key."""
    try:
        # Check if device exists
        Device = Query()
        device = db_client.devices.get(Device.mac == mac)
        
        if not device:
            # Import here to avoid circular import
            from db.device_repository import register_device
            registration_success = register_device(ip, mac, "unknown")
            if not registration_success:
                raise ValueError(f"Failed to register device with MAC {mac}")
        
        # Check if rule exists
        rule = db_client.rules.get(Rule.name == rule_name)
        if not rule:
            raise ValueError(f"Rule '{rule_name}' is not defined")
        
        # Update or insert rule
        existing_rule = db_client.device_rules.get(
            (DeviceRule.mac == mac) & 
            (DeviceRule.rule_name == rule_name)
        )
        
        if existing_rule:
            db_client.device_rules.update(
                {'rule_value': rule_value}, 
                (DeviceRule.mac == mac) & 
                (DeviceRule.rule_name == rule_name)
            )
            logger.info(f"Updated rule {rule_name} for device {mac}")
        else:
            db_client.device_rules.insert({
                'mac': mac,
                'ip': ip,
                'rule_name': rule_name,
                'rule_value': rule_value
            })
            logger.info(f"Added rule {rule_name} for device {mac}")
        
        return True
    except Exception as e:
        logger.error(f"Error setting rule for device: {e}")
        return False

# Remove a rule from a device
def remove_rule_from_device(mac, ip, rule_name):
    """Remove a rule from a device using MAC as the primary key."""
    try:
        db_client.device_rules.remove(
            (DeviceRule.mac == mac) & 
            (DeviceRule.rule_name == rule_name)
        )
        logger.info(f"Removed rule {rule_name} from device {mac}")
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
def create_group(name):
    """Create a new device group."""
    try:
        # Check if group exists
        if not db_client.device_groups.contains(Group.name == name):
            db_client.device_groups.insert({'name': name})
        return True
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        return False

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
    """Get all rules for a device using MAC as the primary key."""
    try:
        return db_client.device_rules.search(DeviceRule.mac == mac)
    except Exception as e:
        logger.error(f"Error getting device rules: {e}")
        return []

def get_all_groups():
    """Get all device groups."""
    try:
        return db_client.device_groups.all()
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return []
    
def get_group_members(group_id):
    """Get all members of a group."""
    try:
        return db_client.group_members.search(GroupMember.group_id == group_id)
    except Exception as e:
        logger.error(f"Error getting group members: {e}")
        return []
    
def delete_group(group_name):
    """Delete a group and move its members to 'general'."""
    try:
        # Get group to delete
        group = db_client.device_groups.get(Group.name == group_name)
        if not group:
            raise ValueError("Group not found")
        
        # Ensure it's not the only group
        group_count = len(db_client.device_groups.all())
        if group_count <= 1:
            raise ValueError("Cannot delete the only group")
        
        # Get general group
        general_group = db_client.device_groups.get(Group.name == 'general')
        if not general_group:
            raise ValueError("'general' group not found")
        
        # Move devices to general group
        members = db_client.group_members.search(GroupMember.group_id == group.doc_id)
        for member in members:
            db_client.group_members.update(
                {'group_id': general_group.doc_id},
                (GroupMember.mac == member['mac']) & (GroupMember.ip == member['ip'])
            )
        
        # Delete the group
        db_client.device_groups.remove(doc_ids=[group.doc_id])
        
        return True
    except Exception as e:
        logger.error(f"Error deleting group: {e}")
        return False
    

