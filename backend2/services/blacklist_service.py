"""
Blacklist Service - Main Orchestration Layer

This service acts as the conductor for blacklist operations, coordinating between
database operations and router command executions. It follows the 3-layer architecture:
1. This service (orchestration) - calls db + commands
2. services/db_operations/blacklist_db.py - Database operations  
3. services/commands_server_operations/blacklist_execute.py - Router command execution
"""

from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import (
    require_user_context,
    handle_service_errors,
    validate_ip_address,
    validate_rate_limit,
    log_service_operation
)

# Database operations imports
from services.db_operations.blacklist_db import (
    get_blacklist as db_get_blacklist,
    add_device_to_blacklist as db_add_device_to_blacklist,
    remove_device_from_blacklist as db_remove_device_from_blacklist,
    is_device_blacklisted as db_is_device_blacklisted,
    get_blacklist_mode_setting as db_get_blacklist_mode_setting,
    activate_blacklist_mode as db_activate_blacklist_mode,
    deactivate_blacklist_mode as db_deactivate_blacklist_mode,
    get_blacklist_limit_rate_setting as db_get_blacklist_limit_rate_setting,
    set_blacklist_limit_rate as db_set_blacklist_limit_rate
)

# Router command execution imports
from services.commands_server_operations.blacklist_execute import (
    execute_get_blacklist,
    execute_add_device_to_blacklist,
    execute_remove_device_from_blacklist,
    execute_set_blacklist_rate_limit,
    execute_activate_blacklist_mode,
    execute_deactivate_blacklist_mode
)

logger = get_logger('services.blacklist_service')

