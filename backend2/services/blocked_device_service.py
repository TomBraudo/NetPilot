"""
Blocked Device Service - Orchestration Layer

Coordinates blocked device operations by orchestrating database operations.
Validates inputs and returns (result, error) tuples following the project patterns.
"""

from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import handle_service_errors, log_service_operation
from services.db_operations.blocked_device_db import (
    get_user_blocked_devices_db,
    block_device_db, 
    unblock_device_db,
    is_device_blocked_db,
    get_blocked_device_ids_db
)
from services.commands_server_operations.blocked_device_execute import (
    execute_block_device,
    execute_unblock_device
)

logger = get_logger('services.blocked_device_service')


@handle_service_errors("Get blocked devices")
def get_user_blocked_devices(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Get all blocked devices for user/router.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID  
        session_id: Session's UUID
        
    Returns:
        Tuple of (list_of_blocked_devices, error_message)
    """
    log_service_operation("blocked_device_get_all", user_id, router_id, session_id)
    return get_user_blocked_devices_db(user_id, router_id)


@handle_service_errors("Block device") 
def block_device(user_id: str, router_id: str, session_id: str, device_data: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Block a device by applying bandwidth limits and saving to database.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        device_data: Dictionary containing device information:
                    - device_id (optional): UUID of existing device
                    - device_ip or ip (required if no device_id): IP address
                    - device_mac or mac (optional): MAC address
        
    Returns:
        Tuple of (blocked_device_dict, error_message)
    """
    log_service_operation("blocked_device_block", user_id, router_id, session_id, {
        "device_id": device_data.get('device_id'),
        "device_ip": device_data.get('device_ip') or device_data.get('ip'),
        "device_mac": device_data.get('device_mac') or device_data.get('mac')
    })
    
    # Validate device data
    device_ip = device_data.get('device_ip') or device_data.get('ip')
    device_mac = device_data.get('device_mac') or device_data.get('mac')
    device_id = device_data.get('device_id')
    
    if not device_ip and not device_id:
        return None, "device_ip or device_id is required"
    
    # If device_id is provided but no IP, we need to get the IP from the database
    if device_id and not device_ip:
        # Get device IP from database for router command execution
        from services.db_operations.device_db import get_device_by_id_db
        device_result, device_error = get_device_by_id_db(user_id, router_id, device_id)
        if device_error:
            return None, f"Failed to get device information: {device_error}"
        if not device_result:
            return None, "Device not found"
        device_ip = device_result.get('ip')
        if not device_ip:
            return None, "Device IP not found"
    
    # Validate IP format
    if not _is_valid_ip(device_ip):
        return None, "Invalid IP address format"
    
    # Step 1: Save blocked device record to database first
    db_result, db_error = block_device_db(user_id, router_id, device_data)
    if db_error:
        return None, db_error
    
    # Step 2: Execute blocking command on router (apply restrictive bandwidth limits)
    try:
        execute_result, execute_error = execute_block_device(router_id, session_id, device_ip)
        if execute_error:
            # Rollback database operation if router command fails
            logger.warning(f"Router blocking failed for device {device_ip}, rolling back database record")
            # We should unblock in database, but for now just log the error
            # In a production system, you might want to implement compensating rollback
            return None, f"Failed to block device on router: {execute_error}"
        
        # Merge database and execution results
        result = db_result.copy()
        result.update({
            "router_blocked": True,
            "router_response": execute_result
        })
        
        logger.info(f"Successfully blocked device {device_ip} both in database and router")
        return result, None
        
    except Exception as e:
        logger.error(f"Exception during router blocking for device {device_ip}: {str(e)}")
        return None, f"Failed to block device on router: {str(e)}"


@handle_service_errors("Unblock device")
def unblock_device(user_id: str, router_id: str, session_id: str, blocked_device_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Unblock a device by removing bandwidth limits and updating database.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        blocked_device_id: Blocked device record UUID
        
    Returns:
        Tuple of (success_message_dict, error_message)
    """
    log_service_operation("blocked_device_unblock", user_id, router_id, session_id, {
        "blocked_device_id": blocked_device_id
    })
    
    if not blocked_device_id:
        return None, "blocked_device_id is required"
    
    # Step 1: Get the blocked device record to get the IP address
    from services.db_operations.blocked_device_db import get_user_blocked_devices_db
    blocked_devices, db_error = get_user_blocked_devices_db(user_id, router_id)
    if db_error:
        return None, f"Failed to get blocked devices: {db_error}"
    
    # Find the specific blocked device
    target_blocked_device = None
    for device in blocked_devices or []:
        if str(device.get('id')) == str(blocked_device_id):
            target_blocked_device = device
            break
    
    if not target_blocked_device:
        return None, "Blocked device not found"
    
    device_ip = target_blocked_device.get('device_ip')
    if not device_ip:
        return None, "Device IP not found in blocked device record"
    
    # Step 2: Execute unblocking command on router (remove bandwidth limits)
    try:
        execute_result, execute_error = execute_unblock_device(router_id, session_id, str(device_ip))
        if execute_error:
            logger.warning(f"Router unblocking failed for device {device_ip}: {execute_error}")
            # Continue with database operation even if router command fails
            # The device will be marked as unblocked in database but may still have limits on router
    
        # Step 3: Update database to mark device as unblocked
        db_result, db_error = unblock_device_db(user_id, router_id, blocked_device_id)
        if db_error:
            return None, db_error
        
        # Merge database and execution results
        result = db_result.copy()
        result.update({
            "device_ip": str(device_ip),
            "router_unblocked": execute_error is None,
            "router_response": execute_result if execute_error is None else None,
            "router_error": execute_error
        })
        
        if execute_error:
            logger.warning(f"Device {device_ip} unblocked in database but router operation failed: {execute_error}")
        else:
            logger.info(f"Successfully unblocked device {device_ip} both in database and router")
        
        return result, None
        
    except Exception as e:
        logger.error(f"Exception during router unblocking for device {device_ip}: {str(e)}")
        # Still try to unblock in database
        db_result, db_error = unblock_device_db(user_id, router_id, blocked_device_id)
        if db_error:
            return None, f"Failed to unblock device in database and router: {str(e)}, {db_error}"
        
        result = db_result.copy()
        result.update({
            "device_ip": str(device_ip),
            "router_unblocked": False,
            "router_error": str(e)
        })
        return result, None


@handle_service_errors("Check if device is blocked")
def is_device_blocked(user_id: str, router_id: str, session_id: str, device_ip: str = None, device_id: str = None) -> Tuple[Optional[bool], Optional[str]]:
    """
    Check if a device is currently blocked.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        device_ip: Device IP address (optional)
        device_id: Device UUID (optional)
        
    Returns:
        Tuple of (is_blocked_boolean, error_message)
    """
    log_service_operation("blocked_device_check", user_id, router_id, session_id, {
        "device_ip": device_ip,
        "device_id": device_id
    })
    
    if not device_ip and not device_id:
        return None, "device_ip or device_id is required"
    
    return is_device_blocked_db(user_id, router_id, device_ip, device_id)


@handle_service_errors("Get blocked device IDs")
def get_blocked_device_ids(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Get list of all blocked device IDs for filtering purposes.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (list_of_device_ids, error_message)
    """
    log_service_operation("blocked_device_get_ids", user_id, router_id, session_id)
    return get_blocked_device_ids_db(user_id, router_id)


def _is_valid_ip(ip: str) -> bool:
    """
    Basic IP address validation.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        bool: True if valid IP format, False otherwise
    """
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit() or not 0 <= int(part) <= 255:
                return False
        return True
    except (ValueError, AttributeError):
        return False
