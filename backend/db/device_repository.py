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
                mac TEXT,
                ip TEXT,
                hostname TEXT,
                device_name TEXT,
                first_seen TEXT,
                last_seen TEXT,
                PRIMARY KEY (mac, ip)
            )
        """)
        conn.commit()

# Register or update a new device (centralized flow)
def register_device(ip, mac, hostname):
    """
    Register a device in the database.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")

            cursor.execute("SELECT * FROM devices WHERE mac = ? AND ip = ?", (mac, ip))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE devices
                    SET hostname = ?, last_seen = ?
                    WHERE mac = ? AND ip = ?
                """, (hostname, now, mac, ip))
            else:
                cursor.execute("""
                    INSERT INTO devices (mac, ip, hostname, device_name, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (mac, ip, hostname, None, now, now))

            # Only add to general group if not already in any group
            cursor.execute("SELECT 1 FROM group_members WHERE mac = ? AND ip = ?", (mac, ip))
            already_grouped = cursor.fetchone()

            if not already_grouped:
                cursor.execute("SELECT group_id FROM device_groups WHERE name = 'general'")
                general_group = cursor.fetchone()
                if general_group:
                    cursor.execute("""
                        INSERT OR IGNORE INTO group_members (mac, ip, group_id)
                        VALUES (?, ?, ?)
                    """, (mac, ip, general_group[0]))

            conn.commit()
            return True
    except Exception as e:
        print(f"Error registering device: {e}")
        return False


# Remove a device and all related data from group_members and device_rules
def delete_device(mac, ip):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM device_rules WHERE mac = ? AND ip = ?", (mac, ip))
        cursor.execute("DELETE FROM group_members WHERE mac = ? AND ip = ?", (mac, ip))
        cursor.execute("DELETE FROM devices WHERE mac = ? AND ip = ?", (mac, ip))
        conn.commit()


# Get all devices
def get_all_devices():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices")
        return cursor.fetchall()

# Update device name by MAC address
def update_device_name(mac, ip, device_name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE devices SET device_name = ? WHERE mac = ? AND ip = ?", (device_name, mac, ip))
        conn.commit()
        return cursor.rowcount > 0

# Clear all devices from the database
def clear_devices():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        # First clear related tables due to foreign key constraints
        cursor.execute("DELETE FROM device_rules")
        cursor.execute("DELETE FROM group_members")
        # Then clear devices table
        cursor.execute("DELETE FROM devices")
        conn.commit()
        
# Get mac address from IP
def get_mac_from_ip(ip):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT mac FROM devices WHERE ip = ?", (ip,))
        result = cursor.fetchone()
        return result[0] if result else None
    

# Get device by MAC address
def get_device_by_mac(mac):
    """
    Retrieves a device record by its MAC address.
    If multiple records exist for the same MAC, returns the most recently seen.
    
    Args:
        mac (str): The MAC address to search for
        
    Returns:
        tuple: Device record or None if not found
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        # Order by last_seen DESC to get the most recent record
        cursor.execute("""
            SELECT * FROM devices 
            WHERE mac = ? 
            ORDER BY last_seen DESC
            LIMIT 1
        """, (mac,))
        return cursor.fetchone()