from db.device_repository import init_db
from db.device_groups_repository import init_group_tables
import sqlite3
from utils.path_utils import get_data_folder
import os

DB_PATH = os.path.join(get_data_folder(), "devices.db")

def initialize_all_tables():
    """
    Initialize all database tables: devices, groups, group_members, rules, and device_rules.
    """
    init_db()
    init_group_tables()
    # Reset all database tables for testing purposes
def reset_all_tables():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM device_rules")
        cursor.execute("DELETE FROM group_members")
        cursor.execute("DELETE FROM device_groups")
        cursor.execute("DELETE FROM rules")
        cursor.execute("DELETE FROM devices")
        conn.commit()
    init_group_tables()