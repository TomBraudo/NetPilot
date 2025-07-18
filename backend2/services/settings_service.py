from models.settings import UserSetting
from models.router import UserRouter

def save_router_id_setting(session, user_id, router_id):
    # Check routerId validity: not empty, not used by another user
    if not router_id or not isinstance(router_id, str):
        return None, 'Invalid routerId.'
    # Check if routerId is already associated with another user
    existing_router = session.query(UserRouter).filter_by(router_id=router_id).first()
    if existing_router and str(existing_router.user_id) != str(user_id):
        return None, 'RouterId already associated with another user.'
    # Save or update UserSetting for routerId
    setting = session.query(UserSetting).filter_by(user_id=user_id, setting_key='routerId').first()
    if setting:
        setting.setting_value = {'routerId': router_id}
    else:
        setting = UserSetting(user_id=user_id, setting_key='routerId', setting_value={'routerId': router_id})
        session.add(setting)
    # Optionally, also update UserRouter table for this user
    user_router = session.query(UserRouter).filter_by(user_id=user_id, router_id=router_id).first()
    if not user_router:
        user_router = UserRouter(user_id=user_id, router_id=router_id, is_active=True)
        session.add(user_router)
    session.commit()
    return {'routerId': router_id, 'message': 'RouterId saved in settings.'}, None 

def get_router_id_setting(session, user_id):
    from models.settings import UserSetting
    setting = session.query(UserSetting).filter_by(user_id=user_id, setting_key='routerId').first()
    if setting and setting.setting_value and 'routerId' in setting.setting_value:
        return {'routerId': setting.setting_value['routerId']}, None
    else:
        return None, 'No routerId found for user' 