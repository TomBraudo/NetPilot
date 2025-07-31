from flask import Blueprint, request, g
from utils.response_helpers import build_success_response, build_error_response
from services.session_service import (
    start_session,
    end_session,
    refresh_session
)
from utils.middleware import router_context_required
import time

session_bp = Blueprint('session', __name__)

@session_bp.route('/start', methods=['POST'])
@router_context_required
def start_session_route():
    """Start a new session for a router and set up the required infrastructure"""
    start_time = time.time()
    data = request.get_json() or {}
    restart = data.get('restart', False)
    
    result, error = start_session(g.user_id, g.router_id, g.session_id, restart)
    if error:
        return build_error_response(f"Session start failed: {error}", 500, "SESSION_START_FAILED", start_time)
    return build_success_response(result, start_time)


@session_bp.route('/end', methods=['POST'])
@router_context_required
def end_session_route():
    """End the session for a router and clean up connections"""
    start_time = time.time()
    
    result, error = end_session(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Session end failed: {error}", 500, "SESSION_END_FAILED", start_time)
    return build_success_response(result, start_time)


@session_bp.route('/refresh', methods=['POST'])
@router_context_required 
def refresh_session_route():
    """Refresh a session's activity timer"""
    start_time = time.time()
    
    result, error = refresh_session(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Session refresh failed: {error}", 500, "SESSION_REFRESH_FAILED", start_time)
    return build_success_response(result, start_time) 