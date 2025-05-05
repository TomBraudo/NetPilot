from tinydb import Query
from db.tinydb_client import db_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_system_config(key, value):
    """
    Set a system configuration value.
    
    Args:
        key: Configuration key
        value: Configuration value
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure config table exists
        if 'system_config' not in db_client.db.tables():
            config_table = db_client.db.table('system_config')
        else:
            config_table = db_client.db.table('system_config')
            
        # Check if config already exists
        Config = Query()
        existing = config_table.get(Config.key == key)
        
        if existing:
            config_table.update({'value': value}, Config.key == key)
        else:
            config_table.insert({'key': key, 'value': value})
            
        return True
    except Exception as e:
        logger.error(f"Error setting system config: {e}")
        return False

def get_system_config(key, default=None):
    """
    Get a system configuration value.
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Value of the configuration key or default
    """
    try:
        # Ensure config table exists
        if 'system_config' not in db_client.db.tables():
            return default
            
        config_table = db_client.db.table('system_config')
        
        # Get config value
        Config = Query()
        config = config_table.get(Config.key == key)
        
        if config:
            return config.get('value', default)
        else:
            return default
    except Exception as e:
        logger.error(f"Error getting system config: {e}")
        return default 