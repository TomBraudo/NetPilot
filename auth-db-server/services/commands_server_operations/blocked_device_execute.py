"""
Blocked Device Commands Server Operations

This module handles blocked device operations by leveraging bandwidth limiting.
Since there's no direct blocking API, devices are "blocked" by applying very
restrictive bandwidth limits (0.1 Mbps) and "unblocked" by removing those limits.

All functions return (result, error) tuples and are decorated to inject
the Commands Server manager and handle errors consistently.
"""

from typing import Dict, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import with_commands_server, handle_commands_errors
from .bandwidth_execute import execute_apply_device_limit, execute_delete_device_limit

logger = get_logger('services.commands_server_operations.blocked_device_execute')

# Block limits: Very restrictive bandwidth to effectively "block" the device
BLOCK_DOWNLOAD_MBPS = 0.1
BLOCK_UPLOAD_MBPS = 0.1


@with_commands_server
@handle_commands_errors("Block device")
def execute_block_device(
    commands_server,
    router_id: str,
    session_id: str,
    device_ip: str
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Block a device by applying very restrictive bandwidth limits.
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        device_ip: IP address of the device to block
        
    Returns:
        Tuple of (result_dict, error_message)
    """
    if not device_ip:
        return None, "device_ip is required"
    
    logger.info(f"Blocking device {device_ip} by applying {BLOCK_DOWNLOAD_MBPS}Mbps limits on router {router_id}")
    
    # Apply very restrictive bandwidth limits to effectively block the device
    result, error = execute_apply_device_limit(
        router_id,
        session_id,
        device_ip,
        download_mbps=BLOCK_DOWNLOAD_MBPS,
        upload_mbps=BLOCK_UPLOAD_MBPS
    )
    
    if error:
        logger.error(f"Failed to block device {device_ip}: {error}")
        return None, f"Failed to apply blocking limits to device: {error}"
    
    logger.info(f"Successfully blocked device {device_ip} with {BLOCK_DOWNLOAD_MBPS}Mbps limits")
    
    # Return a consistent response format
    return {
        "device_ip": device_ip,
        "blocked": True,
        "download_limit_mbps": BLOCK_DOWNLOAD_MBPS,
        "upload_limit_mbps": BLOCK_UPLOAD_MBPS,
        "message": f"Device {device_ip} blocked successfully"
    }, None


@with_commands_server
@handle_commands_errors("Unblock device")
def execute_unblock_device(
    commands_server,
    router_id: str,
    session_id: str,
    device_ip: str
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Unblock a device by removing bandwidth limits.
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        device_ip: IP address of the device to unblock
        
    Returns:
        Tuple of (result_dict, error_message)
    """
    if not device_ip:
        return None, "device_ip is required"
    
    logger.info(f"Unblocking device {device_ip} by removing bandwidth limits on router {router_id}")
    
    # Remove bandwidth limits to unblock the device
    result, error = execute_delete_device_limit(
        router_id,
        session_id,
        device_ip
    )
    
    if error:
        logger.error(f"Failed to unblock device {device_ip}: {error}")
        return None, f"Failed to remove blocking limits from device: {error}"
    
    logger.info(f"Successfully unblocked device {device_ip}")
    
    # Return a consistent response format
    return {
        "device_ip": device_ip,
        "blocked": False,
        "message": f"Device {device_ip} unblocked successfully"
    }, None
