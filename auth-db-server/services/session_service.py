"""
Session Service - Main Orchestration Layer

This service acts as the conductor for session operations, coordinating between
database operations and router command executions. It follows the 3-layer architecture:
1. This service (orchestration) - calls commands server operations (no db operations needed for sessions)
2. services/commands_server_operations/session_execute.py - Router command execution

Even though sessions don't require database operations, we maintain the same architectural 
pattern as other services (like whitelist) for consistency.
"""

from typing import Dict, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import (
    handle_service_errors,
    log_service_operation
)

# Router command execution imports
from services.commands_server_operations.session_execute import (
    execute_start_session,
    execute_end_session,
    execute_refresh_session
)

logger = get_logger('services.session_service')

@handle_service_errors("Start session")
def start_session(user_id: str, router_id: str, session_id: str, restart: bool = False) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Start a new session for a router and set up the required infrastructure.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        restart: Whether to restart the session if it exists
        
    Returns:
        Tuple of (session_info_dict, error_message)
    """
    log_service_operation("start_session", user_id, router_id, session_id, {"restart": restart})
    
    # Execute router command (no database operations needed for sessions)
    cmd_response, cmd_error = execute_start_session(router_id, session_id, restart)
    if cmd_error:
        log_service_operation("start_session", user_id, router_id, session_id, {"restart": restart}, success=False, error=cmd_error)
        return None, cmd_error
    
    log_service_operation("start_session", user_id, router_id, session_id, {"restart": restart}, success=True)
    return cmd_response, None


@handle_service_errors("End session")
def end_session(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    End the session for a router and clean up connections.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (result_dict, error_message)
    """
    log_service_operation("end_session", user_id, router_id, session_id)
    
    # Execute router command (no database operations needed for sessions)
    cmd_response, cmd_error = execute_end_session(router_id, session_id)
    if cmd_error:
        log_service_operation("end_session", user_id, router_id, session_id, success=False, error=cmd_error)
        return None, cmd_error
    
    log_service_operation("end_session", user_id, router_id, session_id, success=True)
    return cmd_response, None


@handle_service_errors("Refresh session")
def refresh_session(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Refresh a session's activity timer.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (result_dict, error_message)
    """
    log_service_operation("refresh_session", user_id, router_id, session_id)
    
    # Execute router command (no database operations needed for sessions)
    cmd_response, cmd_error = execute_refresh_session(router_id, session_id)
    if cmd_error:
        log_service_operation("refresh_session", user_id, router_id, session_id, success=False, error=cmd_error) 
        return None, cmd_error
    
    log_service_operation("refresh_session", user_id, router_id, session_id, success=True)
    return cmd_response, None 