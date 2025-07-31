"""
Blacklist Database Operations Service

This service handles all database operations for blacklist functionality.
It provides data validation, state checking, and CRUD operations for blacklist entries.
All functions return (result, error) tuple format.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from flask import g
from models.blacklist import UserBlacklist
from models.device import UserDevice
from models.user import User
from models.router import UserRouter
from models.settings import UserSetting
from utils.logging_config import get_logger
from .base import safe_dict_conversion, validate_uuid, handle_db_errors

logger = get_logger('services.db_operations.blacklist_db')


@handle_db_errors("Get blacklist")
def get_blacklist(user_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Get the current list of blacklisted devices for a user with full device information.
    
    Args:
        user_id: User's UUID
        
    Returns:
        Tuple of (list_of_device_objects, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    blacklist_entries = session.query(UserBlacklist).filter_by(user_id=user_id).all()
    devices = []
    
    for entry in blacklist_entries:
        device_data = {
            "id": str(entry.id),
            "device_name": entry.device_name or "Unknown Device",
            "mac_address": str(entry.device_mac) if entry.device_mac else None,
            "ip": str(entry.device_ip),
            "description": entry.description,
            "created_at": entry.created_at.isoformat() if entry.created_at else None
        }
        devices.append(device_data)
    
    return devices, None


@handle_db_errors("Add device to blacklist")
def add_device_to_blacklist(user_id: str, router_id: str, ip_address: str, device_name: str = None, description: str = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Add a device to the blacklist in the database.
    
    Note: This function assumes the caller has already checked if the device exists.
    It performs the database insertion without duplicate checking.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        ip_address: Device IP address to blacklist
        device_name: Device name/hostname (optional)
        description: Device description (optional)
        
    Returns:
        Tuple of (created_blacklist_entry, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    # Look up device info from user_devices table if exists
    device = session.query(UserDevice).filter_by(
        user_id=user_id,
        router_id=router_id,
        ip=ip_address
    ).first()
    
    # Use device_name from database if available, otherwise use provided device_name
    # Priority: 1) device.device_name (custom name), 2) device.hostname, 3) provided device_name
    final_device_name = None
    if device:
        final_device_name = device.device_name or device.hostname
    if not final_device_name:
        final_device_name = device_name
    
    # Add the device to the blacklist using db operation
    blacklist_entry = UserBlacklist(
        user_id=user_id,
        router_id=router_id,
        device_ip=ip_address,
        device_id=device.id if device else None,
        device_mac=device.mac if device else None,
        device_name=final_device_name,
        description=description,  # Use provided description
        added_at=datetime.now()
    )
    
    session.add(blacklist_entry)
    # Note: Commit/rollback handled automatically by Flask's after_request handler
    
    # Use safe_dict_conversion for response formatting
    result = safe_dict_conversion(blacklist_entry)
    logger.info(f"Added device {ip_address} to blacklist for user {user_id}, router {router_id}")
    return result, None


@handle_db_errors("Remove device from blacklist")
def remove_device_from_blacklist(user_id: str, router_id: str, ip_address: str) -> Tuple[Optional[bool], Optional[str]]:
    """
    Remove a device from the blacklist in the database.
    
    Note: This function assumes the caller has already checked if the device exists.
    It performs the database deletion and returns True if found and deleted, False if not found.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        ip_address: Device IP address to remove from blacklist
        
    Returns:
        Tuple of (success_boolean, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    # Find and remove the blacklist entry
    blacklist_entry = session.query(UserBlacklist).filter_by(
        user_id=user_id,
        router_id=router_id,
        device_ip=ip_address
    ).first()

    if blacklist_entry:
        session.delete(blacklist_entry)
        # Note: Commit/rollback handled automatically by Flask's after_request handler
        logger.info(f"Removed device {ip_address} from blacklist for user {user_id}, router {router_id}")
        return True, None

    # If not found, return False (but no error - this is handled by service layer)
    return False, None


@handle_db_errors("Check if device is blacklisted")
def is_device_blacklisted(user_id: str, router_id: str, ip_address: str) -> Tuple[Optional[bool], Optional[str]]:
    """
    Check if a device is already blacklisted.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        ip_address: Device IP address to check
        
    Returns:
        Tuple of (is_blacklisted_boolean, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    blacklist_entry = session.query(UserBlacklist).filter_by(
        user_id=user_id,
        router_id=router_id,
        device_ip=ip_address
    ).first()

    if blacklist_entry:
        return True, None
    return False, None

@handle_db_errors("Get blacklist mode setting")
def get_blacklist_mode_setting(user_id: str, router_id: str) -> Tuple[Optional[bool], Optional[str]]:
    """
    Get the current blacklist mode setting for a user and router.
    
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
        setting_key="blacklist_mode_enabled"
    ).first()
    
    if not setting:
        created_setting, error = _create_blacklist_mode_setting(user_id, router_id)
        if error:
            return None, error
        setting = created_setting
    
    return setting.setting_value['enabled'], None


