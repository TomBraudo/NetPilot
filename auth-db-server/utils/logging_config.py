import logging
import os
from datetime import datetime

def get_logger(name):
    """Get a logger instance with the specified name."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # Only add handlers if they don't exist
        logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # File handler for all logs
        log_file = os.path.join(logs_dir, 'main.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for INFO and above
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger 