import logging
import logging.handlers
import os
import sys
from datetime import datetime

# Get the absolute path to the backend directory
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BACKEND_DIR, 'logs')

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# Define log files
MAIN_LOG_FILE = os.path.join(LOGS_DIR, 'netpilot.log')
ERROR_LOG_FILE = os.path.join(LOGS_DIR, 'error.log')
WHITELIST_LOG_FILE = os.path.join(LOGS_DIR, 'whitelist.log')
DB_LOG_FILE = os.path.join(LOGS_DIR, 'database.log')

# Log format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def configure_logging():
    """
    Configure the logging system to write logs to files with rotation
    """
    # Create formatters
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler for showing errors on stderr
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.ERROR)
    console.setFormatter(console_formatter)
    root_logger.addHandler(console)
    
    # Create main rotating file handler - 5MB files, keep 5 backups
    main_handler = logging.handlers.RotatingFileHandler(
        MAIN_LOG_FILE, maxBytes=5*1024*1024, backupCount=5
    )
    main_handler.setLevel(logging.INFO)
    main_handler.setFormatter(file_formatter)
    root_logger.addHandler(main_handler)
    
    # Create error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG_FILE, maxBytes=5*1024*1024, backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    configure_module_logger('db', DB_LOG_FILE)
    configure_module_logger('whitelist', WHITELIST_LOG_FILE)
    
    # Log startup
    logging.info(f"Logging initialized at {datetime.now().strftime(DATE_FORMAT)}")
    logging.info(f"Log files directory: {LOGS_DIR}")

def configure_module_logger(module_name, log_file):
    """Configure a logger for a specific module"""
    logger = logging.getLogger(module_name)
    
    # Create rotating file handler - 5MB files, keep 5 backups
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=5
    )
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(handler)
    
    return logger

def get_logger(name):
    """Get a logger with the specified name"""
    return logging.getLogger(name)

# Initialize logging when this module is imported
configure_logging() 