from typing import Dict, Optional, Tuple
from utils.logging_config import get_logger
from managers.db_session_context import SessionContext

logger = get_logger('services.db_operations.settings_db')


def save_router_id_setting(user_id: str, router_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Persist routerId in UserSetting and ensure an active UserRouter.
    No commits here; caller controls transaction.
    """
    from models.settings import UserSetting
    from models.router import UserRouter

    logger.info("=== DB save_router_id_setting ===")
    if not router_id:
        return None, 'Invalid routerId.'

    session = SessionContext.get()
    try:
        # Upsert UserSetting(routerId)
        setting = session.query(UserSetting).filter_by(user_id=user_id, setting_key='routerId').first()
        if setting:
            setting.setting_value = {'routerId': router_id}
        else:
            setting = UserSetting(user_id=user_id, setting_key='routerId', setting_value={'routerId': router_id})
            session.add(setting)

        # Ensure UserRouter active
        user_router = session.query(UserRouter).filter_by(user_id=user_id, router_id=router_id).first()
        if user_router:
            if not user_router.is_active:
                user_router.is_active = True
        else:
            user_router = UserRouter(user_id=user_id, router_id=router_id, is_active=True)
            session.add(user_router)

        return {'routerId': router_id, 'message': 'RouterId saved in settings.'}, None
    except Exception as e:
        logger.error(f"DB save_router_id_setting failed: {e}", exc_info=True)
        return None, f'Failed to save routerId: {str(e)}'


def get_router_id_setting(user_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Fetch routerId from UserSetting; also inspects UserRouter for visibility.
    No commits here; caller controls transaction.
    """
    from models.settings import UserSetting
    from models.router import UserRouter

    logger.info("=== DB get_router_id_setting ===")
    session = SessionContext.get()
    try:
        setting = session.query(UserSetting).filter_by(user_id=user_id, setting_key='routerId').first()
        if setting and setting.setting_value and 'routerId' in setting.setting_value:
            router_id = setting.setting_value['routerId']
            if router_id and len(str(router_id).strip()) > 0:
                return {'routerId': router_id}, None

        # Visibility aid (does not change semantics)
        _ = session.query(UserRouter).filter_by(user_id=user_id, is_active=True).all()
        return None, 'No routerId found for user'
    except Exception as e:
        logger.error(f"DB get_router_id_setting failed: {e}", exc_info=True)
        return None, f'Failed to fetch routerId: {str(e)}'


