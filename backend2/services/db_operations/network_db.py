"""
Network Database Operations Service

This service handles all database operations for network functionality.
It provides data validation, state checking, and CRUD operations for network-related data.
All functions return (result, error) tuple format.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from utils.logging_config import get_logger
from .base import with_db_session, handle_db_errors
from models.device import UserDevice

logger = get_logger('services.db_operations.network_db')


@with_db_session
@handle_db_errors("Save network scan result")
def save_network_scan_result(session, user_id: str, router_id: str, scan_result: List[Dict]) -> Tuple[Optional[bool], Optional[str]]:
    """
    Save network scan result to database by creating/updating UserDevice entries.
    
    Args:
        session: Database session (automatically injected)
        user_id: User's UUID
        router_id: Router's UUID
        scan_result: List of discovered devices with format:
                    [{"ip": "<ip>", "mac": "<mac>", "hostname": "<hostname>", "vendor": "<vendor>"}]
        
    Returns:
        Tuple of (success_boolean, error_message)
    """
    if not scan_result:
        logger.debug(f"No devices to save for user {user_id}, router {router_id}")
        return True, None
    
    logger.info(f"Saving network scan result for user {user_id}, router {router_id} with {len(scan_result)} devices")
    
    devices_updated = 0
    devices_created = 0
    current_time = datetime.now()
    
    try:
        for device_data in scan_result:
            # Extract device information from scan result
            device_ip = device_data.get('ip')
            device_mac = device_data.get('mac')
            device_hostname = device_data.get('hostname')
            device_vendor = device_data.get('vendor')
            
            # Skip devices without IP address (required field)
            if not device_ip:
                logger.warning(f"Skipping device without IP address: {device_data}")
                continue
            
            # Check if device already exists (first by IP, then by MAC if available)
            existing_device = None
            
            # First, try to find by IP address
            if device_ip:
                existing_device = session.query(UserDevice).filter(
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id,
                    UserDevice.ip == device_ip
                ).first()
            
            # If not found by IP and MAC is available, try to find by MAC
            if not existing_device and device_mac:
                existing_device = session.query(UserDevice).filter(
                    UserDevice.user_id == user_id,
                    UserDevice.router_id == router_id,
                    UserDevice.mac == device_mac
                ).first()
            
            if existing_device:
                # Update existing device
                existing_device.hostname = device_hostname
                existing_device.manufacturer = device_vendor
                existing_device.last_seen = current_time
                # Update IP/MAC if they've changed
                if device_ip and existing_device.ip != device_ip:
                    existing_device.ip = device_ip
                if device_mac and existing_device.mac != device_mac:
                    existing_device.mac = device_mac
                
                devices_updated += 1
                logger.debug(f"Updated existing device: {device_ip} ({device_mac})")
            else:
                # Create new device entry
                new_device = UserDevice(
                    user_id=user_id,
                    router_id=router_id,
                    ip=device_ip,
                    mac=device_mac,
                    hostname=device_hostname,
                    manufacturer=device_vendor,
                    first_seen=current_time,
                    last_seen=current_time
                )
                
                session.add(new_device)
                devices_created += 1
                logger.debug(f"Created new device: {device_ip} ({device_mac})")
        
        # Commit all changes
        session.flush()
        
        logger.info(f"Network scan save completed for user {user_id}, router {router_id}: "
                   f"created {devices_created}, updated {devices_updated} devices")
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error saving network scan result: {str(e)}", exc_info=True)
        return None, f"Failed to save network scan result: {str(e)}"

