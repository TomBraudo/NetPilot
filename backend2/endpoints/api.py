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

@network_bp.route("/session/start", methods=["POST", "OPTIONS"])
@router_context_required
def start_session_endpoint():
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        logger.info("=== Session Start OPTIONS (CORS preflight) ===")
        from flask import make_response
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    start_time = time.time()
    logger.info("=== Session Start Endpoint Called ===")
    
    # Get parameters from request
    data = request.get_json()
    restart = data.get("restart", False)
    
    logger.info(f"Session start parameters: user_id={g.user_id}, router_id={g.router_id}, restart={restart}")
    
    # Call the session service
    result, error = start_session(g.router_id, None, restart)
    
    if error:
        logger.error(f"Session start error: {error}")
        return build_error_response(error, 500, "SESSION_START_FAILED", start_time)
    
    logger.info(f"Session start successful: {result}")
    return build_success_response(result, start_time)

@network_bp.route("/session/end", methods=["POST", "OPTIONS"])
def end_session():
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        logger.info("=== Session End OPTIONS (CORS preflight) ===")
        from flask import make_response
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Check authentication manually
    if not hasattr(g, 'user_id') or not g.user_id:
        from flask import session as flask_session
        if 'user_id' not in flask_session:
            return build_error_response("User authentication required", 401, "UNAUTHENTICATED", 0)
        g.user_id = flask_session.get('user_id')
    
    start_time = time.time()
    logger.info("=== Session End Endpoint Called ===")
    
    user_id = g.user_id  # Get from authenticated user
    data = request.get_json()
    router_id = data.get("routerId")
    
    logger.info(f"Session end parameters: user_id={user_id}, router_id={router_id}")
    
    # Use user_id as session_id (consistent with middleware approach)
    session_id = str(user_id)
    
    payload = {
        "routerId": router_id,
        "sessionId": session_id
    }
    
    logger.info(f"Calling commands server with payload: {payload}")
    
    # FIX: Use correct method - execute_router_command instead of non-existent send_request
    response, error = commands_server_manager.execute_router_command(
        router_id=router_id,
        session_id=session_id,
        endpoint="/session/end",
        method="POST",
        body=payload
    )
    
    if error:
        logger.error(f"Commands server error: {error}")
        return build_error_response(error, 500, "SESSION_END_FAILED", start_time)
    
    if response and response.get("message"):
        logger.info(f"Session end successful: {response}")
        return build_success_response({"message": response["message"]}, start_time)
    else:
        logger.error(f"Unexpected response format: {response}")
        return build_error_response("Session end failed", 500, "SESSION_END_FAILED", start_time)

@network_bp.route("/session/refresh", methods=["POST", "OPTIONS"])
def refresh_session():
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        logger.info("=== Session Refresh OPTIONS (CORS preflight) ===")
        from flask import make_response
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Check authentication manually
    if not hasattr(g, 'user_id') or not g.user_id:
        from flask import session as flask_session
        if 'user_id' not in flask_session:
            return build_error_response("User authentication required", 401, "UNAUTHENTICATED", 0)
        g.user_id = flask_session.get('user_id')
    
    start_time = time.time()
    logger.info("=== Session Refresh Endpoint Called ===")
    
    user_id = g.user_id  # Get from authenticated user
    
    logger.info(f"Session refresh parameters: user_id={user_id}")
    
    # Use user_id as session_id (consistent with middleware approach)
    session_id = str(user_id)
    
    # For refresh, we need a router_id - get from request or use a placeholder
    # Note: Refresh might not need router_id depending on commands server implementation
    payload = {"sessionId": session_id}
    
    logger.info(f"Calling commands server with payload: {payload}")
    
    # FIX: Use correct method - send_direct_command for refresh (might not need router context)
    response, error = commands_server_manager.send_direct_command(
        endpoint="/session/refresh",
        method="POST",
        payload=payload
    )
    
    if error:
        logger.error(f"Commands server error: {error}")
        return build_error_response(error, 500, "SESSION_REFRESH_FAILED", start_time)
    
    if response and response.get("message"):
        logger.info(f"Session refresh successful: {response}")
        return build_success_response({"message": response["message"]}, start_time)
    else:
        logger.error(f"Unexpected response format: {response}")
        return build_error_response("Session refresh failed", 500, "SESSION_REFRESH_FAILED", start_time)

@network_bp.route("/session/status", methods=["GET", "OPTIONS"])
def session_status():
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        logger.info("=== Session Status OPTIONS (CORS preflight) ===")
        from flask import make_response
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Check authentication manually
    if not hasattr(g, 'user_id') or not g.user_id:
        from flask import session as flask_session
        if 'user_id' not in flask_session:
            return build_error_response("User authentication required", 401, "UNAUTHENTICATED", 0)
        g.user_id = flask_session.get('user_id')
    
    start_time = time.time()
    logger.info("=== Session Status Endpoint Called ===")
    
    # Note: This endpoint gets general session status, not user-specific
    logger.info("Calling commands server for session status")
    
    # FIX: Use correct method - send_direct_command for status (general endpoint)
    response, error = commands_server_manager.send_direct_command(
        endpoint="/session/status",
        method="GET"
    )
    
    if error:
        logger.error(f"Commands server error: {error}")
        return build_error_response(error, 500, "SESSION_STATUS_FAILED", start_time)
    
    if response and response.get("sessions"):
        logger.info(f"Session status successful: {response}")
        return build_success_response({
            "message": response.get("message"),
            "sessions": response["sessions"]
        }, start_time)
    else:
        logger.error(f"Unexpected response format: {response}")
        return build_error_response("Session status fetch failed", 500, "SESSION_STATUS_FAILED", start_time) 

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