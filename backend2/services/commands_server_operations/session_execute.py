"""
Session Commands Server Operations

This service handles all router command executions for session functionality.
It provides command execution for session operations including session start,
end, and refresh through the commands server.
All functions return (result, error) tuple format.
"""

from typing import Dict, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import with_commands_server, handle_commands_errors

logger = get_logger('services.commands_server_operations.session_execute')

base_path = "/api/session"

@with_commands_server
@handle_commands_errors("Start session")
def execute_start_session(commands_server, router_id: str, session_id: str, restart: bool = False) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to start a new session for a router and set up the required infrastructure.
    
    Corresponds to: POST /api/session/start
    Expected Request Body: {"sessionId": "<session_id>", "routerId": "<router_id>", "restart": false}
    Expected Response Body: {"session_id": "<session_id>", "router_reachable": true, 
                            "infrastructure_ready": true, "message": "Session established successfully"}
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        restart: Whether to restart the session if it exists
        
    Returns:
        Tuple of (session_info_dict, error_message)
    """
    endpoint = f"{base_path}/start"
    body = {
        "sessionId": session_id,
        "routerId": router_id,
        "restart": restart
    }
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "POST", None, body
    )
    
    if response_data and response_data.get('success'):
        # Extract session information from response
        data = response_data.get('data', {})
        result = {
            'session_id': data.get('session_id', session_id),
            'router_reachable': data.get('router_reachable', True),
            'infrastructure_ready': data.get('infrastructure_ready', True),
            'message': data.get('message', 'Session established successfully')
        }
        logger.info(f"Session started successfully for router {router_id} with session ID {session_id}")
        return result, None
    
    return None, error or "Failed to start session on router"


@with_commands_server
@handle_commands_errors("End session")
def execute_end_session(commands_server, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to end the session for a router and clean up connections.
    
    Corresponds to: POST /api/session/end
    Expected Request Body: {"sessionId": "<session_id>", "routerId": "<router_id>"}
    Expected Response Body: {"message": "Session ended"}
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (result_dict, error_message)
    """
    endpoint = f"{base_path}/end"
    body = {
        "sessionId": session_id,
        "routerId": router_id
    }
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "POST", None, body
    )
    
    if response_data and response_data.get('success'):
        # Extract session end information from response
        data = response_data.get('data', {})
        result = {
            'message': data.get('message', 'Session ended')
        }
        logger.info(f"Session ended successfully for router {router_id} with session ID {session_id}")
        return result, None
    
    return None, error or "Failed to end session on router"


@with_commands_server
@handle_commands_errors("Refresh session")
def execute_refresh_session(commands_server, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute command to refresh a session's activity timer.
    
    Corresponds to: POST /api/session/refresh
    Expected Request Body: {"sessionId": "<session_id>"}
    Expected Response Body: {"message": "Session <session_id> refreshed"}
    
    Args:
        commands_server: Commands server manager (automatically injected)
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        
    Returns:
        Tuple of (result_dict, error_message)
    """
    endpoint = f"{base_path}/refresh"
    body = {
        "sessionId": session_id
    }
    
    response_data, error = commands_server.execute_router_command(
        router_id, session_id, endpoint, "POST", None, body
    )
    
    if response_data and response_data.get('success'):
        # Extract session refresh information from response
        data = response_data.get('data', {})
        result = {
            'message': data.get('message', f'Session {session_id} refreshed')
        }
        logger.info(f"Session refreshed successfully for router {router_id} with session ID {session_id}")
        return result, None
    
    return None, error or "Failed to refresh session on router"
