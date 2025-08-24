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
from managers.db_session_context import SessionContext
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
    session = SessionContext.get()
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
            
            session.flush()
            session.refresh(current_device)
            
            # Convert to dict while still in session
            device_dict = current_device.to_dict()
            
            return device_dict, None
            
    except Exception as e:
        logger.error(f"Failed to update device {device_id}: {str(e)}")
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
    session = SessionContext.get()
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
        raise


@handle_db_errors("Delete device")
def delete_device_by_id(user_id: str, router_id: str, device_id: str) -> Union[Tuple[bool, Dict[str, Any]], None, str]:
    """
    Delete a device by ID and cleanup empty groups.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        device_id: Device's UUID
        
    Returns:
        Either (success_boolean, cleanup_context) on success, None on device not found, or error_message string
    """
    from models.device_group import DeviceGroup
    from models.blocked_device import UserBlockedDevice
    from models.bandwidth_rules import BandwidthRules
    from models.content_control_rules import ContentControlRules
    
    session = SessionContext.get()
    try:
            # Find the single group that contains this device
            device_group = session.query(DeviceGroup).options(
                joinedload(DeviceGroup.devices)
            ).filter(
                and_(
                    DeviceGroup.user_id == user_id,
                    DeviceGroup.router_id == router_id
                )
            ).join(UserDevice, DeviceGroup.devices).filter(
                UserDevice.id == device_id
            ).first()
            
            # Check if group will become empty after device deletion
            will_delete_group = device_group and len(device_group.devices) == 1
            
            # Check if device is blocked
            blocked_device = session.query(UserBlockedDevice).filter(
                and_(
                    UserBlockedDevice.user_id == user_id,
                    UserBlockedDevice.router_id == router_id,
                    UserBlockedDevice.device_id == device_id,
                    UserBlockedDevice.is_active.is_(True)
                )
            ).first()
            
            was_blocked = blocked_device is not None
            blocked_device_ip = str(blocked_device.device_ip) if blocked_device else None
            
            # Build cleanup context for the single group
            group_cleanup = None
            if device_group:
                content_rules = session.query(ContentControlRules).filter(
                    and_(
                        ContentControlRules.group_id == device_group.id,
                        ContentControlRules.router_id == router_id,
                        ContentControlRules.is_active.is_(True)
                    )
                ).first()
                
                bandwidth_rules = session.query(BandwidthRules).filter(
                    and_(
                        BandwidthRules.group_id == device_group.id,
                        BandwidthRules.router_id == router_id,
                        BandwidthRules.is_active.is_(True)
                    )
                ).first()
                
                group_cleanup = {
                    'group_id': str(device_group.id),
                    'should_clear_agh': content_rules and content_rules.blocked_categories and len(content_rules.blocked_categories) > 0,
                    'should_clear_bandwidth': bandwidth_rules and (
                        bandwidth_rules.download_limit_mbps is not None or bandwidth_rules.upload_limit_mbps is not None
                    ),
                    'will_be_deleted': will_delete_group
                }
            
            # Get device info before deletion for cleanup
            device = session.query(UserDevice).filter(
                and_(
                    UserDevice.id == device_id,
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id
                )
            ).first()
            
            if not device:
                return "Device not found"
            
            device_ip = str(device.ip) if device.ip else None
            device_mac = str(device.mac) if device.mac else None
            
            # Delete blocked device record if exists
            if blocked_device:
                session.delete(blocked_device)
            
            # Delete the device
            session.delete(device)
            
            # Delete group if it will become empty
            deleted_group_ids = []
            if will_delete_group and device_group:
                deleted_group_ids.append(str(device_group.id))
                session.delete(device_group)
            
            # Build cleanup context
            cleanup_context = {
                'deleted_group_ids': deleted_group_ids,
                'was_blocked': was_blocked,
                'blocked_device_ip': blocked_device_ip,
                'device_ip': device_ip,
                'device_mac': device_mac,
                'group_cleanup': group_cleanup
            }
            
            return (True, cleanup_context)
    except Exception as e:
        logger.error(f"Failed to delete device {device_id}: {str(e)}")
        raise


# Additional DB operations (no commits; use SessionContext)
def get_user_devices_db(user_id: str, router_id: str) -> List[Dict[str, Any]]:
    session = SessionContext.get()
    devices = session.query(UserDevice).filter(
        and_(UserDevice.user_id == user_id, UserDevice.router_id == router_id)
    ).all()
    return [device.to_dict() for device in devices]


