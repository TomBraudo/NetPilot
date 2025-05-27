from tinydb import TinyDB, Query
from utils.path_utils import get_data_folder
import os
from db.tinydb_client import db_client
from datetime import datetime
from utils.logging_config import get_logger
from db.device_repository import get_mac_from_ip

# Setup logging
logger = get_logger('db.blacklist')

# Use the initialized tables from db_client
blacklist_table = db_client.bandwidth_blacklist
settings_table = db_client.settings
Device = Query()
Setting = Query()

def get_blacklist():
    """
    Retrieves the list of blacklisted devices from the database
    
    Returns:
        list: List of blacklisted device entries
    """
    try:
        entries = blacklist_table.all()
        db_client.flush()  # Ensure we have the latest data
        return entries
    except Exception as e:
        logger.error(f"Error retrieving blacklist: {str(e)}", exc_info=True)
        return []

def add_to_blacklist(ip, name=None):
    """
    Adds a device to the blacklist
    
    Args:
        ip (str): IP address of the device
        name (str, optional): Name of the device
        
    Returns:
        dict: The added device entry
    """
    try:
        mac = get_mac_from_ip(ip)
        if not mac:
            raise ValueError(f"Device with IP {ip} not found in network")
            
        # Check if device already exists in blacklist
        existing = blacklist_table.get(Device.ip == ip)
        if existing:
            # Update existing entry
            entry = {
                "ip": ip,
                "mac": mac,
                "name": name or existing.get("name", f"Device-{ip}"),
                "added_at": datetime.now().isoformat()
            }
            blacklist_table.update(entry, Device.ip == ip)
            logger.info(f"Updated blacklist entry for device {ip}")
        else:
            # Add new entry
            entry = {
                "ip": ip,
                "mac": mac,
                "name": name or f"Device-{ip}",
                "added_at": datetime.now().isoformat()
            }
            blacklist_table.insert(entry)
            logger.info(f"Added device {ip} to blacklist")
            
        db_client.flush()  # Ensure changes are persisted
        return entry
    except Exception as e:
        logger.error(f"Error adding device to blacklist: {str(e)}", exc_info=True)
        raise

def remove_from_blacklist(ip):
    """
    Removes a device from the blacklist
    
    Args:
        ip (str): IP address of the device
        
    Returns:
        bool: True if device was removed, False otherwise
    """
    try:
        removed = blacklist_table.remove(Device.ip == ip)
        db_client.flush()  # Ensure changes are persisted
        if removed:
            logger.info(f"Removed device {ip} from blacklist")
        return bool(removed)
    except Exception as e:
        logger.error(f"Error removing device from blacklist: {str(e)}", exc_info=True)
        raise

def clear_blacklist():
    """
    Clears all entries from the blacklist database
    
    Returns:
        bool: True if successful
        
    Raises:
        Exception: If there was an error clearing the blacklist
    """
    try:
        logger.info("Clearing all entries from blacklist")
        blacklist_table.truncate()
        db_client.flush()  # Ensure the clearing is persisted
        logger.info("Successfully cleared blacklist")
        return True
    except Exception as e:
        logger.error(f"Error clearing blacklist: {str(e)}", exc_info=True)
        raise

def is_blacklist_mode_active():
    """
    Checks if blacklist mode is enabled in the database
    
    Returns:
        bool: True if blacklist mode is active, False otherwise
    """
    try:
        # Flush the storage to ensure we read the latest values
        db_client.flush()
        
        # Query for blacklist_mode setting
        setting_results = settings_table.search(Setting.name == 'blacklist_mode')
        logger.info(f"Checking blacklist mode - Found settings: {setting_results}")
        
        if setting_results and len(setting_results) > 0:
            setting = setting_results[0]
            logger.info(f"Checking blacklist mode - Setting structure: {setting}")
            
            # Only check for 'value' field - the standardized structure
            is_active = setting.get('value', False)
            logger.info(f"Blacklist mode status: {is_active}")
            return is_active
        else:
            # No setting found, initialize it
            logger.info("No blacklist_mode setting found, initializing to False")
            settings_table.upsert(
                {'name': 'blacklist_mode', 'value': False}, 
                Setting.name == 'blacklist_mode'
            )
            db_client.flush()
            return False
    except Exception as e:
        logger.error(f"Error checking blacklist mode: {str(e)}", exc_info=True)
        return False

def activate_blacklist_mode():
    """
    Sets the blacklist_mode setting to active in the database
    
    Returns:
        bool: True on success
    """
    try:
        # Update using standardized 'value' field structure
        logger.info("Activating blacklist mode with standard structure")
        settings_table.upsert(
            {'name': 'blacklist_mode', 'value': True}, 
            Setting.name == 'blacklist_mode'
        )
        
        # Verify the update worked
        after_setting = settings_table.search(Setting.name == 'blacklist_mode')
        logger.info(f"After update, settings: {after_setting}")
        
        # Make sure the settings table is actually persisted
        db_client.flush()
        
        return True
    except Exception as e:
        logger.error(f"Error activating blacklist mode: {str(e)}", exc_info=True)
        return False

def deactivate_blacklist_mode():
    """
    Sets the blacklist_mode setting to inactive in the database
    
    Returns:
        bool: True on success
    """
    try:
        # Update using standardized 'value' field structure
        logger.info("Deactivating blacklist mode with standard structure")
        settings_table.upsert(
            {'name': 'blacklist_mode', 'value': False}, 
            Setting.name == 'blacklist_mode'
        )
        
        # Verify the update worked
        after_setting = settings_table.search(Setting.name == 'blacklist_mode')
        logger.info(f"After update, settings: {after_setting}")
        
        # Make sure the settings table is actually persisted
        db_client.flush()
        
        return True
    except Exception as e:
        logger.error(f"Error deactivating blacklist mode: {str(e)}", exc_info=True)
        return False 