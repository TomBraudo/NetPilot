#!/usr/bin/env python3
from utils.logging_config import get_logger
from utils.response_helpers import success

# Get logger for bandwidth mode service
logger = get_logger('bandwidth.mode')

# In-memory mode storage (will be replaced with session-based storage in Phase 1)
_current_mode = 'none'

def get_current_mode_value():
    """Get the current bandwidth mode (internal use)"""
    global _current_mode
    return _current_mode

def set_current_mode_value(mode):
    """Set the current bandwidth mode (internal use)"""
    global _current_mode
    if mode not in ['none', 'whitelist', 'blacklist']:
        raise ValueError(f"Invalid mode: {mode}. Must be 'none', 'whitelist', or 'blacklist'")
    _current_mode = mode
    logger.info(f"Mode set to: {mode}")
    return success(data={"mode": mode})

def get_current_mode():
    """Get the current bandwidth mode"""
    mode = get_current_mode_value()
    return success(data={"mode": mode})

def set_mode(mode):
    """Set the bandwidth mode - upstream validation ensures mode is valid"""
    result = set_current_mode_value(mode)
    return result

def is_whitelist_mode():
    """Check if whitelist mode is active"""
    return get_current_mode_value() == 'whitelist'

def is_blacklist_mode():
    """Check if blacklist mode is active"""
    return get_current_mode_value() == 'blacklist'

def is_mode_active():
    """Check if any bandwidth limiting mode is active"""
    return get_current_mode_value() != 'none'

def reset_mode():
    """Reset mode to 'none'"""
    set_current_mode_value('none')
    return success(message="Mode reset to 'none'") 