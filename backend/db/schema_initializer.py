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
        {"name": "block", "type": "boolean", "default": "0", "desc": "Block device from network"},
        {"name": "limit_bandwidth", "type": "number", "default": "0", "desc": "Bandwidth limit in Mbps"},
        {"name": "schedule", "type": "string", "default": "", "desc": "Schedule for device access"},
        {"name": "priority", "type": "number", "default": "0", "desc": "Traffic priority (QoS)"}
    ]
    
    # TinyDB's upsert functionality
    for rule in rules:
        # Check if the rule already exists
        Rule = Query()
        existing_rule = db_client.rules.get(Rule.name == rule["name"])
        
        if not existing_rule:
            # Insert new rule
            db_client.rules.insert(rule)
        else:
            # Update existing rule
            db_client.rules.update(rule, Rule.name == rule["name"])
        
    # Initialize settings table
    settings = [
        {"name": "whitelist_mode", "type": "boolean", "default": "0", "desc": "Whitelist mode for bandwidth limiting"}
    ]
    
    for setting in settings:
        # Check if the setting already exists
        Setting = Query()
        existing_setting = db_client.settings.get(Setting.name == setting["name"])
        
        if not existing_setting:
            # Insert new setting    
            db_client.settings.insert(setting)
        else:
            # Update existing setting
            db_client.settings.update(setting, Setting.name == setting["name"])
    
    # Ensure changes are persisted
    db_client.flush()
    
    logger.info("Predefined rules initialized")

def initialize_default_group():
    """Ensure a default group 'general' exists."""
    Group = Query()
    if not db_client.device_groups.contains(Group.name == 'general'):
        db_client.device_groups.insert({"name": "general"})
        db_client.flush()  # Ensure changes are persisted
        logger.info("Default 'general' group created")

def initialize_all_tables():
    """Initialize all database tables with default values."""
    try:
        # Initialize rules and settings
        initialize_predefined_rules()
        
        # Initialize default group
        initialize_default_group()
        
        # Ensure all changes are persisted
        db_client.flush()
        
        logger.info("All tables initialized")
    except Exception as e:
        logger.error(f"Error initializing tables: {e}")
        raise

def reset_all_tables():
    """Reset all tables and reinitialize with default values."""
    db_client.clear_all()
    initialize_all_tables()
    logger.info("All tables reset and reinitialized")