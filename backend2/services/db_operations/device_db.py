"""
Device Database Operations Service

This service handles all database operations for device functionality.
It provides data validation, state checking, and CRUD operations for device-related data.
All functions return (result, error) tuple format.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from utils.logging_config import get_logger
from .base import handle_db_errors
from models.device import UserDevice
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

logger = get_logger('services.db_operations.device_db')


@handle_db_errors("Update device")
def update_device_fields(user_id: str, router_id: str, device_id: str, update_data: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Update specific fields of a device.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        device_id: Device's UUID
        update_data: Dictionary containing fields to update:
                    {"hostname": "new_hostname", "device_name": "new_name", ...}
        
    Returns:
        Tuple of (updated_device_dict, error_message)
    """
    from database.session import get_db_session
    
    with get_db_session() as session:
        try:
            # Get the device in the current session context
            current_device = session.query(UserDevice).filter(
                and_(
                    UserDevice.id == device_id,
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id
                )
            ).first()
            
            if not current_device:
                return None, "Device not found"
            
            # Update the fields
            if 'hostname' in update_data:
                current_device.hostname = update_data['hostname'].strip() if update_data['hostname'] else None
            if 'device_name' in update_data:
                current_device.device_name = update_data['device_name'].strip() if update_data['device_name'] else None
            if 'device_type' in update_data or 'type' in update_data:
                device_type = update_data.get('device_type') or update_data.get('type', '')
                current_device.device_type = device_type.strip() if device_type else None
            if 'manufacturer' in update_data:
                current_device.manufacturer = update_data['manufacturer'].strip() if update_data['manufacturer'] else None
            
            session.commit()
            session.refresh(current_device)
            
            # Convert to dict while still in session
            device_dict = current_device.to_dict()
            
            return device_dict, None
            
        except Exception as e:
            logger.error(f"Failed to update device {device_id}: {str(e)}")
            session.rollback()
            raise


@handle_db_errors("Get device by ID")
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
    from database.session import get_db_session
    
    with get_db_session() as session:
        try:
            device = session.query(UserDevice).filter(
                and_(
                    UserDevice.id == device_id,
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id
                )
            ).first()
            
            if not device:
                return None, "Device not found"
            
            # Convert to dict while still in session
            device_dict = device.to_dict()
            
            return device_dict, None
            
        except Exception as e:
            logger.error(f"Failed to get device {device_id}: {str(e)}")
            session.rollback()
            raise


@handle_db_errors("Delete device")
def delete_device_by_id(user_id: str, router_id: str, device_id: str) -> Union[Tuple[bool, List[str]], None, str]:
    """
    Delete a device by ID and cleanup empty groups.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        device_id: Device's UUID
        
    Returns:
        Either (success_boolean, deleted_group_ids) on success, None on device not found, or error_message string
    """
    from database.session import get_db_session
    from models.device_group import DeviceGroup
    
    with get_db_session() as session:
        try:
            # First, find all groups that contain this device and check their device counts
            groups_with_device = session.query(DeviceGroup).options(
                joinedload(DeviceGroup.devices)
            ).filter(
                and_(
                    DeviceGroup.user_id == user_id,
                    DeviceGroup.router_id == router_id
                )
            ).all()
            
            affected_groups = []
            for group in groups_with_device:
                if any(str(device.id) == str(device_id) for device in group.devices):
                    affected_groups.append(group)
            
            # Check which groups will become empty after device deletion
            groups_to_delete = []
            for group in affected_groups:
                if len(group.devices) == 1:  # This group will become empty
                    groups_to_delete.append(group)
            
            # Delete the device
            device = session.query(UserDevice).filter(
                and_(
                    UserDevice.id == device_id,
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id
                )
            ).first()
            
            if not device:
                return "Device not found"
            
            session.delete(device)
            
            # Delete groups that will become empty
            deleted_group_ids = []
            for group in groups_to_delete:
                deleted_group_ids.append(str(group.id))
                session.delete(group)
            
            session.commit()
            
            return (True, deleted_group_ids)
            
        except Exception as e:
            logger.error(f"Failed to delete device {device_id}: {str(e)}")
            session.rollback()
            raise
