import sqlite3
import os
from utils.path_utils import get_data_folder

DB_PATH = os.path.join(get_data_folder(), "devices.db")

# Initialize group-related tables
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
                FOREIGN KEY(group_id) REFERENCES device_groups(group_id)
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
                FOREIGN KEY(mac) REFERENCES group_members(mac),
                FOREIGN KEY(rule_name) REFERENCES rules(rule_name)
            )
        """)

        conn.commit()

# Set rule for a device
def set_rule_for_device(mac, rule_name, rule_value):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO device_rules (mac, rule_name, rule_value)
            VALUES (?, ?, ?)
            ON CONFLICT(mac, rule_name) DO UPDATE SET rule_value=excluded.rule_value
        """, (mac, rule_name, rule_value))
        conn.commit()

# Set rule for a group (applies the rule to each device in the group)
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
            cursor.execute("""
                INSERT INTO device_rules (mac, rule_name, rule_value)
                VALUES (?, ?, ?)
                ON CONFLICT(mac, rule_name) DO UPDATE SET rule_value=excluded.rule_value
            """, (mac, rule_name, rule_value))

        conn.commit()


# Create a new rule type
def create_rule_type(rule_name, rule_type, default_value=None, description=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO rules (rule_name, rule_type, default_value, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(rule_name) DO NOTHING
        """, (rule_name, rule_type, default_value, description))
        conn.commit()