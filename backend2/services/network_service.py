"""
Network Service - Main Orchestration Layer

This service acts as the conductor for network operations, coordinating between
database operations and router command executions. It follows the 3-layer architecture:
1. This service (orchestration) - calls db + commands
2. services/db_operations/network_db.py - Database operations  
3. services/commands_server_operations/network_execute.py - Router command execution

This service focuses exclusively on network scanning functionality.
Other network operations (blocking, unblocking, etc.) are handled by separate services.
"""
from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import (
    handle_service_errors,
    log_service_operation
)

# Database operations imports
from services.db_operations.network_db import (
    save_network_scan_result as db_save_network_scan_result
)

# Router command execution imports
from services.commands_server_operations.network_execute import (
    execute_scan_network,
    automatic_scan
)

from services.task_registry import register_task

from services.mail_service import send_mail

logger = get_logger('services.network_service')

@handle_service_errors("Scan network")
def scan_network(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Scan the network via router to find connected devices.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID  
        session_id: Session's UUID
        
    Returns:
        Tuple of (list_of_devices, error_message)
    """
    log_service_operation("scan_network", user_id, router_id, session_id)
    
    # Execute router command to scan network
    cmd_response, cmd_error = execute_scan_network(router_id, session_id)
    if cmd_error:
        log_service_operation("scan_network", user_id, router_id, session_id, success=False, error=cmd_error)
        return None, cmd_error
    
    # Save scan result to database
    if cmd_response:
        db_save_result, db_error = db_save_network_scan_result(user_id, router_id, cmd_response)
        if db_error:
            # Log warning but don't fail the operation since network scan succeeded
            logger.warning(f"Failed to save network scan result to database: {db_error}")
    
    log_service_operation("scan_network", user_id, router_id, session_id, success=True)
    return cmd_response, None 

@handle_service_errors("Automatic network scan")
@register_task("network.automatic_scan")
def automatic_scan_network(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Automatic network scan that works both as API call and scheduled task.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
    """
    log_service_operation("automatic_scan_network", user_id, router_id, session_id)
    
    # Get user email for notifications - now works in both contexts!
    user_email = _get_user_email(user_id)
    if user_email:
        logger.info(f"Executing automatic scan for user {user_id} ({user_email})")
    
    result, error = automatic_scan(router_id, session_id, user_id)
    if error:
        log_service_operation("automatic_scan_network", user_id, router_id, session_id, success=False, error=error)
        return None, error
    
    # Send notification email if scan found new devices
    if result and user_email:
        new_device_count = len(result)
        
        if new_device_count > 0:
            # Only send email if there are actually new devices
            _send_scan_notification_email(user_email, result)
        else:
            # No new devices found - skip email notification
            logger.info(f"No new devices found during scan - skipping email notification to {user_email}")
    elif result and not user_email:
        # Scan completed but no user email available
        new_device_count = len(result)
        if new_device_count > 0:
            logger.info(f"Scan found {new_device_count} new devices but no user email available for notifications")
        else:
            logger.info("Scan completed - no new devices found and no user email available")
    elif not result:
        # Scan completed but returned no result (shouldn't happen with successful scan)
        logger.info("Scan completed but returned no result - no email notification sent")
    
    log_service_operation("automatic_scan_network", user_id, router_id, session_id, success=True)
    
    # Log final summary
    if result:
        new_device_count = len(result)
        if new_device_count > 0:
            logger.info(f"Automatic scan completed successfully: {new_device_count} new devices found and added to guests group")
        else:
            logger.info("Automatic scan completed successfully: No new devices found (existing devices updated)")
    else:
        logger.info("Automatic scan completed successfully: No devices returned")
    
    return result, None


def _get_user_email(user_id: str) -> Optional[str]:
    """
    Get user email that works seamlessly in both HTTP request and scheduled task contexts.
    
    Thanks to the updated SessionContext.get(), this function now works everywhere:
    - HTTP requests: Uses existing session from request lifecycle
    - Scheduled tasks: Automatically creates new session if needed
    
    Args:
        user_id: User's UUID
        
    Returns:
        User's email or None if not found
    """
    try:
        from managers.db_session_context import SessionContext
        from models.user import User
        
        # SessionContext.get() now automatically creates a session if none exists
        session = SessionContext.get()
        user = session.query(User).filter_by(id=user_id).first()
        return user.email if user else None
        
    except Exception as e:
        logger.error(f"Failed to get user email for {user_id}: {e}")
        return None


def _send_scan_notification_email(user_email: str, new_devices: List[Dict]) -> bool:
    """
    Send notification email about new devices found during scan.
    
    Args:
        user_email: User's email address
        new_devices: List of new devices found
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    if not new_devices or len(new_devices) == 0:
        logger.info(f"No new devices found - skipping email notification to {user_email}")
        return False
    
    try:
        new_device_count = len(new_devices)
        subject = f"NetPilot: {new_device_count} new devices found"
        body = f"Your automatic network scan found {new_device_count} new devices that have been added to the 'guests' group."
        
        success, error = send_mail(user_email, subject, body)
        if error:
            logger.warning(f"Failed to send notification email to {user_email}: {error}")
            return False
        else:
            logger.info(f"Sent notification email to {user_email} about {new_device_count} new devices")
            return True

        return True
        
    except Exception as e:
        logger.warning(f"Failed to send notification email to {user_email}: {e}")
        return False



