"""
Blocked Device Database Operations Service

This service handles all database operations for blocked device functionality.
It provides data validation, state checking, and CRUD operations for blocked device data.
All functions return (result, error) tuple format.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from utils.logging_config import get_logger
from .base import handle_db_errors
from managers.db_session_context import SessionContext
from models.blocked_device import UserBlockedDevice
from models.device import UserDevice
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload

logger = get_logger('services.db_operations.blocked_device_db')


@handle_db_errors("Get blocked devices")
def get_user_blocked_devices_db(user_id: str, router_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Get all active blocked devices for user/router.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        
    Returns:
        Tuple of (list_of_blocked_devices, error_message)
    """
    session = SessionContext.get()
    
    try:
        blocked_devices = session.query(UserBlockedDevice).options(
            joinedload(UserBlockedDevice.device)
        ).filter(
            and_(
                UserBlockedDevice.user_id == user_id,
                UserBlockedDevice.router_id == router_id, 
                UserBlockedDevice.is_active == True
            )
        ).all()
        
        result = []
        for blocked_device in blocked_devices:
            blocked_dict = blocked_device.to_dict()
            # Add device information if available
            if blocked_device.device:
                blocked_dict['device_info'] = {
                    'hostname': blocked_device.device.hostname,
                    'device_name': blocked_device.device.device_name,
                    'device_type': blocked_device.device.device_type,
                    'manufacturer': blocked_device.device.manufacturer
                }
            result.append(blocked_dict)
        
        logger.info(f"Retrieved {len(result)} blocked devices for user {user_id}, router {router_id}")
        return result, None
        
    except Exception as e:
        logger.error(f"Failed to get blocked devices: {str(e)}")
        return None, f"Failed to get blocked devices: {str(e)}"


