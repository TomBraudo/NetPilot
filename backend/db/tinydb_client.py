from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
import os
from utils.path_utils import get_data_folder
from utils.logging_config import get_logger

# Get logger for database operations
logger = get_logger('db.tinydb')

# Get paths for database files
DB_PATH = os.path.join(get_data_folder(), "netpilot.json")
DEVICES_DB_PATH = os.path.join(get_data_folder(), "devices.json")

class TinyDBClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TinyDBClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return

        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            
            # Initialize main TinyDB with explicit caching middleware
            self.db = TinyDB(
                DB_PATH, 
                storage=CachingMiddleware(JSONStorage)
            )
            logger.info(f"TinyDB initialized with caching middleware at {DB_PATH}")
            
            # Initialize devices TinyDB with explicit caching middleware
            self.devices_db = TinyDB(
                DEVICES_DB_PATH,
                storage=CachingMiddleware(JSONStorage)
            )
            logger.info(f"Devices TinyDB initialized with caching middleware at {DEVICES_DB_PATH}")
            
            # Initialize tables (collections)
            self.devices = self.devices_db.table('devices')
            self.device_groups = self.db.table('device_groups')
            self.group_members = self.db.table('group_members')
            self.rules = self.db.table('rules')
            self.device_rules = self.db.table('device_rules')
            self.bandwidth_whitelist = self.db.table('whitelist')
            self.bandwidth_blacklist = self.db.table('blacklist')
            self.settings = self.db.table('settings')
            
            # Initialize default settings if they don't exist
            self.initialize_settings()
            
            # Ensure tables are created and persisted
            self.flush()
            
            logger.info(f"TinyDB tables initialized")
            self._initialized = True
        except Exception as e:
            logger.error(f"Error initializing TinyDB: {str(e)}", exc_info=True)
            raise
    
    def initialize_settings(self):
        """Initialize default settings if they don't exist."""
        try:
            if not self.settings.contains(Query().name == 'whitelist_mode'):
                self.settings.insert({
                    'name': 'whitelist_mode',
                    'value': False,
                    'description': 'Whether whitelist mode is active'
                })
                self.flush()
        except Exception as e:
            logger.error(f"Error initializing settings: {str(e)}", exc_info=True)
    
    def flush(self):
        """Force flush all cached writes to disk."""
        try:
            if hasattr(self.db.storage, 'flush'):
                self.db.storage.flush()
                logger.debug("Main database cache flushed to disk")
            else:
                logger.warning("Main database storage does not support flushing")
                
            if hasattr(self.devices_db.storage, 'flush'):
                self.devices_db.storage.flush()
                logger.debug("Devices database cache flushed to disk")
            else:
                logger.warning("Devices database storage does not support flushing")
        except Exception as e:
            logger.error(f"Error flushing database: {str(e)}", exc_info=True)
    
    def close(self):
        """Close the database connections and flush any pending writes."""
        try:
            self.flush()
            self.db.close()
            self.devices_db.close()
            logger.info("TinyDB connections closed")
        except Exception as e:
            logger.error(f"Error closing TinyDB connections: {str(e)}", exc_info=True)

# Create a singleton instance
db_client = TinyDBClient() 