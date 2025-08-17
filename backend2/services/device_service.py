from database.session import get_db_session
from models.device import UserDevice
from models.user import User
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, func
from utils.logging_config import get_logger
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

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
    with get_db_session() as session:
        try:
            devices = session.query(UserDevice).filter(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id
                )
            ).all()
            
            # Convert to dict while still in session to avoid detachment issues
            devices_dicts = [device.to_dict() for device in devices]
            
            logger.info(f"Retrieved {len(devices)} devices for user {user_id}, router {router_id}")
            return devices_dicts
            
        except Exception as e:
            logger.error(f"Failed to get devices: {str(e)}")
            session.rollback()
            raise


def create_or_update_device(user_id, router_id, ip, mac=None, hostname=None, device_name=None, device_type=None, manufacturer=None):
    """Create a new device or update existing one"""
    with get_db_session() as session:
        try:
            # Check if device already exists by IP
            existing_device = session.query(UserDevice).filter(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id,
                    UserDevice.ip == ip
                )
            ).first()
            
            current_time = datetime.utcnow()
            
            if existing_device:
                # Update existing device
                existing_device.last_seen = current_time
                if mac:
                    existing_device.mac = mac
                                    # Only update hostname if device_name is not manually set
                    # This preserves user's custom device names
                    if hostname and not existing_device.device_name:
                        existing_device.hostname = hostname
                        logger.debug(f"Updated hostname for device {ip} to {hostname}")
                    elif hostname and existing_device.device_name:
                        # If user has set a custom name, only update hostname if it's different
                        # and the custom name is not the same as the current hostname
                        if existing_device.hostname != hostname and existing_device.device_name != existing_device.hostname:
                            existing_device.hostname = hostname
                            logger.debug(f"Updated hostname for device {ip} to {hostname} (preserving custom name: {existing_device.device_name})")
                        else:
                            logger.debug(f"Preserved custom device name '{existing_device.device_name}' for device {ip} (scan hostname: {hostname})")
                if device_name:
                    existing_device.device_name = device_name
                if device_type:
                    existing_device.device_type = device_type
                if manufacturer:
                    existing_device.manufacturer = manufacturer
                
                session.commit()
                session.refresh(existing_device)
                
                # Convert to dict while still in session
                device_dict = existing_device.to_dict()
                session.expunge(existing_device)
                
                logger.info(f"Updated existing device {ip} for user {user_id}")
                return device_dict
            else:
                # Create new device
                new_device = UserDevice(
                    user_id=user_id,
                    router_id=router_id,
                    ip=ip,
                    mac=mac,
                    hostname=hostname,
                    device_name=device_name,
                    device_type=device_type,
                    manufacturer=manufacturer,
                    first_seen=current_time,
                    last_seen=current_time
                )
                
                session.add(new_device)
                session.commit()
                session.refresh(new_device)
                
                # Convert to dict while still in session
                device_dict = new_device.to_dict()
                session.expunge(new_device)
                
                logger.info(f"Created new device {ip} for user {user_id}")
                return device_dict
            
        except Exception as e:
            logger.error(f"Failed to create/update device: {str(e)}")
            session.rollback()
            raise


