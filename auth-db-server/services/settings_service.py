from utils.logging_config import get_logger
from services.commands_server_operations.settings_execute import execute_get_wifi_name, execute_update_wifi_name, execute_set_wifi_password
from typing import Dict, Optional, Tuple
from .base import (
    handle_service_errors,
    log_service_operation
)
from services.db_operations.settings_db import (
    save_router_id_setting as db_save_router_id_setting,
    get_router_id_setting as db_get_router_id_setting,
)

# Set up logging
logger = get_logger(__name__)

def save_router_id_setting(user_id, router_id):
    logger.info(f"=== Starting save_router_id_setting ===")
    logger.info(f"Input parameters - user_id: {user_id}, router_id: {router_id}")
    result, error = db_save_router_id_setting(user_id, router_id)
    if error:
        logger.error(f"=== save_router_id_setting failed: {error} ===")
        return None, error
    logger.info(f"=== save_router_id_setting completed successfully ===")
    return result, None

def get_router_id_setting(user_id):
    logger.info(f"=== Starting get_router_id_setting ===")
    logger.info(f"Input parameter - user_id: {user_id}")
    result, error = db_get_router_id_setting(user_id)
    if error:
        logger.error(f"=== get_router_id_setting failed: {error} ===")
        return None, error
    logger.info(f"=== get_router_id_setting completed successfully ===")
    return result, None

@handle_service_errors("get_wifi_name")
def get_wifi_name(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Retrieves the router's name.
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (success_response, error_message)
    """
    log_service_operation("get_wifi_name", user_id, router_id, session_id)
    # Execute wifi command
    cmd_response, cmd_error = execute_get_wifi_name(router_id, session_id)
    if cmd_error:
        log_service_operation("get_wifi_name", user_id, router_id, session_id, success=False, error=cmd_error)
        return None, cmd_error

    log_service_operation("get_wifi_name", user_id, router_id, session_id, success=True)
    return cmd_response, None

@handle_service_errors("update_wifi_name")
def update_wifi_name(user_id: str, router_id: str, session_id: str, wifi_name: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Updates the router's WiFi name (SSID).
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        wifi_name: New WiFi name to set
        
    Returns:
        Tuple of (success_response, error_message)
    """
    log_service_operation("update_wifi_name", user_id, router_id, session_id)
    
    # Execute wifi update command
    cmd_response, cmd_error = execute_update_wifi_name(router_id, session_id, wifi_name)
    if cmd_error:
        log_service_operation("update_wifi_name", user_id, router_id, session_id, success=False, error=cmd_error)
        return None, cmd_error

    log_service_operation("update_wifi_name", user_id, router_id, session_id, success=True)
    return cmd_response, None

@handle_service_errors("set_wifi_password")
def set_wifi_password(user_id: str, router_id: str, session_id: str, wifi_password: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Sets the router's WiFi password.
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        wifi_password: New WiFi password to set
        
    Returns:
        Tuple of (success_response, error_message)
    """
    log_service_operation("set_wifi_password", user_id, router_id, session_id)
    
    # Execute wifi password command
    cmd_response, cmd_error = execute_set_wifi_password(router_id, session_id, wifi_password)
    if cmd_error:
        log_service_operation("set_wifi_password", user_id, router_id, session_id, success=False, error=cmd_error)
        return None, cmd_error

    log_service_operation("set_wifi_password", user_id, router_id, session_id, success=True)
    return cmd_response, None