@handle_db_errors("Block device")
def block_device_db(user_id: str, router_id: str, device_data: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Create blocked device record.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        device_data: Dictionary containing device information:
                    - device_id (optional): UUID of existing device
                    - device_ip (required if no device_id): IP address
                    - device_mac (optional): MAC address
                    - ip (alias for device_ip)
                    - mac (alias for device_mac)
        
    Returns:
        Tuple of (blocked_device_dict, error_message)
    """
    session = SessionContext.get()
    
    try:
        # Extract and validate device identifiers
        device_id = device_data.get('device_id')
        device_ip = device_data.get('device_ip') or device_data.get('ip')
        device_mac = device_data.get('device_mac') or device_data.get('mac')
        
        if not device_ip and not device_id:
            return None, "device_ip or device_id is required"
        
        # If device_id provided, verify it exists and get IP/MAC
        if device_id:
            existing_device = session.query(UserDevice).filter(
                and_(
                    UserDevice.id == device_id,
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id
                )
            ).first()
            
            if not existing_device:
                return None, "Device not found"
            
            device_ip = str(existing_device.ip)
            device_mac = str(existing_device.mac) if existing_device.mac else None
        
        # Check if device is already blocked
        existing_blocked = session.query(UserBlockedDevice).filter(
            and_(
                UserBlockedDevice.user_id == user_id,
                UserBlockedDevice.router_id == router_id,
                UserBlockedDevice.is_active == True,
                or_(
                    UserBlockedDevice.device_id == device_id if device_id else False,
                    UserBlockedDevice.device_ip == device_ip if device_ip else False
                )
            )
        ).first()
        
        if existing_blocked:
            return None, "Device is already blocked"
        
        # Create UserBlockedDevice record
        blocked_device = UserBlockedDevice(
            user_id=user_id,
            router_id=router_id,
            device_id=device_id,
            device_ip=device_ip,
            device_mac=device_mac,
            block_type='manual',
            blocked_at=datetime.utcnow(),
            is_active=True
        )
        
        session.add(blocked_device)
        session.flush()  # Get the ID without committing
        
        result = blocked_device.to_dict()
        logger.info(f"Blocked device {device_ip} (ID: {device_id}) for user {user_id}, router {router_id}")
        return result, None
        
    except Exception as e:
        logger.error(f"Failed to block device: {str(e)}")
        return None, f"Failed to block device: {str(e)}"


@handle_db_errors("Unblock device")  
def unblock_device_db(user_id: str, router_id: str, blocked_device_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Set blocked device as inactive (unblock).
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        blocked_device_id: Blocked device record UUID
        
    Returns:
        Tuple of (success_message_dict, error_message)
    """
    session = SessionContext.get()
    
    try:
        blocked_device = session.query(UserBlockedDevice).filter(
            and_(
                UserBlockedDevice.id == blocked_device_id,
                UserBlockedDevice.user_id == user_id,
                UserBlockedDevice.router_id == router_id,
                UserBlockedDevice.is_active == True
            )
        ).first()
        
        if not blocked_device:
            return None, "Blocked device not found"
        
        # Update to inactive and set unblocked timestamp
        blocked_device.is_active = False
        blocked_device.unblocked_at = datetime.utcnow()
        
        session.flush()
        
        result = {
            "message": "Device unblocked successfully",
            "device_ip": str(blocked_device.device_ip),
            "unblocked_at": blocked_device.unblocked_at.isoformat()
        }
        
        logger.info(f"Unblocked device {blocked_device.device_ip} (ID: {blocked_device_id}) for user {user_id}, router {router_id}")
        return result, None
        
    except Exception as e:
        logger.error(f"Failed to unblock device: {str(e)}")
        return None, f"Failed to unblock device: {str(e)}"


@handle_db_errors("Check if device is blocked")
def is_device_blocked_db(user_id: str, router_id: str, device_ip: str = None, device_id: str = None) -> Tuple[Optional[bool], Optional[str]]:
    """
    Check if a device is currently blocked.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        device_ip: Device IP address (optional)
        device_id: Device UUID (optional)
        
    Returns:
        Tuple of (is_blocked_boolean, error_message)
    """
    session = SessionContext.get()
    
    try:
        if not device_ip and not device_id:
            return None, "device_ip or device_id is required"
        
        query_conditions = [
            UserBlockedDevice.user_id == user_id,
            UserBlockedDevice.router_id == router_id,
            UserBlockedDevice.is_active == True
        ]
        
        if device_id:
            query_conditions.append(UserBlockedDevice.device_id == device_id)
        if device_ip:
            query_conditions.append(UserBlockedDevice.device_ip == device_ip)
        
        blocked_device = session.query(UserBlockedDevice).filter(
            and_(*query_conditions)
        ).first()
        
        return blocked_device is not None, None
        
    except Exception as e:
        logger.error(f"Failed to check if device is blocked: {str(e)}")
        return None, f"Failed to check if device is blocked: {str(e)}"


@handle_db_errors("Get blocked device IDs")
def get_blocked_device_ids_db(user_id: str, router_id: str) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Get list of all blocked device IDs for filtering purposes.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        
    Returns:
        Tuple of (list_of_device_ids, error_message)
    """
    session = SessionContext.get()
    
    try:
        blocked_devices = session.query(UserBlockedDevice.device_id).filter(
            and_(
                UserBlockedDevice.user_id == user_id,
                UserBlockedDevice.router_id == router_id,
                UserBlockedDevice.is_active == True,
                UserBlockedDevice.device_id.isnot(None)
            )
        ).all()
        
        # Extract device IDs from query result tuples
        device_ids = [str(blocked_device[0]) for blocked_device in blocked_devices if blocked_device[0]]
        
        logger.debug(f"Retrieved {len(device_ids)} blocked device IDs for user {user_id}, router {router_id}")
        return device_ids, None
        
    except Exception as e:
        logger.error(f"Failed to get blocked device IDs: {str(e)}")
        return None, f"Failed to get blocked device IDs: {str(e)}"
