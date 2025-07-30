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
    execute_scan_network
)

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