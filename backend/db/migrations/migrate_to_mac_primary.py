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
        new_devices = db_client.devices_db.table('devices_new')
        
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
        db_client.devices_db.drop_table('devices_new')
        
        # Ensure changes are persisted
        db_client.flush()
        
        logger.info("Successfully migrated devices table")
        return True
    except Exception as e:
        logger.error(f"Error migrating devices table: {e}")
        return False

def migrate_device_rules():
    """Migrate device rules to use MAC as primary key."""
    try:
        # Get all device rules
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
            existing = new_rules.get(Rule.mac == rule['mac'])
            
            if existing:
                # Update existing rule if this one is more recent
                if rule.get('updated_at', '') > existing.get('updated_at', ''):
                    new_rules.update(rule, Rule.mac == rule['mac'])
                    logger.info(f"Updated rule for device {rule['mac']} with newer data")
            else:
                # Insert new rule
                new_rules.insert(rule)
                logger.info(f"Migrated rule for device {rule['mac']}")
        
        # Replace old table with new one
        db_client.device_rules.truncate()
        for rule in new_rules.all():
            db_client.device_rules.insert(rule)
        
        # Drop temporary table
        db_client.db.drop_table('device_rules_new')
        
        # Ensure changes are persisted
        db_client.flush()
        
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
            
            if existing:
                # Update existing member if this one is more recent
                if member.get('updated_at', '') > existing.get('updated_at', ''):
                    new_members.update(member, Member.mac == member['mac'])
                    logger.info(f"Updated group member {member['mac']} with newer data")
            else:
                # Insert new member
                new_members.insert(member)
                logger.info(f"Migrated group member {member['mac']}")
        
        # Replace old table with new one
        db_client.group_members.truncate()
        for member in new_members.all():
            db_client.group_members.insert(member)
        
        # Drop temporary table
        db_client.db.drop_table('group_members_new')
        
        # Ensure changes are persisted
        db_client.flush()
        
        logger.info("Successfully migrated group members")
        return True
    except Exception as e:
        logger.error(f"Error migrating group members: {e}")
        return False

def migrate_bandwidth_lists():
    """Migrate bandwidth whitelist and blacklist to use MAC as primary key."""
    try:
        # Get all whitelist entries
        whitelist = db_client.bandwidth_whitelist.all()
        
        # Create a new table for the migration
        new_whitelist = db_client.db.table('whitelist_new')
        
        # Process each whitelist entry
        for entry in whitelist:
            # Ensure MAC is present
            if 'mac' not in entry:
                logger.warning(f"Whitelist entry without MAC found: {entry}")
                continue
                
            # Check if entry already exists in new table
            Entry = Query()
            existing = new_whitelist.get(Entry.mac == entry['mac'])
            
            if existing:
                # Update existing entry if this one is more recent
                if entry.get('added_at', '') > existing.get('added_at', ''):
                    new_whitelist.update(entry, Entry.mac == entry['mac'])
                    logger.info(f"Updated whitelist entry for device {entry['mac']} with newer data")
            else:
                # Insert new entry
                new_whitelist.insert(entry)
                logger.info(f"Migrated whitelist entry for device {entry['mac']}")
        
        # Replace old table with new one
        db_client.bandwidth_whitelist.truncate()
        for entry in new_whitelist.all():
            db_client.bandwidth_whitelist.insert(entry)
        
        # Drop temporary table
        db_client.db.drop_table('whitelist_new')
        
        # Get all blacklist entries
        blacklist = db_client.bandwidth_blacklist.all()
        
        # Create a new table for the migration
        new_blacklist = db_client.db.table('blacklist_new')
        
        # Process each blacklist entry
        for entry in blacklist:
            # Ensure MAC is present
            if 'mac' not in entry:
                logger.warning(f"Blacklist entry without MAC found: {entry}")
                continue
                
            # Check if entry already exists in new table
            Entry = Query()
            existing = new_blacklist.get(Entry.mac == entry['mac'])
            
            if existing:
                # Update existing entry if this one is more recent
                if entry.get('added_at', '') > existing.get('added_at', ''):
                    new_blacklist.update(entry, Entry.mac == entry['mac'])
                    logger.info(f"Updated blacklist entry for device {entry['mac']} with newer data")
            else:
                # Insert new entry
                new_blacklist.insert(entry)
                logger.info(f"Migrated blacklist entry for device {entry['mac']}")
        
        # Replace old table with new one
        db_client.bandwidth_blacklist.truncate()
        for entry in new_blacklist.all():
            db_client.bandwidth_blacklist.insert(entry)
        
        # Drop temporary table
        db_client.db.drop_table('blacklist_new')
        
        # Ensure changes are persisted
        db_client.flush()
        
        logger.info("Successfully migrated bandwidth lists")
        return True
    except Exception as e:
        logger.error(f"Error migrating bandwidth lists: {e}")
        return False

def run_migration():
    """Run all migrations in sequence."""
    try:
        # Migrate devices table
        if not migrate_devices_table():
            logger.error("Migration failed: Devices table")
            return False
            
        # Migrate device rules
        if not migrate_device_rules():
            logger.error("Migration failed: Device rules")
            return False
            
        # Migrate group members
        if not migrate_group_members():
            logger.error("Migration failed: Group members")
            return False
            
        # Migrate bandwidth lists
        if not migrate_bandwidth_lists():
            logger.error("Migration failed: Bandwidth lists")
            return False
            
        logger.info("All migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    if run_migration():
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed")
        sys.exit(1) 