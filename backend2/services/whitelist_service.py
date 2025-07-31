"""
Whitelist Service - Main Orchestration Layer

This service acts as the conductor for whitelist operations, coordinating between
database operations and router command executions. It follows the 3-layer architecture:
1. This service (orchestration) - calls db + commands
2. services/db_operations/whitelist_db.py - Database operations  
3. services/commands_server_operations/whitelist_execute.py - Router command execution
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
from services.db_operations.whitelist_db import (
    get_whitelist as db_get_whitelist,
    add_device_to_whitelist as db_add_device_to_whitelist,
    remove_device_from_whitelist as db_remove_device_from_whitelist,
    is_device_whitelisted as db_is_device_whitelisted,
    get_whitelist_mode_setting as db_get_whitelist_mode_setting,
    activate_whitelist_mode as db_activate_whitelist_mode,
    deactivate_whitelist_mode as db_deactivate_whitelist_mode,
    get_whitelist_limit_rate_setting as db_get_whitelist_limit_rate_setting,
    set_whitelist_limit_rate as db_set_whitelist_limit_rate
)

# Router command execution imports
from services.commands_server_operations.whitelist_execute import (
    execute_get_whitelist,
    execute_add_device_to_whitelist,
    execute_remove_device_from_whitelist,
    execute_set_whitelist_rate_limit,
    execute_activate_whitelist_mode,
    execute_deactivate_whitelist_mode
)

logger = get_logger('services.whitelist_service')

@handle_service_errors("Get whitelist")
def get_whitelist(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Gets the current whitelist state from the database and router.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (list_of_device_objects, error_message)
    """
    log_service_operation("get_whitelist", user_id, router_id, session_id)
    
    # Use database as the source of truth
    db_result, db_error = db_get_whitelist(user_id)
    if db_error:
        log_service_operation("get_whitelist", user_id, router_id, session_id, success=False, error=db_error)
        return None, db_error
    
    log_service_operation("get_whitelist", user_id, router_id, session_id, success=True)
    return db_result, None


