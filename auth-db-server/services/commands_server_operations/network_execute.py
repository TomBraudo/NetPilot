"""
Network Commands Server Operations

This service handles all router command executions for network functionality.
It provides command execution for network operations including network scanning
through the commands server.
All functions return (result, error) tuple format.
"""

from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import with_commands_server, handle_commands_errors

logger = get_logger('services.commands_server_operations.network_execute')

base_path = "/api/network"

@with_commands_server
@handle_commands_errors("Scan network")
def execute_scan_network(commands_server, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Execute command to scan the network via router to find connected devices.
    
    Corresponds to: GET /api/network/scan
    Expected Query Params: ?sessionId=<session_id>&routerId=<router_id>
    Expected Response Body: Array of device objects with ip, mac, hostname properties
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (list_of_devices, error_message)
    """
    endpoint = f"{base_path}/scan"
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "GET", None, None
    )
    
    # If there was a communication error
    if error:
        return None, error
    
    # If no response received
    if not response_data:
        return None, "No response from commands server"
    
    # The manager already unpacked the response - if we have response_data and no error, it was successful
    if response_data and not error:
        # The response_data is already the device list (data section from commands server)
        devices = response_data if isinstance(response_data, list) else []
        logger.info(f"Network scan completed successfully for router {router_id}, found {len(devices)} devices")
        return devices, None
    else:
        # This should not happen as error would be set, but keeping for safety
        return None, "Scan network failed: 'list' object has no attribute 'get'"


@with_commands_server
@handle_commands_errors("Automatic network scan")
def automatic_scan(commands_server, router_id: str, session_id: str, user_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Automatically scan the network and manage devices:
    1. Scans the network for active devices
    2. Updates existing devices in the database
    3. Creates a "guests" group if it doesn't exist
    4. Adds new devices to the guests group
    5. Returns list of new devices
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        user_id: User ID for the operation
        
    Returns:
        Tuple of (list_of_new_devices, error_message)
    """
    # Validate user_id parameter
    if not user_id:
        return None, "User ID is required"
    
    # Step 1: Scan the network
    scanned_devices, scan_error = execute_scan_network(router_id, session_id)
    if scan_error:
        return None, f"Network scan failed: {scan_error}"
    
    if not scanned_devices:
        logger.info(f"No devices found during network scan for router {router_id}")
        return [], None
    
    logger.info(f"Network scan found {len(scanned_devices)} devices for router {router_id}")
    
    try:
        # Step 2: Check database for existing devices and update/create them
        from services.device_service import bulk_create_or_update_devices
        from services.db_operations.device_db import get_devices_by_ips_db
        
        # Get existing devices by IPs to identify which are new
        existing_devices = get_devices_by_ips_db(user_id, router_id, [device.get('ip') for device in scanned_devices])
        existing_ips = {device.ip for device in existing_devices}
        
        # Separate new and existing devices
        new_devices = []
        existing_device_data = []
        
        for device in scanned_devices:
            if device.get('ip') in existing_ips:
                existing_device_data.append(device)
            else:
                new_devices.append(device)
        
        # Update existing devices
        if existing_device_data:
            try:
                updated_devices = bulk_create_or_update_devices(user_id, router_id, existing_device_data)
                logger.info(f"Successfully updated {len(updated_devices)} existing devices")
            except Exception as e:
                logger.warning(f"Failed to update existing devices: {e}")
        
        # Step 3: Create "guests" group if it doesn't exist
        from services.device_group_service import get_user_device_groups, create_device_group
        
        existing_groups = get_user_device_groups(user_id, router_id)
        guests_group = None
        
        for group in existing_groups:
            if group.get('name') == 'guests':
                guests_group = group
                break
        
        if not guests_group:
            logger.info(f"Creating 'guests' group for user {user_id} and router {router_id}")
            try:
                guests_group = create_device_group(user_id, router_id, 'guests', 'Automatically created group for new devices')
                logger.info(f"Successfully created 'guests' group with ID: {guests_group.get('id')}")
            except Exception as e:
                logger.error(f"Failed to create guests group: {e}")
                return None, f"Failed to create guests group: {str(e)}"
        
        # Step 4: Add new devices to the guests group
        if new_devices:
            # Create the new devices in the database
            try:
                created_devices = bulk_create_or_update_devices(user_id, router_id, new_devices)
                logger.info(f"Successfully created {len(created_devices)} new devices")
            except Exception as e:
                logger.error(f"Failed to create new devices: {e}")
                return None, f"Failed to create new devices: {str(e)}"
            
            # Add new devices to the guests group
            from services.device_group_service import add_device_to_group
            
            for device in created_devices:
                add_success = add_device_to_group(user_id, router_id, guests_group['id'], device['id'])
                if not add_success:
                    logger.warning(f"Failed to add device {device.get('ip')} to guests group")
            
            logger.info(f"Successfully added {len(new_devices)} new devices to guests group")
        
        logger.info(f"Automatic scan completed: {len(existing_device_data)} existing devices updated, {len(new_devices)} new devices added to guests group")
        return new_devices, None
        
    except Exception as e:
        logger.error(f"Error during automatic scan: {str(e)}", exc_info=True)
        return None, f"Automatic scan failed: {str(e)}"
