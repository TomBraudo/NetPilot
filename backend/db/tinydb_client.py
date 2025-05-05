from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
import os
from utils.path_utils import get_data_folder
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = os.path.join(get_data_folder(), '.env')
load_dotenv(dotenv_path=env_path)

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
            
            # Initialize TinyDB with caching for better performance
            self.db = TinyDB(DB_PATH, storage=CachingMiddleware(JSONStorage))
            
            # Initialize tables (collections)
            self.devices = self.db.table('devices')
            self.device_groups = self.db.table('device_groups')
            self.group_members = self.db.table('group_members')
            self.rules = self.db.table('rules')
            self.device_rules = self.db.table('device_rules')
            
            logger.info(f"TinyDB initialized at {DB_PATH}")
        except Exception as e:
            logger.error(f"Failed to initialize TinyDB: {e}")
            raise
    
    def clear_all(self):
        """Clear all data from all tables."""
        tables = ['devices', 'device_groups', 'group_members', 'rules', 'device_rules']
        for table_name in tables:
            table = self.db.table(table_name)
            table.truncate()
        logger.info("All tables cleared")

    def close(self):
        """Close the database connection."""
        if hasattr(self, 'db'):
            self.db.close()
            logger.info("TinyDB connection closed")

# Initialize the singleton instance
db_client = TinyDBClient() 