@handle_service_errors("Add device to whitelist")
def add_device_to_whitelist(user_id: str, router_id: str, session_id: str, ip: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Adds a device to the whitelist if it's not already there.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        ip: IP address to add to whitelist
        
    Returns:
        Tuple of (success_response, error_message)
    """
    if not ip:
        return None, "IP address is required."
    
    if not validate_ip_address(ip):
        return None, "Invalid IP address format."
    
    log_service_operation("add_device_to_whitelist", user_id, router_id, session_id, {"ip": ip})
    
    # Check if device is already whitelisted
    is_whitelisted, check_error = db_is_device_whitelisted(user_id, router_id, ip)
    if check_error:
        log_service_operation("add_device_to_whitelist", user_id, router_id, session_id, {"ip": ip}, success=False, error=check_error)
        return None, check_error
    
    if is_whitelisted:
        error_msg = f"Device {ip} is already whitelisted."
        log_service_operation("add_device_to_whitelist", user_id, router_id, session_id, {"ip": ip}, success=False, error=error_msg)
        return None, error_msg
    
    # Add to database
    db_response, db_error = db_add_device_to_whitelist(user_id, router_id, ip)
    if db_error:
        log_service_operation("add_device_to_whitelist", user_id, router_id, session_id, {"ip": ip}, success=False, error=db_error)
        return None, db_error
    
    # Execute router command
    cmd_response, cmd_error = execute_add_device_to_whitelist(router_id, session_id, ip)
    if cmd_error:
        log_service_operation("add_device_to_whitelist", user_id, router_id, session_id, {"ip": ip}, success=False, error=cmd_error)
        return None, cmd_error
    
    log_service_operation("add_device_to_whitelist", user_id, router_id, session_id, {"ip": ip}, success=True)
    return cmd_response, None


@handle_service_errors("Remove device from whitelist")
def remove_device_from_whitelist(user_id: str, router_id: str, session_id: str, ip: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Removes a device from the whitelist if it exists.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        ip: IP address to remove from whitelist
        
    Returns:
        Tuple of (success_response, error_message)
    """
    if not ip:
        return None, "IP address is required."
    
    if not validate_ip_address(ip):
        return None, "Invalid IP address format."
    
    log_service_operation("remove_device_from_whitelist", user_id, router_id, session_id, {"ip": ip})
    
    # Check if device is whitelisted
    is_whitelisted, check_error = db_is_device_whitelisted(user_id, router_id, ip)    
    if check_error:
        log_service_operation("remove_device_from_whitelist", user_id, router_id, session_id, {"ip": ip}, success=False, error=check_error)
        return None, check_error
    
    if not is_whitelisted:
        error_msg = f"Device {ip} is not whitelisted."
        log_service_operation("remove_device_from_whitelist", user_id, router_id, session_id, {"ip": ip}, success=False, error=error_msg)
        return None, error_msg
    
    # Remove from database
    db_response, db_error = db_remove_device_from_whitelist(user_id, router_id, ip)
    if db_error:
        log_service_operation("remove_device_from_whitelist", user_id, router_id, session_id, {"ip": ip}, success=False, error=db_error)
        return None, db_error
    
    # Check if the removal was successful (db_response is True if removed, False if not found)
    if not db_response:
        error_msg = f"Device {ip} is not whitelisted."
        log_service_operation("remove_device_from_whitelist", user_id, router_id, session_id, {"ip": ip}, success=False, error=error_msg)
        return None, error_msg
    
    # Execute router command
    cmd_response, cmd_error = execute_remove_device_from_whitelist(router_id, session_id, ip)
    if cmd_error:
        log_service_operation("remove_device_from_whitelist", user_id, router_id, session_id, {"ip": ip}, success=False, error=cmd_error)
        return None, cmd_error
    
    log_service_operation("remove_device_from_whitelist", user_id, router_id, session_id, {"ip": ip}, success=True)
    return cmd_response, None


@handle_service_errors("Get whitelist limit rate")
def get_whitelist_limit_rate(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Gets the current whitelist limited rate.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (rate_mbps, error_message)
    """
    log_service_operation("get_whitelist_limit_rate", user_id, router_id, session_id)
    
    db_result, db_error = db_get_whitelist_limit_rate_setting(user_id, router_id)
    if db_error:
        log_service_operation("get_whitelist_limit_rate", user_id, router_id, session_id, success=False, error=db_error)
        return None, db_error
    
    log_service_operation("get_whitelist_limit_rate", user_id, router_id, session_id, success=True)
    return db_result, None


@handle_service_errors("Set whitelist limit rate")
def set_whitelist_limit_rate(user_id: str, router_id: str, session_id: str, rate: int) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Sets the whitelist limited rate.
    
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
    
    log_service_operation("set_whitelist_limit_rate", user_id, router_id, session_id, {"rate": rate})
    
    # Update database
    db_response, db_error = db_set_whitelist_limit_rate(user_id, router_id, rate)
    if db_error:
        log_service_operation("set_whitelist_limit_rate", user_id, router_id, session_id, {"rate": rate}, success=False, error=db_error)
        return None, db_error
    
    # Execute router command
    cmd_response, cmd_error = execute_set_whitelist_rate_limit(router_id, session_id, rate)
    if cmd_error:
        log_service_operation("set_whitelist_limit_rate", user_id, router_id, session_id, {"rate": rate}, success=False, error=cmd_error)
        return None, cmd_error
    
    log_service_operation("set_whitelist_limit_rate", user_id, router_id, session_id, {"rate": rate}, success=True)
    return cmd_response, None


@handle_service_errors("Activate whitelist mode")
def activate_whitelist_mode(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Activates whitelist mode if not already active.
    TODO: Implement logic to check if blacklist mode is activated, and if so, deactivate it before activating whitelist mode.
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (success_response, error_message)
    """
    log_service_operation("activate_whitelist_mode", user_id, router_id, session_id)
    
    # Check current mode status
    is_active, check_error = db_get_whitelist_mode_setting(user_id, router_id)
    if check_error:
        log_service_operation("activate_whitelist_mode", user_id, router_id, session_id, success=False, error=check_error)
        return None, check_error
    
    if is_active:
        error_msg = "Whitelist mode is already active."
        log_service_operation("activate_whitelist_mode", user_id, router_id, session_id, success=False, error=error_msg)
        return None, error_msg
    
    # Activate in database
    db_response, db_error = db_activate_whitelist_mode(user_id, router_id)
    if db_error:
        log_service_operation("activate_whitelist_mode", user_id, router_id, session_id, success=False, error=db_error)
        return None, db_error
    
    # Execute router command
    cmd_response, cmd_error = execute_activate_whitelist_mode(router_id, session_id)
    if cmd_error:
        log_service_operation("activate_whitelist_mode", user_id, router_id, session_id, success=False, error=cmd_error)
        return None, cmd_error
    
    log_service_operation("activate_whitelist_mode", user_id, router_id, session_id, success=True)
    return cmd_response, None


@handle_service_errors("Deactivate whitelist mode")
def deactivate_whitelist_mode(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Deactivates any active mode.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (success_response, error_message)
    """
    log_service_operation("deactivate_whitelist_mode", user_id, router_id, session_id)
    
    # Check current mode status
    is_active, check_error = db_get_whitelist_mode_setting(user_id, router_id)
    if check_error:
        log_service_operation("deactivate_whitelist_mode", user_id, router_id, session_id, success=False, error=check_error)
        return None, check_error
    
    if not is_active:
        error_msg = "Whitelist mode is not active."
        log_service_operation("deactivate_whitelist_mode", user_id, router_id, session_id, success=False, error=error_msg)
        return None, error_msg
    
    # Deactivate in database
    db_response, db_error = db_deactivate_whitelist_mode(user_id, router_id)
    if db_error:
        log_service_operation("deactivate_whitelist_mode", user_id, router_id, session_id, success=False, error=db_error)
        return None, db_error
    
    # Execute router command
    cmd_response, cmd_error = execute_deactivate_whitelist_mode(router_id, session_id)
    if cmd_error:
        log_service_operation("deactivate_whitelist_mode", user_id, router_id, session_id, success=False, error=cmd_error)
        return None, cmd_error
    
    log_service_operation("deactivate_whitelist_mode", user_id, router_id, session_id, success=True)
    return cmd_response, None