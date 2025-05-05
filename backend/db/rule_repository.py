from tinydb import Query
from db.tinydb_client import db_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TinyDB Query objects
Rule = Query()

def get_all_rule_definitions():
    """
    Get all defined rule types.
    
    Returns:
        list: List of rule type dictionaries
    """
    try:
        return db_client.rules.all()
    except Exception as e:
        logger.error(f"Error getting rule definitions: {e}")
        return []

def define_rule(name, description, type="boolean", default=None):
    """
    Define a new rule type.
    
    Args:
        name: Rule name
        description: Rule description
        type: Type of value (boolean, number, string)
        default: Default value for the rule
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if rule already exists
        existing = db_client.rules.get(Rule.name == name)
        
        if existing:
            # Update existing rule
            db_client.rules.update({
                'description': description,
                'type': type,
                'default': default
            }, Rule.name == name)
        else:
            # Create new rule
            db_client.rules.insert({
                'name': name,
                'description': description,
                'type': type,
                'default': default
            })
            
        return True
    except Exception as e:
        logger.error(f"Error defining rule: {e}")
        return False

def get_rule_definition(name):
    """
    Get a rule definition by name.
    
    Args:
        name: Rule name
    
    Returns:
        dict: Rule definition or None if not found
    """
    try:
        return db_client.rules.get(Rule.name == name)
    except Exception as e:
        logger.error(f"Error getting rule definition: {e}")
        return None

def get_device_effective_rules(mac):
    """
    Get the effective rules for a device, combining device-specific and group rules.
    
    Args:
        mac: Device MAC address
    
    Returns:
        dict: Dictionary of rule name to value
    """
    try:
        # Import required functions
        from db.device_repository import get_device
        from db.group_repository import get_device_group
        
        # Get device and its rules
        device = get_device(mac)
        if not device:
            return {}
            
        # Extract rules from device
        rules = {
            'block': device.get('block', False),
            'bandwidth_limit': device.get('bandwidth_limit', 0),
            'access_schedule': device.get('access_schedule', ''),
            'qos_priority': device.get('qos_priority', 0)
        }
        
        return rules
    except Exception as e:
        logger.error(f"Error getting device effective rules: {e}")
        return {} 