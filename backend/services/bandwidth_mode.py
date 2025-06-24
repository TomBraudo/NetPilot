#!/usr/bin/env python3
from utils.logging_config import get_logger
from utils.response_helpers import success
from services.whitelist_service import deactivate_whitelist_mode as actual_deactivate_whitelist
from services.blacklist_service import deactivate_blacklist_mode as actual_deactivate_blacklist
from services.mode_state_service import get_current_mode_value, set_current_mode_value

# Get logger for bandwidth mode service
logger = get_logger('bandwidth.mode')

# Default mode is 'none'
DEFAULT_MODE = 'none'

def get_current_mode_internal():
    """Get the current bandwidth mode (internal use, fetches from state service)"""
    try:
        return get_current_mode_value()
    except Exception as e:
        logger.error(f"Error getting current mode: {str(e)}", exc_info=True)
        raise

def get_current_mode():
    """Get the current bandwidth mode (API response)"""
    try:
        mode = get_current_mode_value()
        return success(data={"mode": mode})
    except Exception as e:
        logger.error(f"Error getting current mode: {str(e)}", exc_info=True)
        raise

def set_mode(mode):
    """Set the bandwidth mode"""
    try:
        result = set_current_mode_value(mode)
        return result
    except Exception as e:
        logger.error(f"Error setting bandwidth mode: {str(e)}", exc_info=True)
        raise

def is_whitelist_mode():
    """
    Checks if whitelist mode is active
    
    Returns:
        bool: True if whitelist mode is active
    """
    return get_current_mode_value() == 'whitelist'

def is_blacklist_mode():
    """
    Checks if blacklist mode is active
    
    Returns:
        bool: True if blacklist mode is active
    """
    return get_current_mode_value() == 'blacklist'

def is_mode_active():
    """
    Checks if any bandwidth limiting mode is active
    
    Returns:
        bool: True if either whitelist or blacklist mode is active
    """
    return get_current_mode_value() != 'none'

def deactivate_current_mode():
    """
    Deactivates the current bandwidth mode by calling the specific service's deactivation.
    The specific service is responsible for cleanup and setting mode to 'none' via mode_state_service.
    
    Returns:
        dict: Success or error response from the specific deactivation function.
    """
    try:
        current_mode = get_current_mode_value()
        logger.info(f"Attempting to deactivate current bandwidth mode: {current_mode}")
        
        response = None
        if current_mode == "whitelist":
            response = actual_deactivate_whitelist()
        elif current_mode == "blacklist":
            response = actual_deactivate_blacklist()
        else:
            logger.info("No active mode to deactivate")
            response = success(message="No active mode to deactivate")
        
        return response

    except Exception as e:
        logger.error(f"Error deactivating current mode: {str(e)}", exc_info=True)
        raise 