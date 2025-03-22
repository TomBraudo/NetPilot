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
                mac TEXT PRIMARY KEY,
                group_id INTEGER NOT NULL,
                FOREIGN KEY(group_id) REFERENCES device_groups(group_id) ON DELETE CASCADE,
                FOREIGN KEY(mac) REFERENCES devices(mac) ON DELETE CASCADE
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

        # Table: device_rules (rule values for individual devices)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_rules (
                mac TEXT,
                rule_name TEXT,
                rule_value TEXT,
                PRIMARY KEY(mac, rule_name),
                FOREIGN KEY(mac) REFERENCES devices(mac) ON DELETE CASCADE,
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
def set_rule_for_device(mac, rule_name, rule_value):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM devices WHERE mac = ?", (mac,))
        if cursor.fetchone() is None:
            raise ValueError(f"Device with MAC {mac} does not exist")

        cursor.execute("SELECT 1 FROM rules WHERE rule_name = ?", (rule_name,))
        if cursor.fetchone() is None:
            raise ValueError(f"Rule '{rule_name}' is not defined")

    register_device("0.0.0.0", mac, "unknown")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO device_rules (mac, rule_name, rule_value)
            VALUES (?, ?, ?)
            ON CONFLICT(mac, rule_name) DO UPDATE SET rule_value = excluded.rule_value
        """, (mac, rule_name, rule_value))
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

        cursor.execute("SELECT mac FROM group_members WHERE group_id = ?", (group_id,))
        macs = [r[0] for r in cursor.fetchall()]

    for mac in macs:
        set_rule_for_device(mac, rule_name, rule_value)

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
def move_device_to_group(mac, group_name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Ensure the device exists
        cursor.execute("SELECT 1 FROM devices WHERE mac = ?", (mac,))
        if not cursor.fetchone():
            raise ValueError(f"Device with MAC {mac} does not exist")

        # Ensure the target group exists
        cursor.execute("SELECT group_id FROM device_groups WHERE name = ?", (group_name,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Target group not found")
        group_id = row[0]

        # Move the device into the new group
        cursor.execute("""
            INSERT INTO group_members (mac, group_id)
            VALUES (?, ?)
            ON CONFLICT(mac) DO UPDATE SET group_id = excluded.group_id
        """, (mac, group_id))
        conn.commit()

