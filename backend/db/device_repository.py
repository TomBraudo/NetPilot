import sqlite3
import os
from datetime import datetime
from utils.path_utils import get_data_folder

DB_PATH = os.path.join(get_data_folder(), "devices.db")

# Ensure database and table are created
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                mac TEXT PRIMARY KEY,
                ip TEXT,
                hostname TEXT,
                device_name TEXT,
                first_seen TEXT,
                last_seen TEXT
            )
        """)
        conn.commit()

# Register or update a new device (centralized flow)
def register_device(ip, mac, hostname):
    now = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM devices WHERE mac = ?", (mac,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE devices
                SET ip = ?, hostname = ?, last_seen = ?
                WHERE mac = ?
            """, (ip, hostname, now, mac))
        else:
            cursor.execute("""
                INSERT INTO devices (mac, ip, hostname, device_name, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (mac, ip, hostname, None, now, now))

        # Only add to general group if not already in any group
        cursor.execute("SELECT 1 FROM group_members WHERE mac = ?", (mac,))
        already_grouped = cursor.fetchone()

        if not already_grouped:
            cursor.execute("SELECT group_id FROM device_groups WHERE name = 'general'")
            general_group = cursor.fetchone()
            if general_group:
                cursor.execute("""
                    INSERT OR IGNORE INTO group_members (mac, group_id)
                    VALUES (?, ?)
                """, (mac, general_group[0]))

        conn.commit()


# Remove a device and all related data from group_members and device_rules
def delete_device(mac):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM device_rules WHERE mac = ?", (mac,))
        cursor.execute("DELETE FROM group_members WHERE mac = ?", (mac,))
        cursor.execute("DELETE FROM devices WHERE mac = ?", (mac,))
        conn.commit()


# Get all devices
def get_all_devices():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices")
        return cursor.fetchall()

# Update device name by MAC address
def update_device_name(mac, device_name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE devices SET device_name = ? WHERE mac = ?", (device_name, mac))
        conn.commit()
        return cursor.rowcount > 0

# Clear all devices from the database
def clear_devices():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM devices")
        conn.commit()
