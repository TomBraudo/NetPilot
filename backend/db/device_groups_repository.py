import sqlite3
import os
from datetime import datetime
from utils.path_utils import get_data_folder
from db.device_repository import register_device

DB_PATH = os.path.join(get_data_folder(), "devices.db")

# Initialize all tables: groups, rules, and rule assignments
def init_group_tables():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        # Table: device_groups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_groups (
                group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # Table: group_members
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                mac TEXT,
                ip TEXT,
                group_id INTEGER NOT NULL,
                PRIMARY KEY(mac, ip),
                FOREIGN KEY(group_id) REFERENCES device_groups(group_id) ON DELETE CASCADE,
                FOREIGN KEY(mac, ip) REFERENCES devices(mac, ip) ON DELETE CASCADE
            )
        """)

        # Table: rules (registry of all rule types)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                rule_name TEXT PRIMARY KEY,
                rule_type TEXT NOT NULL,
                default_value TEXT,
                description TEXT
            )
        """)

        # Table: device_rules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_rules (
                mac TEXT,
                ip TEXT,
                rule_name TEXT,
                rule_value TEXT,
                PRIMARY KEY(mac, ip, rule_name),
                FOREIGN KEY(mac, ip) REFERENCES devices(mac, ip) ON DELETE CASCADE,
                FOREIGN KEY(rule_name) REFERENCES rules(rule_name)
            )
        """)

        # Ensure a default group "general" exists
        cursor.execute("""
            INSERT OR IGNORE INTO device_groups (name)
            VALUES ('general')
        """)

        conn.commit()

# Assign a rule to a device, ensuring device and rule exist
def set_rule_for_device(mac, ip, rule_name, rule_value="0"):
    # Default empty rule value to "0" instead of None
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("SELECT 1 FROM devices WHERE mac = ? AND ip = ?", (mac, ip))
        if cursor.fetchone() is None:
            # Register the device if it doesn't exist
            registration_success = register_device(ip, mac, "unknown")
            if not registration_success:
                raise ValueError(f"Failed to register device with MAC {mac} and IP {ip}")
            
        cursor.execute("SELECT 1 FROM rules WHERE rule_name = ?", (rule_name,))
        if cursor.fetchone() is None:
            raise ValueError(f"Rule '{rule_name}' is not defined")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("""
            INSERT INTO device_rules (mac, ip, rule_name, rule_value)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(mac, ip, rule_name) DO UPDATE SET rule_value = excluded.rule_value
        """, (mac, ip, rule_name, rule_value))
        conn.commit()

# Remove a rule from a device
def remove_rule_from_device(mac, ip, rule_name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM device_rules WHERE mac = ? AND ip = ? AND rule_name = ?", 
                      (mac, ip, rule_name))
        conn.commit()

# Assign a rule to all members of a group
def set_rule_for_group(group_name, rule_name, rule_value):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT group_id FROM device_groups WHERE name = ?", (group_name,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Group not found")
        group_id = row[0]

        # Updated to select both mac and ip
        cursor.execute("SELECT mac, ip FROM group_members WHERE group_id = ?", (group_id,))
        device_pairs = cursor.fetchall()  # Now returns (mac, ip) tuples

    # Apply the rule to each device in the group
    for mac, ip in device_pairs:
        set_rule_for_device(mac, ip, rule_name, rule_value)  # Pass both mac and ip

# Define a new rule type (if it doesn't already exist)
def create_rule_type(rule_name, rule_type, default_value=None, description=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO rules (rule_name, rule_type, default_value, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(rule_name) DO NOTHING
        """, (rule_name, rule_type, default_value, description))
        conn.commit()

# Create a new group with a unique name
def create_group(name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO device_groups (name) VALUES (?)", (name,))
        conn.commit()

# Rename an existing group
def rename_group(old_name, new_name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE device_groups SET name = ? WHERE name = ?", (new_name, old_name))
        conn.commit()

# Move a device to a different group
def move_device_to_group(mac, ip, group_name):  # Added ip parameter
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Ensure the device exists
        cursor.execute("SELECT 1 FROM devices WHERE mac = ? AND ip = ?", (mac, ip))
        if not cursor.fetchone():
            raise ValueError(f"Device with MAC {mac} and IP {ip} does not exist")

        # Ensure the target group exists
        cursor.execute("SELECT group_id FROM device_groups WHERE name = ?", (group_name,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Target group not found")
        group_id = row[0]

        # Move the device into the new group
        cursor.execute("""
            INSERT INTO group_members (mac, ip, group_id)  # Added ip column
            VALUES (?, ?, ?)
            ON CONFLICT(mac, ip) DO UPDATE SET group_id = excluded.group_id  # Fixed conflict column
        """, (mac, ip, group_id))
        conn.commit()
        
def get_rules_for_device(mac, ip):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rule_name, rule_value FROM device_rules WHERE mac = ? AND ip = ?", (mac, ip))
        return cursor.fetchall()

def get_all_groups():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM device_groups")
        return [r[0] for r in cursor.fetchall()]
    
def get_group_members(group_name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT devices.mac, devices.ip, devices.hostname
            FROM devices
            JOIN group_members ON devices.mac = group_members.mac AND devices.ip = group_members.ip
            JOIN device_groups ON group_members.group_id = device_groups.group_id
            WHERE device_groups.name = ?
        """, (group_name,))
        return cursor.fetchall()
    
def delete_group(group_name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Ensure the group exists
        cursor.execute("SELECT group_id FROM device_groups WHERE name = ?", (group_name,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Group not found")
        group_id = row[0]

        # Ensure it's not the only group
        cursor.execute("SELECT COUNT(*) FROM device_groups")
        group_count = cursor.fetchone()[0]
        if group_count <= 1:
            raise ValueError("Cannot delete the only group")

        # Get the 'general' group ID
        cursor.execute("SELECT group_id FROM device_groups WHERE name = 'general'")
        general_group = cursor.fetchone()
        if not general_group:
            raise ValueError("'general' group not found")
        general_group_id = general_group[0]

        # Move devices from the group to 'general'
        cursor.execute("UPDATE group_members SET group_id = ? WHERE group_id = ?", (general_group_id, group_id))

        # Delete the group
        cursor.execute("DELETE FROM device_groups WHERE group_id = ?", (group_id,))
        conn.commit()
    