def create_or_update_device_db(
    user_id: str,
    router_id: str,
    ip: str,
    mac: Optional[str],
    hostname: Optional[str],
    device_name: Optional[str],
    device_type: Optional[str],
    manufacturer: Optional[str],
) -> Dict[str, Any]:
    session = SessionContext.get()
    existing_device = session.query(UserDevice).filter(
        and_(UserDevice.user_id == user_id, UserDevice.router_id == router_id, UserDevice.ip == ip)
    ).first()

    current_time = datetime.utcnow()
    if existing_device:
        existing_device.last_seen = current_time
        if mac:
            existing_device.mac = mac
        if hostname and not existing_device.device_name:
            existing_device.hostname = hostname
        elif hostname and existing_device.device_name:
            if existing_device.hostname != hostname and existing_device.device_name != existing_device.hostname:
                existing_device.hostname = hostname
        if device_name:
            existing_device.device_name = device_name
        if device_type:
            existing_device.device_type = device_type
        if manufacturer:
            existing_device.manufacturer = manufacturer
        session.flush()
        session.refresh(existing_device)
        return existing_device.to_dict()
    else:
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
            last_seen=current_time,
        )
        session.add(new_device)
        session.flush()
        session.refresh(new_device)
        return new_device.to_dict()


def bulk_create_or_update_devices_db(user_id: str, router_id: str, devices_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    session = SessionContext.get()
    created_devices: List[UserDevice] = []
    current_time = datetime.utcnow()
    for device_data in devices_data:
        ip = device_data.get('ip')
        if not ip:
            continue
        mac = device_data.get('mac')
        hostname = device_data.get('hostname')
        device_type = device_data.get('type') or device_data.get('device_type')

        existing_device = session.query(UserDevice).filter(
            and_(UserDevice.user_id == user_id, UserDevice.router_id == router_id, UserDevice.ip == ip)
        ).first()

        if existing_device:
            existing_device.last_seen = current_time
            if mac:
                existing_device.mac = mac
            if hostname and not existing_device.device_name:
                existing_device.hostname = hostname
            elif hostname and existing_device.device_name:
                if existing_device.hostname != hostname and existing_device.device_name != existing_device.hostname:
                    existing_device.hostname = hostname
            if device_type:
                existing_device.device_type = device_type
            created_devices.append(existing_device)
        else:
            new_device = UserDevice(
                user_id=user_id,
                router_id=router_id,
                ip=ip,
                mac=mac,
                hostname=hostname,
                device_type=device_type,
                first_seen=current_time,
                last_seen=current_time,
            )
            session.add(new_device)
            created_devices.append(new_device)

    session.flush()
    for device in created_devices:
        session.refresh(device)
    return [device.to_dict() for device in created_devices]


def get_devices_by_ips_db(user_id: str, router_id: str, ips: List[str]) -> List[Any]:
    session = SessionContext.get()
    devices = session.query(UserDevice).filter(
        and_(UserDevice.user_id == user_id, UserDevice.router_id == router_id, UserDevice.ip.in_(ips))
    ).all()
    return devices


def validate_devices_db(user_id: str, router_id: str, device_identifiers: List[str]) -> Dict[str, Any]:
    from utils.response_helpers import is_uuid
    session = SessionContext.get()
    valid_devices: List[Dict[str, Any]] = []
    invalid_devices: List[str] = []
    device_objects: List[Any] = []

    for identifier in device_identifiers:
        if is_uuid(identifier):
            device = session.query(UserDevice).filter(
                and_(UserDevice.id == identifier, UserDevice.user_id == user_id, UserDevice.router_id == router_id)
            ).first()
            if device:
                device_objects.append(device)
            else:
                invalid_devices.append(identifier)
        else:
            devices = session.query(UserDevice).filter(
                and_(UserDevice.user_id == user_id, UserDevice.router_id == router_id, UserDevice.ip == identifier)
            ).all()
            if devices:
                device_objects.extend(devices)
            else:
                invalid_devices.append(identifier)

    for device in device_objects:
        try:
            valid_devices.append(device.to_dict())
        except Exception:
            if hasattr(device, 'id'):
                invalid_devices.append(str(device.id))
            elif hasattr(device, 'ip'):
                invalid_devices.append(str(device.ip))

    return {
        'valid_devices': valid_devices,
        'invalid_devices': invalid_devices,
        'total_valid': len(valid_devices),
        'total_invalid': len(invalid_devices),
    }
