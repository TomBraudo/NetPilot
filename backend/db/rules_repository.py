from tinydb import Query
from db.tinydb_client import db_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TinyDB Query objects
Rule = Query()

def get_all_rule_types():
    """
    Get all defined rule types.
    
    Returns:
        list: List of rule type dictionaries
    """
    try:
        return db_client.rules.all()
    except Exception as e:
        logger.error(f"Error getting rule types: {e}")
        return []

def define_rule_type(name, description, value_type="boolean", default_value=None):
    """
    Define a new rule type.
    
    Args:
        name: Rule name
        description: Rule description
        value_type: Type of value (boolean, number, string)
        default_value: Default value for the rule
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if rule type already exists
        existing = db_client.rules.get(Rule.name == name)
        
        if existing:
            # Update existing rule type
            db_client.rules.update({
                'desc': description,
                'type': value_type,
                'default': default_value
            }, Rule.name == name)
        else:
            # Create new rule type
            db_client.rules.insert({
                'name': name,
                'desc': description,
                'type': value_type,
                'default': default_value
            })
            
        return True
    except Exception as e:
        logger.error(f"Error defining rule type: {e}")
        return False

def apply_rule_to_device(mac, rule_name, value):
    """
    Apply a rule directly to a device.
    This updates the device record with the rule.
    
    Args:
        mac: Device MAC address
        rule_name: Name of the rule to apply
        value: Value to set for the rule
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Map rule names to device fields
        rule_to_field = {
            'block': 'is_blocked',
            'limit_bandwidth': 'bandwidth_limit',
            'schedule': 'access_schedule',
            'priority': 'qos_priority'
        }
        
        # Get the corresponding device field
        field = rule_to_field.get(rule_name)
        if not field:
            logger.error(f"Unknown rule: {rule_name}")
            return False
            
        # Create update data
        update_data = {field: value}
        
        # Update the device
        Device = Query()
        result = db_client.devices.update(update_data, Device.mac == mac)
        
        return len(result) > 0
    except Exception as e:
        logger.error(f"Error applying rule to device: {e}")
        return False

def apply_rule_to_group(group_name, rule_name, value):
    """
    Apply a rule to all devices in a group.
    
    Args:
        group_name: Name of the group
        rule_name: Name of the rule to apply
        value: Value to set for the rule
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get group
        Group = Query()
        group = db_client.device_groups.get(Group.name == group_name)
        if not group:
            logger.error(f"Group not found: {group_name}")
            return False
            
        # Get all device MACs in this group
        GroupMember = Query()
        members = db_client.group_members.search(GroupMember.group_id == group.doc_id)
        if not members:
            return True  # No devices to update
            
        # Apply rule to each device
        success = True
        for member in members:
            mac = member.get('mac')
            if not apply_rule_to_device(mac, rule_name, value):
                success = False
                
        return success
    except Exception as e:
        logger.error(f"Error applying rule to group: {e}")
        return False

def get_device_rules(mac):
    """
    Get all rules applied to a device.
    
    Args:
        mac: Device MAC address
    
    Returns:
        dict: Dictionary of rule name to value
    """
    try:
        Device = Query()
        device = db_client.devices.get(Device.mac == mac)
        if not device:
            return {}
            
        # Map device fields to rules
        rules = {}
        if 'is_blocked' in device:
            rules['block'] = device['is_blocked']
        if 'bandwidth_limit' in device:
            rules['limit_bandwidth'] = device['bandwidth_limit']
        if 'access_schedule' in device:
            rules['schedule'] = device['access_schedule']
        if 'qos_priority' in device:
            rules['priority'] = device['qos_priority']
            
        return rules
    except Exception as e:
        logger.error(f"Error getting device rules: {e}")
        return {}

def remove_rule_from_device(mac, rule_name):
    """
    Remove a rule from a device.
    
    Args:
        mac: Device MAC address
        rule_name: Name of the rule to remove
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Map rule names to device fields
        rule_to_field = {
            'block': 'is_blocked',
            'limit_bandwidth': 'bandwidth_limit',
            'schedule': 'access_schedule',
            'priority': 'qos_priority'
        }
        
        # Get the corresponding device field
        field = rule_to_field.get(rule_name)
        if not field:
            logger.error(f"Unknown rule: {rule_name}")
            return False
            
        # Create update data to remove the field
        Device = Query()
        result = db_client.devices.update({field: None}, Device.mac == mac)
        
        return len(result) > 0
    except Exception as e:
        logger.error(f"Error removing rule from device: {e}")
        return False 