@handle_db_errors("Activate blacklist mode")
def activate_blacklist_mode(user_id: str, router_id: str) -> Tuple[Optional[bool], Optional[str]]:
    """
    Activate blacklist mode for a user and router.
    
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
        setting_key="blacklist_mode_enabled"
    ).first()
    
    if not setting:
        created_setting, error = _create_blacklist_mode_setting(user_id, router_id)
        if error:
            return None, error
        setting = created_setting
    
    setting.setting_value = {'enabled': True}
    # Note: Commit/rollback handled automatically by Flask's after_request handler
    logger.info(f"Activated blacklist mode for user {user_id}, router {router_id}")
    return True, None


@handle_db_errors("Deactivate blacklist mode")
def deactivate_blacklist_mode(user_id: str, router_id: str) -> Tuple[Optional[bool], Optional[str]]:
    """
    Deactivate blacklist mode for a user and router.
    
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
        setting_key="blacklist_mode_enabled"
    ).first()
    
    if not setting:
        created_setting, error = _create_blacklist_mode_setting(user_id, router_id)
        if error:
            return None, error
        setting = created_setting
    
    setting.setting_value = {'enabled': False}
    # Note: Commit/rollback handled automatically by Flask's after_request handler
    logger.info(f"Deactivated blacklist mode for user {user_id}, router {router_id}")
    return True, None

@handle_db_errors("Get blacklist limit rate setting")
def get_blacklist_limit_rate_setting(user_id: str, router_id: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Get the current blacklist limit rate setting for a user and router.
    
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
        setting_key="blacklist_limit_rate"
    ).first()
    
    if not setting:
        created_setting, error = _create_blacklist_limit_rate_setting(user_id, router_id)
        if error:
            return None, error
        setting = created_setting
    
    return setting.setting_value['rate_mbps'], None

@handle_db_errors("Set blacklist limit rate")
def set_blacklist_limit_rate(user_id: str, router_id: str, rate_mbps: int) -> Tuple[Optional[bool], Optional[str]]:
    """
    Set the blacklist limit rate for a user and router.
    
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
        setting_key="blacklist_limit_rate"
    ).first()
    
    if not setting:
        created_setting, error = _create_blacklist_limit_rate_setting(user_id, router_id)
        if error:
            return None, error
        setting = created_setting
    
    setting.setting_value = {'rate_mbps': rate_mbps}
    # Note: Commit/rollback handled automatically by Flask's after_request handler
    logger.info(f"Set blacklist limit rate for user {user_id}, router {router_id} to {rate_mbps} Mbps")
    return True, None

@handle_db_errors("Create blacklist mode setting")
def _create_blacklist_mode_setting(user_id: str, router_id: str) -> Tuple[Optional[UserSetting], Optional[str]]:
    """
    Internal method: Create blacklist mode enabled setting with default value (disabled).
    Only use when the setting doesn't exist.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        
    Returns:
        Tuple of (created_setting, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    setting_key = "blacklist_mode_enabled"
    default_value = {'enabled': False}
    
    new_setting = UserSetting(
        user_id=user_id,
        router_id=router_id,
        setting_key=setting_key,
        setting_value=default_value
    )
    
    session.add(new_setting)
    # Note: Commit/rollback handled automatically by Flask's after_request handler
    
    logger.info(f"Created blacklist mode setting for user {user_id}, router {router_id} with default: disabled")
    return new_setting, None


@handle_db_errors("Create blacklist limit rate setting")
def _create_blacklist_limit_rate_setting(user_id: str, router_id: str) -> Tuple[Optional[UserSetting], Optional[str]]:
    """
    Internal method: Create blacklist limit rate setting with default value (50 mbps).
    Only use when the setting doesn't exist.
    
    Args:
        user_id: User's UUID
        router_id: Router's ID
        
    Returns:
        Tuple of (created_setting, error_message)
    """
    # Get database session from Flask's g object
    session = g.db_session
    
    setting_key = "blacklist_limit_rate"
    default_value = {'rate_mbps': 50}
    
    new_setting = UserSetting(
        user_id=user_id,
        router_id=router_id,
        setting_key=setting_key,
        setting_value=default_value
    )
    
    session.add(new_setting)
    # Note: Commit/rollback handled automatically by Flask's after_request handler
    
    logger.info(f"Created blacklist limit rate setting for user {user_id}, router {router_id} with default: 50 mbps")
    return new_setting, None
