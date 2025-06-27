#!/usr/bin/env python3
from utils.logging_config import get_logger
from utils.response_helpers import success, error
from utils.config_manager import config_manager

# Get logger for bandwidth mode service
logger = get_logger('services.bandwidth_mode')

def get_current_mode_value():
    """
    Gets the current operational mode from the persistent mode configuration file.
    Returns the mode and a None error on success.
    """
    try:
        mode_config = config_manager.load_config('mode')
        return mode_config.get('mode', 'none'), None
    except FileNotFoundError:
        logger.warning("mode.json not found. Creating a default file and defaulting to 'none' mode.")
        # Create a default mode file and return the default value
        _, err = set_current_mode_value('none')
        if err:
            return None, "Failed to create a default mode file."
        return 'none', None
    except Exception as e:
        logger.error(f"Error loading mode configuration: {e}", exc_info=True)
        return None, "Failed to load mode configuration."

def set_current_mode_value(mode):
    """
    Sets the current operational mode in the persistent mode configuration file.
    """
    if mode not in ['none', 'whitelist', 'blacklist']:
        err_msg = f"Invalid mode specified: {mode}. Must be 'none', 'whitelist', or 'blacklist'."
        logger.error(err_msg)
        return None, err_msg
    
    try:
        mode_config = {'mode': mode}
        config_manager.save_config('mode', mode_config)
        logger.info(f"Bandwidth mode set to '{mode}'.")
        return f"Mode set to {mode}.", None
    except Exception as e:
        logger.error(f"Error saving mode configuration: {e}", exc_info=True)
        return None, "Failed to save mode configuration."

def get_current_mode():
    """Get the current bandwidth mode for API endpoints."""
    mode, err = get_current_mode_value()
    if err:
        return None, err
    return {"mode": mode}, None

def set_mode(mode):
    """Set the bandwidth mode - upstream validation ensures mode is valid"""
    result = set_current_mode_value(mode)
    return result

def is_whitelist_mode():
    """Check if whitelist mode is active"""
    mode, _ = get_current_mode_value()
    return mode == 'whitelist'

def is_blacklist_mode():
    """Check if blacklist mode is active"""
    mode, _ = get_current_mode_value()
    return mode == 'blacklist'

def is_mode_active():
    """Check if any bandwidth limiting mode is active"""
    mode, _ = get_current_mode_value()
    return mode != 'normal'

def reset_mode():
    """Reset mode to 'normal'"""
    _, err = set_current_mode_value('normal')
    if err:
        return None, err
    return success(message="Mode reset to 'normal'"), None 