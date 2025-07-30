"""
Whitelist Database Operations Service

This service handles all database operations for whitelist functionality.
It provides data validation, state checking, and CRUD operations for whitelist entries.
All functions return (result, error) tuple format.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from flask import g
from models.whitelist import UserWhitelist
from models.device import UserDevice
from models.user import User
from models.router import UserRouter
from models.settings import UserSetting
from utils.logging_config import get_logger
from .base import safe_dict_conversion, validate_uuid, handle_db_errors

logger = get_logger('services.db_operations.whitelist_db')


@handle_db_errors("Get whitelist")
def get_whitelist(user_id: str) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Get the current list of whitelisted device IP addresses for a user.
    
    Args:
        user_id: User's UUID
        
    Returns:
        Tuple of (list_of_ip_addresses, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    whitelist_entries = session.query(UserWhitelist).filter_by(user_id=user_id).all()
    ip_addresses = [str(entry.device_ip) for entry in whitelist_entries]
    return ip_addresses, None


@handle_db_errors("Add device to whitelist")
def add_device_to_whitelist(user_id: str, router_id: str, ip_address: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Add a device to the whitelist in the database.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        ip_address: Device IP address to whitelist
        
    Returns:
        Tuple of (created_whitelist_entry, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    # Step 1: Check if device is already in the whitelist
    existing_entry = session.query(UserWhitelist).filter_by(
        user_id=user_id,
        device_ip=ip_address
    ).first()
    
    # Step 2: If yes, return an error
    if existing_entry:
        return None, "Device is already whitelisted"
    
    # Step 3: Look up device info from user_devices table if exists
    device = session.query(UserDevice).filter_by(
        user_id=user_id,
        router_id=router_id,
        ip=ip_address
    ).first()
    
    # Step 4: Add the device to the whitelist using db operation
    whitelist_entry = UserWhitelist(
        user_id=user_id,
        router_id=router_id,
        device_ip=ip_address,
        device_id=device.id if device else None,
        device_mac=device.mac if device else None,
        device_name=device.device_name if device else None,
        added_at=datetime.now()
    )
    
    session.add(whitelist_entry)
    # Note: No need for flush/commit - Flask handles it automatically
    
    # Use safe_dict_conversion for response formatting
    result = safe_dict_conversion(whitelist_entry)
    logger.info(f"Added device {ip_address} to whitelist for user {user_id}, router {router_id}")
    return result, None


@handle_db_errors("Remove device from whitelist")
def remove_device_from_whitelist(user_id: str, router_id: str, ip_address: str) -> Tuple[Optional[bool], Optional[str]]:
    """
    Remove a device from the whitelist in the database.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        ip_address: Device IP address to remove from whitelist
        
    Returns:
        Tuple of (success_boolean, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    # Step 1: Find the whitelist entry
    whitelist_entry = session.query(UserWhitelist).filter_by(
        user_id=user_id,
        router_id=router_id,
        device_ip=ip_address
    ).first()

    # Step 2: If found, delete the entry
    if whitelist_entry:
        session.delete(whitelist_entry)
        # Note: No need for commit - Flask handles it automatically
        logger.info(f"Removed device {ip_address} from whitelist for user {user_id}, router {router_id}")
        return True, None

    # Step 3: If not found, return an error
    return False, "Device is not whitelisted"


@handle_db_errors("Check if device is whitelisted")
def is_device_whitelisted(user_id: str, router_id: str, ip_address: str) -> Tuple[Optional[bool], Optional[str]]:
    """
    Check if a device is already whitelisted.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        ip_address: Device IP address to check
        
    Returns:
        Tuple of (is_whitelisted_boolean, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    whitelist_entry = session.query(UserWhitelist).filter_by(
        user_id=user_id,
        router_id=router_id,
        device_ip=ip_address
    ).first()

    if whitelist_entry:
        return True, None
    return False, "Device is not whitelisted"

@handle_db_errors("Get whitelist mode setting")
def get_whitelist_mode_setting(user_id: str, router_id: str) -> Tuple[Optional[bool], Optional[str]]:
    """
    Get the current whitelist mode setting for a user and router.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        
    Returns:
        Tuple of (is_enabled_boolean, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    setting = session.query(UserSetting).filter_by(
        user_id=user_id,
        router_id=router_id,
        setting_key="whitelist_mode_enabled"
    ).first()
    
    if not setting:
        created_setting, error = _create_whitelist_mode_setting(user_id, router_id)
        if error:
            return None, error
        setting = created_setting
    
    return setting.setting_value['enabled'], None


@handle_db_errors("Activate whitelist mode")
def activate_whitelist_mode(user_id: str, router_id: str) -> Tuple[Optional[bool], Optional[str]]:
    """
    Activate whitelist mode for a user and router.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        
    Returns:
        Tuple of (success_boolean, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    setting = session.query(UserSetting).filter_by(
        user_id=user_id,
        router_id=router_id,
        setting_key="whitelist_mode_enabled"
    ).first()
    
    if not setting:
        created_setting, error = _create_whitelist_mode_setting(user_id, router_id)
        if error:
            return None, error
        setting = created_setting
    
    setting.setting_value = {'enabled': True}
    # Note: No need for commit - Flask handles it automatically
    logger.info(f"Activated whitelist mode for user {user_id}, router {router_id}")
    return True, None


@handle_db_errors("Deactivate whitelist mode")
def deactivate_whitelist_mode(user_id: str, router_id: str) -> Tuple[Optional[bool], Optional[str]]:
    """
    Deactivate whitelist mode for a user and router.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        
    Returns:
        Tuple of (success_boolean, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    setting = session.query(UserSetting).filter_by(
        user_id=user_id,
        router_id=router_id,
        setting_key="whitelist_mode_enabled"
    ).first()
    
    if not setting:
        created_setting, error = _create_whitelist_mode_setting(user_id, router_id)
        if error:
            return None, error
        setting = created_setting
    
    setting.setting_value = {'enabled': False}
    # Note: No need for commit - Flask handles it automatically
    logger.info(f"Deactivated whitelist mode for user {user_id}, router {router_id}")
    return True, None

@handle_db_errors("Get whitelist limit rate setting")
def get_whitelist_limit_rate_setting(user_id: str, router_id: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Get the current whitelist limit rate setting for a user and router.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        
    Returns:
        Tuple of (rate_mbps, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    setting = session.query(UserSetting).filter_by(
        user_id=user_id,
        router_id=router_id,
        setting_key="whitelist_limit_rate"
    ).first()
    
    if not setting:
        created_setting, error = _create_whitelist_limit_rate_setting(user_id, router_id)
        if error:
            return None, error
        setting = created_setting
    
    return setting.setting_value['rate_mbps'], None

@handle_db_errors("Set whitelist limit rate")
def set_whitelist_limit_rate(user_id: str, router_id: str, rate_mbps: int) -> Tuple[Optional[bool], Optional[str]]:
    """
    Set the whitelist limit rate for a user and router.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        rate_mbps: Rate in Mbps to set
        
    Returns:
        Tuple of (success_boolean, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    setting = session.query(UserSetting).filter_by(
        user_id=user_id,
        router_id=router_id,
        setting_key="whitelist_limit_rate"
    ).first()
    
    if not setting:
        created_setting, error = _create_whitelist_limit_rate_setting(user_id, router_id)
        if error:
            return None, error
        setting = created_setting
    
    setting.setting_value = {'rate_mbps': rate_mbps}
    # Note: No need for commit - Flask handles it automatically
    logger.info(f"Set whitelist limit rate for user {user_id}, router {router_id} to {rate_mbps} Mbps")
    return True, None

@handle_db_errors("Create whitelist mode setting")
def _create_whitelist_mode_setting(user_id: str, router_id: str) -> Tuple[Optional[UserSetting], Optional[str]]:
    """
    Internal method: Create whitelist mode enabled setting with default value (disabled).
    Only use when the setting doesn't exist.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        
    Returns:
        Tuple of (created_setting, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    setting_key = "whitelist_mode_enabled"
    default_value = {'enabled': False}
    
    new_setting = UserSetting(
        user_id=user_id,
        router_id=router_id,
        setting_key=setting_key,
        setting_value=default_value
    )
    
    session.add(new_setting)
    # Note: No need for commit - Flask handles it automatically
    
    logger.info(f"Created whitelist mode setting for user {user_id}, router {router_id} with default: disabled")
    return new_setting, None


@handle_db_errors("Create whitelist limit rate setting")
def _create_whitelist_limit_rate_setting(user_id: str, router_id: str) -> Tuple[Optional[UserSetting], Optional[str]]:
    """
    Internal method: Create whitelist limit rate setting with default value (50 mbps).
    Only use when the setting doesn't exist.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        
    Returns:
        Tuple of (created_setting, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    setting_key = "whitelist_limit_rate"
    default_value = {'rate_mbps': 50}
    
    new_setting = UserSetting(
        user_id=user_id,
        router_id=router_id,
        setting_key=setting_key,
        setting_value=default_value
    )
    
    session.add(new_setting)
    # Note: No need for commit - Flask handles it automatically
    
    logger.info(f"Created whitelist limit rate setting for user {user_id}, router {router_id} with default: 50 mbps")
    return new_setting, None
