from models.settings import UserSetting
from models.router import UserRouter
from utils.logging_config import get_logger

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
        # Check if routerId is already associated with another user
        logger.info("Checking if router_id is already associated with another user...")
        existing_router = session.query(UserRouter).filter_by(router_id=router_id).first()
        if existing_router:
            logger.info(f"Found existing router record: user_id={existing_router.user_id}, current_user_id={user_id}")
            if str(existing_router.user_id) != str(user_id):
                logger.error(f"Router ID {router_id} already associated with user {existing_router.user_id}, not {user_id}")
                return None, 'RouterId already associated with another user.'
            else:
                logger.info("Router ID belongs to the same user, proceeding...")
        else:
            logger.info("No existing router record found for this router_id")

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