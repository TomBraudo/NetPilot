from models.settings import UserSetting
from models.router import UserRouter
from utils.logging_config import get_logger
from services.commands_server_operations.settings_execute import execute_get_wifi_name, execute_update_wifi_name, execute_set_wifi_password
from typing import Dict, List, Optional, Tuple, Any
from utils.logging_config import get_logger
from .base import (
    require_user_context,
    handle_service_errors,
    validate_ip_address,
    validate_rate_limit,
    log_service_operation
)

# Set up logging
logger = get_logger(__name__)

def save_router_id_setting(session, user_id, router_id):
    logger.info(f"=== Starting save_router_id_setting ===")
    logger.info(f"Input parameters - user_id: {user_id}, router_id: {router_id}")
    
    # Check routerId validity: not empty, not used by another user
    if not router_id:
        logger.error("Router ID is empty or None")
        return None, 'Invalid routerId.'
    
    logger.info(f"Router ID validation passed: {router_id}")
    
    try:
        # Allow multiple users to use the same router ID
        logger.info("Allowing multiple users to use the same router ID")

        # Save or update UserSetting for routerId
        logger.info("Querying existing UserSetting record...")
        setting = session.query(UserSetting).filter_by(user_id=user_id, setting_key='routerId').first()
        
        if setting:
            logger.info(f"Found existing UserSetting record: id={setting.id}")
            logger.info(f"Updating setting_value from {setting.setting_value} to {{'routerId': {router_id}}}")
            setting.setting_value = {'routerId': router_id}
            logger.info("UserSetting record updated successfully")
        else:
            logger.info("No existing UserSetting record found, creating new one...")
            setting = UserSetting(user_id=user_id, setting_key='routerId', setting_value={'routerId': router_id})
            session.add(setting)
            logger.info(f"New UserSetting record created and added to session: {setting}")
        
        # Optionally, also update UserRouter table for this user
        logger.info("Querying existing UserRouter record...")
        user_router = session.query(UserRouter).filter_by(user_id=user_id, router_id=router_id).first()
        
        if user_router:
            logger.info(f"Found existing UserRouter record: id={user_router.id}, is_active={user_router.is_active}")
            if not user_router.is_active:
                logger.info("Setting UserRouter is_active to True")
                user_router.is_active = True
            else:
                logger.info("UserRouter is already active")
        else:
            logger.info("No existing UserRouter record found, creating new one...")
            user_router = UserRouter(user_id=user_id, router_id=router_id, is_active=True)
            session.add(user_router)
            logger.info(f"New UserRouter record created and added to session: {user_router}")
        
        logger.info("About to commit session to database...")
        session.commit()
        logger.info("Session committed successfully!")
        
        logger.info(f"=== save_router_id_setting completed successfully ===")
        return {'routerId': router_id, 'message': 'RouterId saved in settings.'}, None
        
    except Exception as e:
        logger.error(f"Exception occurred in save_router_id_setting: {str(e)}", exc_info=True)
        logger.info("Rolling back session...")
        session.rollback()
        logger.error(f"=== save_router_id_setting failed ===")
        return None, f'Failed to save routerId: {str(e)}'

def get_router_id_setting(session, user_id):
    logger.info(f"=== Starting get_router_id_setting ===")
    logger.info(f"Input parameter - user_id: {user_id}")
    logger.info(f"User ID type: {type(user_id)}")
    
    try:
        from models.settings import UserSetting
        logger.info("Querying UserSetting for routerId...")
        logger.info(f"Query: session.query(UserSetting).filter_by(user_id={user_id}, setting_key='routerId')")
        
        setting = session.query(UserSetting).filter_by(user_id=user_id, setting_key='routerId').first()
        
        if setting:
            logger.info(f"Found UserSetting record: id={setting.id}, setting_value={setting.setting_value}")
            logger.info(f"Setting value type: {type(setting.setting_value)}")
            
            if setting.setting_value and 'routerId' in setting.setting_value:
                router_id = setting.setting_value['routerId']
                logger.info(f"Router ID found: {router_id}")
                logger.info(f"Router ID type: {type(router_id)}")
                
                # Additional validation
                if router_id and len(str(router_id).strip()) > 0:
                    logger.info(f"Router ID is valid and non-empty")
                    logger.info(f"=== get_router_id_setting completed successfully ===")
                    return {'routerId': router_id}, None
                else:
                    logger.warning(f"Router ID is empty or invalid: '{router_id}'")
            else:
                logger.warning("UserSetting found but setting_value is empty or missing routerId")
                logger.warning(f"Setting value keys: {list(setting.setting_value.keys()) if setting.setting_value else 'None'}")
        else:
            logger.info("No UserSetting record found for this user")
            logger.info("This means the user has never saved a router ID before")
        
        # Also check if there's a UserRouter record for this user
        logger.info("Checking UserRouter table for additional verification...")
        from models.router import UserRouter
        user_routers = session.query(UserRouter).filter_by(user_id=user_id, is_active=True).all()
        logger.info(f"Found {len(user_routers)} active UserRouter records for user")
        
        for i, user_router in enumerate(user_routers):
            logger.info(f"UserRouter {i+1}: id={user_router.id}, router_id={user_router.router_id}, is_active={user_router.is_active}")
        
        logger.info(f"=== get_router_id_setting completed - no routerId found ===")
        return None, 'No routerId found for user'
        
    except Exception as e:
        logger.error(f"Exception occurred in get_router_id_setting: {str(e)}", exc_info=True)
        logger.error(f"Exception type: {type(e)}")
        logger.error(f"=== get_router_id_setting failed ===")
        return None, f'Failed to fetch routerId: {str(e)}' 

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