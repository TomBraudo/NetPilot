from utils.logging_config import get_logger
from typing import Dict, Tuple, Optional, Union, List

# Database operations imports
from services.db_operations.device_db import (
    update_device_fields as db_update_device_fields,
    get_device_by_id as db_get_device_by_id,
    delete_device_by_id as db_delete_device_by_id
)

# Base service imports
from .base import (
    handle_service_errors
)

"""
Device Service

This service handles all device-related operations including:
- Creating and updating devices from network scans
- Preserving user-customized device names during updates
- Managing device metadata and relationships

IMPORTANT: When updating devices from network scans, this service preserves
manually edited device names (device_name field) to prevent users from losing
their customizations. The hostname field is only updated if:
1. No custom device_name is set, OR
2. The custom device_name is different from the current hostname
"""

logger = get_logger('services.device_service')


def get_user_devices(user_id, router_id):
    """Get all devices for a user and router"""
    from services.db_operations.device_db import get_user_devices_db
    return get_user_devices_db(user_id, router_id)


def create_or_update_device(user_id, router_id, ip, mac=None, hostname=None, device_name=None, device_type=None, manufacturer=None):
    """Create a new device or update existing one"""
    from services.db_operations.device_db import create_or_update_device_db
    return create_or_update_device_db(user_id, router_id, ip, mac, hostname, device_name, device_type, manufacturer)


def bulk_create_or_update_devices(user_id, router_id, devices_data):
    """Create or update multiple devices from scan data"""
    from services.db_operations.device_db import bulk_create_or_update_devices_db
    return bulk_create_or_update_devices_db(user_id, router_id, devices_data)


@handle_service_errors("Update device")
def update_device(user_id: str, router_id: str, device_id: str, update_data: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Update a device's fields.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        device_id: Device's UUID
        update_data: Dictionary containing fields to update
        
    Returns:
        Tuple of (updated_device_dict, error_message)
    """
    # Execute database operation to update device
    result, error = db_update_device_fields(user_id, router_id, device_id, update_data)
    if error:
        return None, error
    
    return result, None


@handle_service_errors("Get device by ID")
def get_device_by_id(user_id: str, router_id: str, device_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Get a specific device by ID.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        device_id: Device's UUID
        
    Returns:
        Tuple of (device_dict, error_message)
    """
    # Execute database operation to get device
    result, error = db_get_device_by_id(user_id, router_id, device_id)
    if error:
        return None, error
    
    return result, None


@handle_service_errors("Delete device")
def delete_device(user_id: str, router_id: str, device_id: str) -> Union[Tuple[bool, List[str]], None, str]:
    """
    Delete a device by ID and cleanup empty groups.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        device_id: Device's UUID
        
    Returns:
        Either (success_boolean, deleted_group_ids) on success, None on device not found, or error_message string
    """
    # Execute database operation to delete device and cleanup empty groups
    result = db_delete_device_by_id(user_id, router_id, device_id)
    
    # Handle different return types from database operation
    if result is None:
        return "Device not found"
    elif isinstance(result, str):
        # Error message
        return result
    elif isinstance(result, tuple) and len(result) == 2:
        # Success: (success, deleted_group_ids)
        success, deleted_group_ids = result
        if success:
            return result
    
    # Fallback
    return "Unknown error occurred during device deletion"


def get_devices_by_ips(user_id, router_id, ips):
    """Get devices by their IP addresses"""
    from services.db_operations.device_db import get_devices_by_ips_db
    return get_devices_by_ips_db(user_id, router_id, ips)


def validate_devices(user_id, router_id, device_identifiers):
    """Validate that devices exist in database by IP or UUID"""
    from services.db_operations.device_db import validate_devices_db
    return validate_devices_db(user_id, router_id, device_identifiers)
