from flask import Blueprint, request
from utils.response_helpers import build_success_response, build_error_response
from services.session_service import start_session as start_session_service
from utils.middleware import router_context_required

session_bp = Blueprint('session', __name__)

@session_bp.route('/start', methods=['POST'])
@router_context_required
def start_session():
    data = request.get_json()
    router_id = data.get('routerId')
    restart = data.get('restart', False)
    result, error = start_session_service(router_id, None, restart)
    if error is None:
        return build_success_response(result, 0)
    else:
        return build_error_response(error, 400, 'SESSION_START_FAILED', 0) 