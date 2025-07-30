from flask import Blueprint, request
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.network_service import (
    get_blocked_devices_list,
    block_device,
    unblock_device,
    reset_network_rules,
    scan_network_via_router,
)
import time
from utils.middleware import router_context_required
from managers.commands_server_manager import commands_server_manager
from flask import request
from flask import g
from models.router import UserRouter
from models.user import User
from auth import login_required
from services.session_service import start_session

network_bp = Blueprint('network', __name__)
logger = get_logger('endpoints.network')

@network_bp.route("/blocked", methods=["GET"])
@router_context_required
def get_blocked():
    """Get all currently blocked devices"""
    start_time = time.time()
    result, error = get_blocked_devices_list()
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@network_bp.route("/block", methods=["POST"])
@router_context_required
def block():
    """Block a device by IP address"""
    start_time = time.time()
    data = request.get_json()
    ip = data.get("ip")
    if not ip:
        return build_error_response("Missing 'ip' in request body", 400, "BAD_REQUEST", start_time)
    
    result, error = block_device(ip)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@network_bp.route("/unblock", methods=["POST"])
@router_context_required
def unblock():
    """Unblock a device by IP address"""
    start_time = time.time()
    data = request.get_json()
    ip = data.get("ip")
    if not ip:
        return build_error_response("Missing 'ip' in request body", 400, "BAD_REQUEST", start_time)
    
    result, error = unblock_device(ip)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@network_bp.route("/reset", methods=["POST"])
@router_context_required
def reset():
    """Reset all network rules"""
    start_time = time.time()
    result, error = reset_network_rules()
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@network_bp.route("/scan", methods=["GET"])
@router_context_required
def scan_router():
    """Scan the network via router"""
    start_time = time.time()
    from flask import g
    result, error = scan_network_via_router(g.router_id)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time) 

@network_bp.route("/command-server/health", methods=["GET"])
def command_server_health():
    """Health check to Command Server using new manager"""
    import time
    start_time = time.time()
    response, error = commands_server_manager.is_connected(), None
    if not response:
        return build_error_response(f"Command Server health check failed", 502, "COMMAND_SERVER_UNHEALTHY", start_time)
    # Optionally, get more info
    # info, info_error = commands_server_manager.get_server_info()
    # if info_error:
    #     return build_error_response(f"Command Server info failed: {info_error}", 502, "COMMAND_SERVER_UNHEALTHY", start_time)
    return build_success_response({"connected": True}, start_time) 


@network_bp.route("/router-id", methods=["POST"])
def save_router_id():
    """Save (create or update) the routerId for the current user"""
    session = g.db_session
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        return build_error_response("User not authenticated", 401)
    data = request.get_json()
    router_id = data.get("routerId")
    if not router_id:
        return build_error_response("Missing 'routerId' in request body", 400)
    try:
        # Check if router already exists for this user
        user_router = session.query(UserRouter).filter_by(user_id=user_id, router_id=router_id).first()
        if not user_router:
            # Create new router association
            user_router = UserRouter(user_id=user_id, router_id=router_id, is_active=True)
            session.add(user_router)
        else:
            # Update existing router (could update last_seen, is_active, etc.)
            user_router.is_active = True
        session.commit()
        return build_success_response({"routerId": router_id, "message": "RouterId saved"})
    except Exception as e:
        session.rollback()
        return build_error_response(f"Failed to save routerId: {str(e)}", 500) 

@network_bp.route("/router-id", methods=["GET"])
def get_router_id():
    """Get the routerId for the current user (if any)"""
    session = g.db_session
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        return build_error_response("User not authenticated", 401)
    try:
        user_router = session.query(UserRouter).filter_by(user_id=user_id, is_active=True).first()
        if user_router:
            return build_success_response({"routerId": user_router.router_id})
        else:
            return build_error_response("No routerId found for user", 404)
    except Exception as e:
        return build_error_response(f"Failed to fetch routerId: {str(e)}", 500) 