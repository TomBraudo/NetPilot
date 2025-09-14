"""
Scheduler Session Manager

This utility ensures active sessions for scheduled tasks by reusing existing
session_execute functions. It handles session refresh and creation without
relying on Flask request context.
"""

from typing import Optional, Tuple
from utils.logging_config import get_logger
from services.commands_server_operations.session_execute import (
    execute_refresh_session,
    execute_start_session
)

logger = get_logger('scheduler.session_manager')


def ensure_active_session(user_id: str, router_id: str, last_known_session_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Ensure an active session exists for the given user_id and router_id.
    
    This function is designed for scheduler use where there's no Flask request context.
    It follows the project convention: session_id = user_id.
    
    Args:
        user_id: User's UUID (will be used as session_id)
        router_id: Router's UUID
        last_known_session_id: Optional previous session_id for refresh attempts
        
    Returns:
        Tuple of (session_id, error_message)
        - session_id: The active session_id (always user_id if successful)
        - error_message: Error description if failed, None if successful
    """
    session_id = user_id  # Project convention: session_id = user_id
    
    # First, try to refresh existing session if we have a last known session_id
    if last_known_session_id:
        logger.debug(f"Attempting to refresh existing session {last_known_session_id} for router {router_id}")
        try:
            result, error = execute_refresh_session(router_id, last_known_session_id)
            if not error:
                logger.info(f"Successfully refreshed existing session {last_known_session_id} for router {router_id}")
                return last_known_session_id, None
            else:
                logger.debug(f"Failed to refresh session {last_known_session_id}: {error}")
        except Exception as e:
            logger.warning(f"Exception during session refresh: {e}")
    
    # If refresh failed or no previous session, start a new one
    logger.info(f"Starting new session for user {user_id} on router {router_id}")
    try:
        result, error = execute_start_session(router_id, session_id, restart=False)
        if not error:
            logger.info(f"Successfully started new session {session_id} for router {router_id}")
            return session_id, None
        else:
            logger.error(f"Failed to start session {session_id} for router {router_id}: {error}")
            return None, error
    except Exception as e:
        error_msg = f"Exception during session start: {e}"
        logger.error(f"Failed to start session {session_id} for router {router_id}: {error_msg}")
        return None, error_msg


def wait_for_session_ready(user_id: str, router_id: str, max_wait_seconds: int = 30) -> Tuple[Optional[str], Optional[str]]:
    """
    Wait for a session to be ready, with timeout.
    
    This function ensures the session is fully established before returning.
    It's useful when session creation might take some time to complete.
    
    Args:
        user_id: User's UUID (will be used as session_id)
        router_id: Router's UUID
        max_wait_seconds: Maximum time to wait for session readiness
        
    Returns:
        Tuple of (session_id, error_message)
        - session_id: The ready session_id if successful
        - error_message: Error description if failed or timed out
    """
    import time
    
    session_id = user_id
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        # Try to start/refresh the session
        current_session_id, error = ensure_active_session(user_id, router_id)
        if not error and current_session_id:
            logger.info(f"Session {current_session_id} is ready for router {router_id}")
            return current_session_id, None
        
        # Wait a bit before retrying
        time.sleep(2)
        logger.debug(f"Waiting for session readiness, retrying... (elapsed: {time.time() - start_time:.1f}s)")
    
    error_msg = f"Session creation timed out after {max_wait_seconds} seconds"
    logger.error(f"Failed to establish session for user {user_id} on router {router_id}: {error_msg}")
    return None, error_msg
