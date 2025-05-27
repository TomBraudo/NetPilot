from tinydb import TinyDB, Query
from utils.path_utils import get_data_folder
import os
from db.tinydb_client import db_client
from datetime import datetime
from utils.logging_config import get_logger
from db.device_repository import get_mac_from_ip

# Setup logging
logger = get_logger('db.whitelist')

# Use the initialized tables from db_client
whitelist_table = db_client.bandwidth_whitelist
settings_table = db_client.settings
Device = Query()
Setting = Query()

def get_whitelist():
    """
    Retrieves the list of whitelisted devices from the database
    
    Returns:
        list: List of whitelisted device entries
    """
    try:
        entries = whitelist_table.all()
        db_client.flush()  # Ensure we have the latest data
        return entries
    except Exception as e:
        logger.error(f"Error retrieving whitelist: {str(e)}", exc_info=True)
        return []

def add_to_whitelist(ip, name=None, description=None):
    """
    Adds a device to the whitelist database
    
    Args:
        ip (str): IP address of the device
        name (str, optional): Name of the device
        description (str, optional): Description of the device
        
    Returns:
        dict: The entry that was added
        
    Raises:
        ValueError: If the IP already exists in whitelist or if device not found in devices table
    """
    try:
        # Check if IP already exists in whitelist
        if whitelist_table.search(Device.ip == ip):
            logger.warning(f"Attempted to add IP {ip} that already exists in whitelist")
            raise ValueError(f"Device with IP {ip} already in whitelist")
        
        # Get MAC address from devices table
        mac = get_mac_from_ip(ip)
        if not mac:
            logger.warning(f"Attempted to add IP {ip} that does not exist in devices table")
            raise ValueError(f"Device with IP {ip} not found in devices table")
        
        # Add device to whitelist
        entry = {
            'ip': ip,
            'mac': mac,
            'name': name or f"Device-{ip}",
            'description': description or "",
            'added_at': str(datetime.now())
        }
        whitelist_table.insert(entry)
        db_client.flush()  # Ensure the entry is persisted
        
        logger.info(f"Added device with IP {ip} to whitelist")
        return entry
    except Exception as e:
        logger.error(f"Error adding to whitelist: {str(e)}", exc_info=True)
        raise

def remove_from_whitelist(ip):
    """
    Removes a device from the whitelist database
    
    Args:
        ip (str): IP address to remove
        
    Returns:
        str: The IP that was removed
        
    Raises:
        ValueError: If the IP was not found in whitelist
    """
    try:
        # Check if IP exists in whitelist
        if not whitelist_table.search(Device.ip == ip):
            logger.warning(f"Attempted to remove IP {ip} that does not exist in whitelist")
            raise ValueError(f"Device with IP {ip} not found in whitelist")
        
        # Remove from whitelist
        whitelist_table.remove(Device.ip == ip)
        db_client.flush()  # Ensure the removal is persisted
        
        logger.info(f"Removed device with IP {ip} from whitelist")
        return ip
    except Exception as e:
        logger.error(f"Error removing from whitelist: {str(e)}", exc_info=True)
        raise

def clear_whitelist():
    """
    Clears all entries from the whitelist database
    
    Returns:
        bool: True if successful
        
    Raises:
        Exception: If there was an error clearing the whitelist
    """
    try:
        logger.info("Clearing all entries from whitelist")
        whitelist_table.truncate()
        db_client.flush()  # Ensure the clearing is persisted
        logger.info("Successfully cleared whitelist")
        return True
    except Exception as e:
        logger.error(f"Error clearing whitelist: {str(e)}", exc_info=True)
        raise

def is_whitelist_mode_active():
    """
    Checks if whitelist mode is enabled in the database
    
    Returns:
        bool: True if whitelist mode is active, False otherwise
    """
    try:
        # Flush the storage to ensure we read the latest values
        db_client.flush()
        
        # Query for whitelist_mode setting
        setting_results = settings_table.search(Setting.name == 'whitelist_mode')
        logger.info(f"Checking whitelist mode - Found settings: {setting_results}")
        
        if setting_results and len(setting_results) > 0:
            setting = setting_results[0]
            logger.info(f"Checking whitelist mode - Setting structure: {setting}")
            
            # Only check for 'value' field - the standardized structure
            is_active = setting.get('value', False)
            logger.info(f"Whitelist mode status: {is_active}")
            return is_active
        else:
            # No setting found, initialize it
            logger.info("No whitelist_mode setting found, initializing to False")
            settings_table.upsert(
                {'name': 'whitelist_mode', 'value': False}, 
                Setting.name == 'whitelist_mode'
            )
            db_client.flush()
            return False
    except Exception as e:
        logger.error(f"Error checking whitelist mode: {str(e)}", exc_info=True)
        return False

def activate_whitelist_mode():
    """
    Sets the whitelist_mode setting to active in the database
    
    Returns:
        bool: True on success
    """
    try:
        # Update using standardized 'value' field structure
        logger.info("Activating whitelist mode with standard structure")
        settings_table.upsert(
            {'name': 'whitelist_mode', 'value': True}, 
            Setting.name == 'whitelist_mode'
        )
        
        # Verify the update worked
        after_setting = settings_table.search(Setting.name == 'whitelist_mode')
        logger.info(f"After update, settings: {after_setting}")
        
        # Make sure the settings table is actually persisted
        db_client.flush()
        
        return True
    except Exception as e:
        logger.error(f"Error activating whitelist mode: {str(e)}", exc_info=True)
        return False

def deactivate_whitelist_mode():
    """
    Sets the whitelist_mode setting to inactive in the database
    
    Returns:
        bool: True on success
    """
    try:
        # Update using standardized 'value' field structure
        logger.info("Deactivating whitelist mode with standard structure")
        settings_table.upsert(
            {'name': 'whitelist_mode', 'value': False}, 
            Setting.name == 'whitelist_mode'
        )
        
        # Verify the update worked
        after_setting = settings_table.search(Setting.name == 'whitelist_mode')
        logger.info(f"After update, settings: {after_setting}")
        
        # Make sure the settings table is actually persisted
        db_client.flush()
        
        return True
    except Exception as e:
        logger.error(f"Error deactivating whitelist mode: {str(e)}", exc_info=True)
        return False
