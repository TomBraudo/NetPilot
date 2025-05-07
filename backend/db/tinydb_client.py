from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
import os
from utils.path_utils import get_data_folder
from utils.logging_config import get_logger

# Get logger for database operations
logger = get_logger('db.tinydb')

# Get path for database file
DB_PATH = os.path.join(get_data_folder(), "netpilot.json")

class TinyDBClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TinyDBClient, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self):
        """Initialize the TinyDB instance with caching for better performance."""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            
            # Initialize TinyDB with explicit caching middleware
            self.db = TinyDB(
                DB_PATH, 
                storage=CachingMiddleware(JSONStorage)
            )
            logger.info(f"TinyDB initialized with caching middleware at {DB_PATH}")
            
            # Initialize tables (collections)
            self.devices = self.db.table('devices')
            self.device_groups = self.db.table('device_groups')
            self.group_members = self.db.table('group_members')
            self.rules = self.db.table('rules')
            self.device_rules = self.db.table('device_rules')
            self.bandwidth_whitelist = self.db.table('whitelist')
            self.settings = self.db.table('settings')
            
            # Initialize default settings if they don't exist
            self.initialize_settings()
            
            logger.info(f"TinyDB tables initialized")
        except Exception as e:
            logger.error(f"Failed to initialize TinyDB: {e}", exc_info=True)
            raise
    
    def initialize_settings(self):
        """Initialize default settings in the settings table"""
        Setting = Query()
        
        # Define default settings
        default_settings = [
            {'name': 'whitelist_mode', 'value': False},
            # Add other default settings here as needed
        ]
        
        # Insert default settings if they don't already exist
        for setting in default_settings:
            if not self.settings.get(Setting.name == setting['name']):
                self.settings.insert(setting)
                logger.info(f"Initialized setting {setting['name']} to {setting['value']}")
            else:
                # Ensure consistent structure - convert any existing entries to use 'value' field
                existing = self.settings.get(Setting.name == setting['name'])
                if 'value' not in existing:
                    # Convert from legacy format to standard format
                    if 'default' in existing:
                        new_value = existing['default'] != '0'
                        self.settings.update({'value': new_value}, Setting.name == setting['name'])
                        logger.info(f"Converted setting {setting['name']} from legacy format to value={new_value}")
                
        # Ensure settings are persisted
        self.flush()
    
    def flush(self):
        """Force flush all cached writes to disk."""
        try:
            if hasattr(self.db.storage, 'flush'):
                self.db.storage.flush()
                logger.debug("Database cache flushed to disk")
            else:
                logger.warning("Database storage does not support flushing")
        except Exception as e:
            logger.error(f"Error flushing database: {str(e)}", exc_info=True)
    
    def clear_all(self):
        """Clear all data from all tables."""
        for table_name in ['devices', 'device_groups', 'group_members', 'rules', 'device_rules']:
            table = self.db.table(table_name)
            table.truncate()
        logger.info("All tables cleared")
        self.flush()

    def close(self):
        """Close the database connection."""
        self.flush()
        self.db.close()
        logger.info("TinyDB connection closed")

# Create a singleton instance
db_client = TinyDBClient() 