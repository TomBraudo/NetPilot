import sys
import sqlite3
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime
from utils.path_utils import get_data_folder
from db.device_repository import register_device, get_all_devices, update_device_name, delete_device
from db.device_groups_repository import create_rule_type, set_rule_for_device, set_rule_for_group, create_group, rename_group, move_device_to_group

DB_PATH = os.path.join(get_data_folder(), "devices.db")

# Utility to print all database state
def print_full_db_state():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        print("\n--- DEVICES ---")
        for row in cursor.execute("SELECT * FROM devices"):
            print(row)

        print("\n--- GROUPS ---")
        for row in cursor.execute("SELECT * FROM device_groups"):
            print(row)

        print("\n--- GROUP MEMBERS ---")
        for row in cursor.execute("SELECT * FROM group_members"):
            print(row)

        print("\n--- RULES ---")
        for row in cursor.execute("SELECT * FROM rules"):
            print(row)

        print("\n--- DEVICE RULES ---")
        for row in cursor.execute("SELECT * FROM device_rules"):
            print(row)

# Test scenario with step prompts and state printing
def run_test_scenario():
    print("\nStep 1: Resetting and printing empty database...")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM device_rules")
        cursor.execute("DELETE FROM group_members")
        cursor.execute("DELETE FROM device_groups")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'device_groups'")
        cursor.execute("DELETE FROM rules")
        cursor.execute("DELETE FROM devices")
        conn.commit()

    from db.device_groups_repository import init_group_tables
    init_group_tables()
    print_full_db_state()
    input("Press 'c' to continue...\n")

    print("\nStep 2: Creating fictional devices...")
    register_device("192.168.1.10", "AA:BB:CC:DD:EE:01", "laptop")
    register_device("192.168.1.11", "AA:BB:CC:DD:EE:02", "phone")
    register_device("192.168.1.12", "AA:BB:CC:DD:EE:03", "tablet")
    update_device_name("AA:BB:CC:DD:EE:01", "Tom's Laptop")
    update_device_name("AA:BB:CC:DD:EE:02", "Tom's Phone")
    update_device_name("AA:BB:CC:DD:EE:03", "Tom's Tablet")
    print_full_db_state()
    input("Press 'c' to continue...\n")

    print("\nStep 3: Creating groups...")
    create_group("work")
    create_group("home")
    rename_group("work", "work-devices")
    print_full_db_state()
    input("Press 'c' to continue...\n")

    print("\nStep 4: Moving devices to groups...")
    move_device_to_group("AA:BB:CC:DD:EE:01", "work-devices")
    move_device_to_group("AA:BB:CC:DD:EE:03", "home")
    print_full_db_state()
    input("Press 'c' to continue...\n")

    print("\nStep 5: Creating and assigning rules...")
    create_rule_type("block", "boolean", "0", "Block device from network")
    create_rule_type("bandwidth_limit", "number", None, "Bandwidth limit in Mbps")
    set_rule_for_device("AA:BB:CC:DD:EE:01", "block", "1")
    set_rule_for_group("home", "bandwidth_limit", "100")
    print_full_db_state()
    input("Press 'c' to continue...\n")

    print("\nStep 6: Assign multiple rules to a single device...")
    set_rule_for_device("AA:BB:CC:DD:EE:01", "bandwidth_limit", "20")
    print_full_db_state()
    input("Press 'c' to continue...\n")

    print("\nStep 7: Overwrite rule for a device...")
    set_rule_for_device("AA:BB:CC:DD:EE:01", "bandwidth_limit", "10")
    print_full_db_state()
    input("Press 'c' to continue...\n")

    print("\nStep 8: Move device between groups...")
    move_device_to_group("AA:BB:CC:DD:EE:03", "work-devices")
    print_full_db_state()
    input("Press 'c' to continue...\n")

    print("\nStep 9: Verify group rule overrides device rule...")
    set_rule_for_device("AA:BB:CC:DD:EE:03", "block", "0")
    set_rule_for_group("work-devices", "block", "1")
    print_full_db_state()
    input("Press 'c' to continue...\n")

    print("\nStep 10: Delete a device and check cleanup...")
    delete_device("AA:BB:CC:DD:EE:01")
    print_full_db_state()
    input("Press 'c' to finish.\n")

if __name__ == "__main__":
    run_test_scenario()
