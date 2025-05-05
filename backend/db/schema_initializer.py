from db.tinydb_client import db_client
from tinydb import Query
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_predefined_rules():
    """Initialize all predefined network rules in the database."""
    # Define all available rules here - use consistent naming
    rules = [
        {
            "name": "block", 
            "type": "boolean", 
            "default": False, 
            "description": "Block device from network"
        },
        {
            "name": "bandwidth_limit", 
            "type": "number", 
            "default": 0, 
            "description": "Bandwidth limit in Mbps"
        },
        {
            "name": "access_schedule", 
            "type": "string", 
            "default": "", 
            "description": "Schedule for device access"
        },
        {
            "name": "qos_priority", 
            "type": "number", 
            "default": 0, 
            "description": "Traffic priority (QoS)"
        }
    ]
    
    # Add or update rules
    Rule = Query()
    for rule in rules:
        existing_rule = db_client.rules.get(Rule.name == rule["name"])
        
        if not existing_rule:
            db_client.rules.insert(rule)
        else:
            db_client.rules.update(rule, Rule.name == rule["name"])
    
    logger.info("Predefined rules initialized")

def initialize_default_group():
    """Ensure a default group 'general' exists."""
    Group = Query()
    if not db_client.device_groups.contains(Group.name == 'general'):
        db_client.device_groups.insert({
            "name": "general",
            "description": "Default group for all devices",
            "is_blacklist": False,
            "enable_internet": True
        })
        logger.info("Default 'general' group created")

def add_protection_field_to_devices():
    """Add the 'protected' field to all devices if it doesn't exist."""
    try:
        # Update all devices to add protected field if missing
        devices = db_client.devices.all()
        for device in devices:
            if 'protected' not in device:
                db_client.devices.update({'protected': False}, doc_ids=[device.doc_id])
                
        logger.info("Added protection field to devices")
    except Exception as e:
        logger.error(f"Error adding protection field to devices: {e}")

def initialize_all_tables():
    """
    Initialize all database tables with TinyDB.
    Since TinyDB creates tables on-demand, we just need to ensure
    the default data is present.
    """
    initialize_default_group()
    initialize_predefined_rules()
    add_protection_field_to_devices()
    logger.info("All tables initialized")

def reset_all_tables():
    """Reset all tables and reinitialize with default values."""
    db_client.clear_all()
    initialize_all_tables()
    logger.info("All tables reset and reinitialized")