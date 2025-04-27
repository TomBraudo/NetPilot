from db.tinydb_client import db_client
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
    
    logger.info("Predefined rules initialized")

def initialize_default_group():
    """Ensure a default group 'general' exists."""
    Group = Query()
    if not db_client.device_groups.contains(Group.name == 'general'):
        db_client.device_groups.insert({"name": "general"})
        logger.info("Default 'general' group created")

def initialize_all_tables():
    """
    Initialize all database tables with TinyDB.
    Since TinyDB creates tables on-demand, we just need to ensure
    the default data is present.
    """
    initialize_default_group()
    initialize_predefined_rules()
    logger.info("All tables initialized")

def reset_all_tables():
    """Reset all tables and reinitialize with default values."""
    db_client.clear_all()
    initialize_all_tables()
    logger.info("All tables reset and reinitialized")