from flask import Blueprint, request, g
from utils.response_helpers import build_success_response, build_error_response
from services.settings_service import save_router_id_setting
import time

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/router-id', methods=['POST'])
def save_router_id():
    start_time = time.time()
    session = g.db_session
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        return build_error_response('User not authenticated', 401, 'UNAUTHORIZED', start_time)
    data = request.get_json()
    router_id = data.get('routerId')
    if not router_id:
        return build_error_response('Missing routerId', 400, 'BAD_REQUEST', start_time)
    # Call service logic
    result, error = save_router_id_setting(session, user_id, router_id)
    if error:
        return build_error_response(error, 400, 'SAVE_FAILED', start_time)
    return build_success_response(result, start_time)

@settings_bp.route('/router-id', methods=['GET'])
def get_router_id():
    start_time = time.time()
    session = g.db_session
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        return build_error_response('User not authenticated', 401, 'UNAUTHORIZED', start_time)
    from services.settings_service import get_router_id_setting
    result, error = get_router_id_setting(session, user_id)
    if error:
        return build_error_response(error, 404, 'NOT_FOUND', start_time)
    return build_success_response(result, start_time) 