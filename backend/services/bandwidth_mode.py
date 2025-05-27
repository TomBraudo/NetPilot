#!/usr/bin/env python3
from utils.path_utils import get_data_folder
from utils.logging_config import get_logger
from utils.config_manager import config_manager
import os
import json

# Get logger for bandwidth mode service
logger = get_logger('bandwidth.mode')

# Default mode is 'none'
DEFAULT_MODE = 'none'

def load_mode_config():
    """
    Loads the mode configuration from the config file
    
    Returns:
        dict: The mode configuration
    """
    return config_manager.load_config('mode')

def save_mode_config(config):
    """
    Saves the mode configuration to the config file
    
    Args:
        config (dict): The mode configuration to save
    """
    config_manager.save_config('mode', config)

def get_current_mode():
    """
    Gets the current bandwidth mode
    
    Returns:
        str: The current mode ('none', 'whitelist', or 'blacklist')
    """
    config = load_mode_config()
    return config.get('mode', DEFAULT_MODE)

def set_mode(mode):
    """
    Sets the bandwidth mode
    
    Args:
        mode (str): The mode to set ('none', 'whitelist', or 'blacklist')
        
    Returns:
        str: The mode that was set
        
    Raises:
        ValueError: If an invalid mode is provided
    """
    if mode not in ['none', 'whitelist', 'blacklist']:
        raise ValueError(f"Invalid mode: {mode}. Must be one of: none, whitelist, blacklist")
    
    config = load_mode_config()
    config['mode'] = mode
    save_mode_config(config)
    logger.info(f"Bandwidth mode set to {mode}")
    return mode

def is_whitelist_mode():
    """
    Checks if whitelist mode is active
    
    Returns:
        bool: True if whitelist mode is active
    """
    return get_current_mode() == 'whitelist'

def is_blacklist_mode():
    """
    Checks if blacklist mode is active
    
    Returns:
        bool: True if blacklist mode is active
    """
    return get_current_mode() == 'blacklist'

def is_mode_active():
    """
    Checks if any bandwidth limiting mode is active
    
    Returns:
        bool: True if either whitelist or blacklist mode is active
    """
    return get_current_mode() != 'none'

def deactivate_current_mode():
    """
    Deactivates the current bandwidth mode
    
    Returns:
        bool: True if successful
    """
    try:
        current_mode = get_current_mode()
        logger.info(f"Deactivating current bandwidth mode: {current_mode}")
        
        if current_mode == "whitelist":
            from services.whitelist_bandwidth import deactivate_whitelist_mode
            result = deactivate_whitelist_mode()
        elif current_mode == "blacklist":
            from services.blacklist_bandwidth import deactivate_blacklist_mode
            result = deactivate_blacklist_mode()
        else:
            logger.info("No active mode to deactivate")
            result = True
        
        if result:
            # Set mode to none
            config = load_mode_config()
            config["mode"] = "none"
            save_mode_config(config)
            logger.info("Successfully deactivated current mode")
        
        return result
    except Exception as e:
        logger.error(f"Error deactivating current mode: {str(e)}", exc_info=True)
        return False 