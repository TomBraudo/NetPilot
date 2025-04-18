from db.device_repository import init_db
from db.device_groups_repository import init_group_tables
import sqlite3
from utils.path_utils import get_data_folder
import os

DB_PATH = os.path.join(get_data_folder(), "devices.db")

def initialize_predefined_rules():
    """Initialize all predefined network rules in the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Define all available rules here - use consistent naming
        rules = [
            {"name": "block", "type": "boolean", "default": "0", "desc": "Block device from network"},
            {"name": "limit_bandwidth", "type": "number", "default": "0", "desc": "Bandwidth limit in Mbps"}, # Consistent name
            {"name": "schedule", "type": "string", "default": "", "desc": "Schedule for device access"},
            {"name": "priority", "type": "number", "default": "0", "desc": "Traffic priority (QoS)"}
        ]
        
        for rule in rules:
            try:
                cursor.execute("""
                    INSERT INTO rules (rule_name, rule_type, default_value, description)
                    VALUES (?, ?, ?, ?)
                """, (rule["name"], rule["type"], rule["default"], rule["desc"]))
            except sqlite3.IntegrityError:
                # Rule already exists, which is fine
                pass
        conn.commit()

def initialize_all_tables():
    """
    Initialize all database tables: devices, groups, group_members, rules, and device_rules.
    """
    init_db()
    init_group_tables()
    initialize_predefined_rules()

def reset_all_tables():
    """Reset all tables and reinitialize with default values."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Drop all tables
        cursor.execute("DROP TABLE IF EXISTS device_rules")
        cursor.execute("DROP TABLE IF EXISTS group_members") 
        cursor.execute("DROP TABLE IF EXISTS device_groups")
        cursor.execute("DROP TABLE IF EXISTS rules")
        cursor.execute("DROP TABLE IF EXISTS devices")
        conn.commit()
    
    # Recreate tables and rules
    init_db()
    init_group_tables()
    initialize_predefined_rules()