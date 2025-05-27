from db.tinydb_client import db_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_all_tables():
    """Ensure the database client is initialized. Specific table setup is handled elsewhere or not needed."""
    try:
        # db_client is already initialized on import.
        # Flushing here might be redundant if no changes are made by this function.
        # db_client.flush()
        logger.info("Database client ensured to be initialized. No specific table initialization here.")
    except Exception as e:
        logger.error(f"Error during minimal table initialization: {e}", exc_info=True)
        raise

def reset_all_tables():
    """Reset tables in the main database (netpilot.json) except for 'whitelist' and 'blacklist'."""
    try:
        logger.info("Resetting tables in main database (netpilot.json)...")
        
        # Get all table names from the main db
        all_table_names_in_main_db = db_client.db.tables()
        
        tables_to_keep = {'whitelist', 'blacklist'}
        
        for table_name in all_table_names_in_main_db:
            if table_name not in tables_to_keep:
                db_client.db.drop_table(table_name)
                logger.info(f"Dropped table: {table_name} from main DB")
            else:
                logger.info(f"Kept table: {table_name} in main DB")

        # Re-initialize any necessary structures for the kept tables if needed (currently none defined here)
        # initialize_all_tables() # This function is now minimal, so calling it might be for logging/consistency
        logger.info("Main database tables reset (excluding whitelist, blacklist). Devices DB is separate.")
    except Exception as e:
        logger.error(f"Error resetting main DB tables: {e}", exc_info=True)
        raise