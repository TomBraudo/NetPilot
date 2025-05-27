#!/usr/bin/env python3
from utils.path_utils import get_data_folder
from utils.logging_config import get_logger
from services.whitelist_bandwidth import deactivate_whitelist_mode
from services.blacklist_bandwidth import deactivate_blacklist_mode
import os
import json

# Get logger for bandwidth mode service
logger = get_logger('bandwidth.mode')

# Get the mode config file path
mode_config_path = os.path.join(get_data_folder(), "bandwidth_mode.json")

def load_mode_config():
    """
    Loads the bandwidth mode configuration from the config file
    
    Returns:
        dict: The mode configuration
    """
    try:
        with open(mode_config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # If file doesn't exist, create it with default settings
        default_config = {"current_mode": "none"}
        with open(mode_config_path, 'w') as f:
            json.dump(default_config, f)
        return default_config

def get_current_mode():
    """
    Gets the current bandwidth mode
    
    Returns:
        str: Current mode ("whitelist", "blacklist", or "none")
    """
    config = load_mode_config()
    current_mode = config.get("current_mode", "none")
    logger.info(f"Current bandwidth mode: {current_mode}")
    return current_mode

def set_mode(new_mode):
    """
    Sets the bandwidth mode, handling mode transitions
    
    Args:
        new_mode (str): The mode to set ("whitelist", "blacklist", or "none")
        
    Returns:
        bool: True if successful
        
    Raises:
        ValueError: If new_mode is invalid
    """
    if new_mode not in ["whitelist", "blacklist", "none"]:
        logger.error(f"Invalid mode requested: {new_mode}")
        raise ValueError("Mode must be 'whitelist', 'blacklist', or 'none'")
    
    try:
        current_mode = get_current_mode()
        logger.info(f"Switching bandwidth mode from {current_mode} to {new_mode}")
        
        # If switching to a new mode, deactivate current mode first
        if current_mode != "none":
            if current_mode == "whitelist":
                deactivate_whitelist_mode()
            elif current_mode == "blacklist":
                deactivate_blacklist_mode()
        
        # Update the mode in the config file
        config = load_mode_config()
        config["current_mode"] = new_mode
        with open(mode_config_path, 'w') as f:
            json.dump(config, f)
        
        logger.info(f"Successfully switched bandwidth mode to {new_mode}")
        return True
    except Exception as e:
        logger.error(f"Error switching bandwidth mode: {str(e)}", exc_info=True)
        raise

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
            result = deactivate_whitelist_mode()
        elif current_mode == "blacklist":
            result = deactivate_blacklist_mode()
        else:
            logger.info("No active mode to deactivate")
            result = True
        
        if result:
            # Set mode to none
            config = load_mode_config()
            config["current_mode"] = "none"
            with open(mode_config_path, 'w') as f:
                json.dump(config, f)
            logger.info("Successfully deactivated current mode")
        
        return result
    except Exception as e:
        logger.error(f"Error deactivating current mode: {str(e)}", exc_info=True)
        return False 