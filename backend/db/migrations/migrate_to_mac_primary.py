import sys
import os

# Add both the parent directory and the backend directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_dir = os.path.dirname(parent_dir)
sys.path.extend([parent_dir, backend_dir])

from tinydb_client import db_client
from tinydb import Query
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_devices_table():
    """Migrate the devices table to use MAC as primary key."""
    try:
        # Get all devices
        devices = db_client.devices.all()
        
        # Create a new table for the migration
        new_devices = db_client.db.table('devices_new')
        
        # Process each device
        for device in devices:
            # Ensure MAC is present
            if 'mac' not in device:
                logger.warning(f"Device without MAC found: {device}")
                continue
                
            # Check if device already exists in new table
            Device = Query()
            existing = new_devices.get(Device.mac == device['mac'])
            
            if existing:
                # Update existing device if this one is more recent
                if device.get('last_seen', '') > existing.get('last_seen', ''):
                    new_devices.update(device, Device.mac == device['mac'])
                    logger.info(f"Updated device {device['mac']} with newer data")
            else:
                # Insert new device
                new_devices.insert(device)
                logger.info(f"Migrated device {device['mac']}")
        
        # Replace old table with new one
        db_client.devices.truncate()
        for device in new_devices.all():
            db_client.devices.insert(device)
        
        # Drop temporary table
        db_client.db.drop_table('devices_new')
        
        logger.info("Successfully migrated devices table")
        return True
    except Exception as e:
        logger.error(f"Error migrating devices table: {e}")
        return False

def migrate_device_rules():
    """Migrate device rules to use MAC as primary key."""
    try:
        # Get all rules
        rules = db_client.device_rules.all()
        
        # Create a new table for the migration
        new_rules = db_client.db.table('device_rules_new')
        
        # Process each rule
        for rule in rules:
            # Ensure MAC is present
            if 'mac' not in rule:
                logger.warning(f"Rule without MAC found: {rule}")
                continue
                
            # Check if rule already exists in new table
            Rule = Query()
            existing = new_rules.get(
                (Rule.mac == rule['mac']) & 
                (Rule.rule_name == rule['rule_name'])
            )
            
            if not existing:
                # Insert new rule
                new_rules.insert(rule)
                logger.info(f"Migrated rule for device {rule['mac']}")
        
        # Replace old table with new one
        db_client.device_rules.truncate()
        for rule in new_rules.all():
            db_client.device_rules.insert(rule)
        
        # Drop temporary table
        db_client.db.drop_table('device_rules_new')
        
        logger.info("Successfully migrated device rules")
        return True
    except Exception as e:
        logger.error(f"Error migrating device rules: {e}")
        return False

def migrate_group_members():
    """Migrate group members to use MAC as primary key."""
    try:
        # Get all group members
        members = db_client.group_members.all()
        
        # Create a new table for the migration
        new_members = db_client.db.table('group_members_new')
        
        # Process each member
        for member in members:
            # Ensure MAC is present
            if 'mac' not in member:
                logger.warning(f"Group member without MAC found: {member}")
                continue
                
            # Check if member already exists in new table
            Member = Query()
            existing = new_members.get(Member.mac == member['mac'])
            
            if not existing:
                # Insert new member
                new_members.insert(member)
                logger.info(f"Migrated group member {member['mac']}")
        
        # Replace old table with new one
        db_client.group_members.truncate()
        for member in new_members.all():
            db_client.group_members.insert(member)
        
        # Drop temporary table
        db_client.db.drop_table('group_members_new')
        
        logger.info("Successfully migrated group members")
        return True
    except Exception as e:
        logger.error(f"Error migrating group members: {e}")
        return False

def migrate_bandwidth_lists():
    """Migrate bandwidth whitelist and blacklist to use MAC as primary key."""
    try:
        # Process whitelist
        whitelist = db_client.bandwidth_whitelist.all()
        new_whitelist = db_client.db.table('whitelist_new')
        
        for entry in whitelist:
            if 'mac' not in entry:
                logger.warning(f"Whitelist entry without MAC found: {entry}")
                continue
                
            Whitelist = Query()
            existing = new_whitelist.get(Whitelist.mac == entry['mac'])
            
            if not existing:
                new_whitelist.insert(entry)
                logger.info(f"Migrated whitelist entry for {entry['mac']}")
        
        # Replace old whitelist with new one
        db_client.bandwidth_whitelist.truncate()
        for entry in new_whitelist.all():
            db_client.bandwidth_whitelist.insert(entry)
        
        # Drop temporary whitelist table
        db_client.db.drop_table('whitelist_new')
        
        # Process blacklist
        blacklist = db_client.bandwidth_blacklist.all()
        new_blacklist = db_client.db.table('blacklist_new')
        
        for entry in blacklist:
            if 'mac' not in entry:
                logger.warning(f"Blacklist entry without MAC found: {entry}")
                continue
                
            Blacklist = Query()
            existing = new_blacklist.get(Blacklist.mac == entry['mac'])
            
            if not existing:
                new_blacklist.insert(entry)
                logger.info(f"Migrated blacklist entry for {entry['mac']}")
        
        # Replace old blacklist with new one
        db_client.bandwidth_blacklist.truncate()
        for entry in new_blacklist.all():
            db_client.bandwidth_blacklist.insert(entry)
        
        # Drop temporary blacklist table
        db_client.db.drop_table('blacklist_new')
        
        logger.info("Successfully migrated bandwidth lists")
        return True
    except Exception as e:
        logger.error(f"Error migrating bandwidth lists: {e}")
        return False

def run_migration():
    """Run all migrations in the correct order."""
    try:
        logger.info("Starting database migration to MAC-based primary keys")
        
        # Run migrations in order
        migrations = [
            ("Devices table", migrate_devices_table),
            ("Device rules", migrate_device_rules),
            ("Group members", migrate_group_members),
            ("Bandwidth lists", migrate_bandwidth_lists)
        ]
        
        for name, migration in migrations:
            logger.info(f"Running migration: {name}")
            if not migration():
                logger.error(f"Migration failed: {name}")
                return False
        
        logger.info("All migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False

if __name__ == "__main__":
    run_migration() 