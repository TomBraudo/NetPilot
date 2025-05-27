import sys
import os
import logging

# Add both the current directory and the backend directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.extend([current_dir, backend_dir])

from migrations.migrate_to_mac_primary import run_migration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the database migration."""
    try:
        logger.info("Starting database migration")
        success = run_migration()
        
        if success:
            logger.info("Migration completed successfully")
        else:
            logger.error("Migration failed")
            
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return False
    
    return success

if __name__ == "__main__":
    main() 