@handle_service_errors("Get blacklist")
def get_blacklist(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Gets the current blacklist state from the database and router.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (list_of_device_objects, error_message)
    """
    log_service_operation("get_blacklist", user_id, router_id, session_id)
    
    # Use database as the source of truth
    db_result, db_error = db_get_blacklist(user_id)
    if db_error:
        log_service_operation("get_blacklist", user_id, router_id, session_id, success=False, error=db_error)
        return None, db_error
    
    log_service_operation("get_blacklist", user_id, router_id, session_id, success=True)
    return db_result, None


@handle_service_errors("Add device to blacklist")
def add_device_to_blacklist(user_id: str, router_id: str, session_id: str, ip: str, device_name: str = None, description: str = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Adds a device to the blacklist if it doesn't already exist.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        ip: IP address to add to blacklist
        device_name: Device name/hostname (optional)
        description: Device description (optional)
        
    Returns:
        Tuple of (success_response, error_message)
    """
    if not ip:
        return None, "IP address is required."
    
    if not validate_ip_address(ip):
        return None, "Invalid IP address format."
    
    log_service_operation("add_device_to_blacklist", user_id, router_id, session_id, {"ip": ip})
    
    # Check if device is already blacklisted
    is_blacklisted, check_error = db_is_device_blacklisted(user_id, router_id, ip)
    if check_error:
        log_service_operation("add_device_to_blacklist", user_id, router_id, session_id, {"ip": ip}, success=False, error=check_error)
        return None, check_error
    
    if is_blacklisted:
        error_msg = f"Device {ip} is already blacklisted."
        log_service_operation("add_device_to_blacklist", user_id, router_id, session_id, {"ip": ip}, success=False, error=error_msg)
        return None, error_msg
    
    # Add to database
    db_response, db_error = db_add_device_to_blacklist(user_id, router_id, ip, device_name, description)
    if db_error:
        log_service_operation("add_device_to_blacklist", user_id, router_id, session_id, {"ip": ip}, success=False, error=db_error)
        return None, db_error
    
    # Execute router command
    cmd_response, cmd_error = execute_add_device_to_blacklist(router_id, session_id, ip)
    if cmd_error:
        log_service_operation("add_device_to_blacklist", user_id, router_id, session_id, {"ip": ip}, success=False, error=cmd_error)
        return None, cmd_error
    
    log_service_operation("add_device_to_blacklist", user_id, router_id, session_id, {"ip": ip}, success=True)
    return cmd_response, None


@handle_service_errors("Remove device from blacklist")
def remove_device_from_blacklist(user_id: str, router_id: str, session_id: str, ip: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Removes a device from the blacklist if it exists.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        ip: IP address to remove from blacklist
        
    Returns:
        Tuple of (success_response, error_message)
    """
    if not ip:
        return None, "IP address is required."
    
    if not validate_ip_address(ip):
        return None, "Invalid IP address format."
    
    log_service_operation("remove_device_from_blacklist", user_id, router_id, session_id, {"ip": ip})
    
    # Check if device is blacklisted
    is_blacklisted, check_error = db_is_device_blacklisted(user_id, router_id, ip)    
    if check_error:
        log_service_operation("remove_device_from_blacklist", user_id, router_id, session_id, {"ip": ip}, success=False, error=check_error)
        return None, check_error
    
    if not is_blacklisted:
        error_msg = f"Device {ip} is not blacklisted."
        log_service_operation("remove_device_from_blacklist", user_id, router_id, session_id, {"ip": ip}, success=False, error=error_msg)
        return None, error_msg
    
    # Remove from database
    db_response, db_error = db_remove_device_from_blacklist(user_id, router_id, ip)
    if db_error:
        log_service_operation("remove_device_from_blacklist", user_id, router_id, session_id, {"ip": ip}, success=False, error=db_error)
        return None, db_error
    
    # Check if the removal was successful (db_response is True if removed, False if not found)
    if not db_response:
        error_msg = f"Device {ip} is not blacklisted."
        log_service_operation("remove_device_from_blacklist", user_id, router_id, session_id, {"ip": ip}, success=False, error=error_msg)
        return None, error_msg
    
    # Execute router command
    cmd_response, cmd_error = execute_remove_device_from_blacklist(router_id, session_id, ip)
    if cmd_error:
        log_service_operation("remove_device_from_blacklist", user_id, router_id, session_id, {"ip": ip}, success=False, error=cmd_error)
        return None, cmd_error
    
    log_service_operation("remove_device_from_blacklist", user_id, router_id, session_id, {"ip": ip}, success=True)
    return cmd_response, None


@handle_service_errors("Get blacklist limit rate")
def get_blacklist_limit_rate(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Gets the current blacklist limited rate.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (rate_mbps, error_message)
    """
    log_service_operation("get_blacklist_limit_rate", user_id, router_id, session_id)
    
    db_result, db_error = db_get_blacklist_limit_rate_setting(user_id, router_id)
    if db_error:
        log_service_operation("get_blacklist_limit_rate", user_id, router_id, session_id, success=False, error=db_error)
        return None, db_error
    
    log_service_operation("get_blacklist_limit_rate", user_id, router_id, session_id, success=True)
    return db_result, None


@handle_service_errors("Set blacklist limit rate")
def set_blacklist_limit_rate(user_id: str, router_id: str, session_id: str, rate: int) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Sets the blacklist limited rate.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        rate: Rate limit in Mbps
        
    Returns:
        Tuple of (success_response, error_message)
    """
    if not rate:
        return None, "Rate is required."
    
    if not validate_rate_limit(rate):
        return None, "Invalid rate value. Rate must be between 1 and 1000 Mbps."
    
    log_service_operation("set_blacklist_limit_rate", user_id, router_id, session_id, {"rate": rate})
    
    # Update database
    db_response, db_error = db_set_blacklist_limit_rate(user_id, router_id, rate)
    if db_error:
        log_service_operation("set_blacklist_limit_rate", user_id, router_id, session_id, {"rate": rate}, success=False, error=db_error)
        return None, db_error
    
    # Execute router command
    cmd_response, cmd_error = execute_set_blacklist_rate_limit(router_id, session_id, rate)
    if cmd_error:
        log_service_operation("set_blacklist_limit_rate", user_id, router_id, session_id, {"rate": rate}, success=False, error=cmd_error)
        return None, cmd_error
    
    log_service_operation("set_blacklist_limit_rate", user_id, router_id, session_id, {"rate": rate}, success=True)
    return cmd_response, None


@handle_service_errors("Activate blacklist mode")
def activate_blacklist_mode(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Activates blacklist mode if not already active.
    TODO: Implement logic to check if whitelist mode is activated, and if so, deactivate it before activating blacklist mode.
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (success_response, error_message)
    """
    log_service_operation("activate_blacklist_mode", user_id, router_id, session_id)
    
    # Check current mode status
    is_active, check_error = db_get_blacklist_mode_setting(user_id, router_id)
    if check_error:
        log_service_operation("activate_blacklist_mode", user_id, router_id, session_id, success=False, error=check_error)
        return None, check_error
    
    if is_active:
        error_msg = "Blacklist mode is already active."
        log_service_operation("activate_blacklist_mode", user_id, router_id, session_id, success=False, error=error_msg)
        return None, error_msg
    
    # Activate in database
    db_response, db_error = db_activate_blacklist_mode(user_id, router_id)
    if db_error:
        log_service_operation("activate_blacklist_mode", user_id, router_id, session_id, success=False, error=db_error)
        return None, db_error
    
    # Execute router command
    cmd_response, cmd_error = execute_activate_blacklist_mode(router_id, session_id)
    if cmd_error:
        log_service_operation("activate_blacklist_mode", user_id, router_id, session_id, success=False, error=cmd_error)
        return None, cmd_error
    
    log_service_operation("activate_blacklist_mode", user_id, router_id, session_id, success=True)
    return cmd_response, None


@handle_service_errors("Deactivate blacklist mode")
def deactivate_blacklist_mode(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Deactivates any active mode.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (success_response, error_message)
    """
    log_service_operation("deactivate_blacklist_mode", user_id, router_id, session_id)
    
    # Check current mode status
    is_active, check_error = db_get_blacklist_mode_setting(user_id, router_id)
    if check_error:
        log_service_operation("deactivate_blacklist_mode", user_id, router_id, session_id, success=False, error=check_error)
        return None, check_error
    
    if not is_active:
        error_msg = "Blacklist mode is not active."
        log_service_operation("deactivate_blacklist_mode", user_id, router_id, session_id, success=False, error=error_msg)
        return None, error_msg
    
    # Deactivate in database
    db_response, db_error = db_deactivate_blacklist_mode(user_id, router_id)
    if db_error:
        log_service_operation("deactivate_blacklist_mode", user_id, router_id, session_id, success=False, error=db_error)
        return None, db_error
    
    # Execute router command
    cmd_response, cmd_error = execute_deactivate_blacklist_mode(router_id, session_id)
    if cmd_error:
        log_service_operation("deactivate_blacklist_mode", user_id, router_id, session_id, success=False, error=cmd_error)
        return None, cmd_error
    
    log_service_operation("deactivate_blacklist_mode", user_id, router_id, session_id, success=True)
    return cmd_response, None 