def bulk_create_or_update_devices(user_id, router_id, devices_data):
    """Create or update multiple devices from scan data"""
    with get_db_session() as session:
        try:
            created_devices = []
            current_time = datetime.utcnow()
            
            for device_data in devices_data:
                ip = device_data.get('ip')
                if not ip:
                    continue
                    
                mac = device_data.get('mac')
                hostname = device_data.get('hostname')
                device_type = device_data.get('type') or device_data.get('device_type')
                
                # Check if device already exists
                existing_device = session.query(UserDevice).filter(
                    and_(
                        UserDevice.user_id == user_id,
                        UserDevice.router_id == router_id,
                        UserDevice.ip == ip
                    )
                ).first()
                
                if existing_device:
                    # Update existing device
                    existing_device.last_seen = current_time
                    if mac:
                        existing_device.mac = mac
                    
                    # Only update hostname if device_name is not manually set
                    # This preserves user's custom device names
                    if hostname and not existing_device.device_name:
                        existing_device.hostname = hostname
                        logger.debug(f"Updated hostname for device {ip} to {hostname}")
                    elif hostname and existing_device.device_name:
                        # If user has set a custom name, only update hostname if it's different
                        # and the custom name is not the same as the current hostname
                        if existing_device.hostname != hostname and existing_device.device_name != existing_device.hostname:
                            existing_device.hostname = hostname
                            logger.debug(f"Updated hostname for device {ip} to {hostname} (preserving custom name: {existing_device.device_name})")
                        else:
                            logger.debug(f"Preserved custom device name '{existing_device.device_name}' for device {ip} (scan hostname: {hostname})")
                    
                    if device_type:
                        existing_device.device_type = device_type
                    
                    created_devices.append(existing_device)
                else:
                    # Create new device
                    new_device = UserDevice(
                        user_id=user_id,
                        router_id=router_id,
                        ip=ip,
                        mac=mac,
                        hostname=hostname,
                        device_type=device_type,
                        first_seen=current_time,
                        last_seen=current_time
                    )
                    
                    session.add(new_device)
                    created_devices.append(new_device)
            
            session.commit()
            
            # Refresh all devices to get their IDs while session is still active
            for device in created_devices:
                session.refresh(device)
            
            # Convert to dicts while still in session to avoid detachment issues
            devices_dicts = [device.to_dict() for device in created_devices]
            
            logger.info(f"Bulk created/updated {len(created_devices)} devices for user {user_id}")
            return devices_dicts
            
        except Exception as e:
            logger.error(f"Failed to bulk create/update devices: {str(e)}")
            session.rollback()
            raise


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
    with get_db_session() as session:
        try:
            devices = session.query(UserDevice).filter(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id,
                    UserDevice.ip.in_(ips)
                )
            ).all()
            
            return devices
            
        except Exception as e:
            logger.error(f"Failed to get devices by IPs: {str(e)}")
            session.rollback()
            raise


def validate_devices(user_id, router_id, device_identifiers):
    """Validate that devices exist in database by IP or UUID"""
    with get_db_session() as session:
        try:
            from utils.response_helpers import is_uuid
            
            logger.info(f"Starting device validation for {len(device_identifiers)} identifiers")
            
            valid_devices = []
            invalid_devices = []
            
            # Process all identifiers first, collecting device objects
            device_objects = []
            
            for identifier in device_identifiers:
                logger.info(f"Processing identifier: {identifier}")
                
                if is_uuid(identifier):
                    # Check by UUID
                    device = session.query(UserDevice).filter(
                        and_(
                            UserDevice.id == identifier,
                            UserDevice.user_id == user_id,
                            UserDevice.router_id == router_id
                        )
                    ).first()
                    
                    if device:
                        logger.info(f"Found device by UUID: {device.id}")
                        device_objects.append(device)
                    else:
                        logger.info(f"No device found for UUID: {identifier}")
                        invalid_devices.append(identifier)
                else:
                    # Check by IP
                    devices = session.query(UserDevice).filter(
                        and_(
                            UserDevice.user_id == user_id,
                            UserDevice.router_id == router_id,
                            UserDevice.ip == identifier
                        )
                    ).all()
                    
                    if devices:
                        logger.info(f"Found {len(devices)} devices by IP: {identifier}")
                        device_objects.extend(devices)
                    else:
                        logger.info(f"No devices found for IP: {identifier}")
                        invalid_devices.append(identifier)
            
            # Convert all device objects to dictionaries while still in session
            for device in device_objects:
                try:
                    device_dict = device.to_dict()
                    valid_devices.append(device_dict)
                    logger.info(f"Successfully converted device {device.id} to dict")
                except Exception as e:
                    logger.error(f"Failed to convert device {device.id} to dict: {e}")
                    # If conversion fails, mark as invalid
                    if hasattr(device, 'id'):
                        invalid_devices.append(device.id)
                    elif hasattr(device, 'ip'):
                        invalid_devices.append(device.ip)
            
            logger.info(f"Device validation complete: {len(valid_devices)} valid, {len(invalid_devices)} invalid")
            
            return {
                'valid_devices': valid_devices,
                'invalid_devices': invalid_devices,
                'total_valid': len(valid_devices),
                'total_invalid': len(invalid_devices)
            }
            
        except Exception as e:
            logger.error(f"Failed to validate devices: {str(e)}")
            session.rollback()
            raise
