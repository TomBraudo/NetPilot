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
from utils.command_server_proxy import command_server_health_check
import uuid
from flask import request
from utils.command_server_proxy import send_command_server_request

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
    """Proxy health check to Command Server"""
    import time
    start_time = time.time()
    response = command_server_health_check()
    if response.get("success") is False:
        return build_error_response(f"Command Server health check failed: {response.get('error')}", 502, "COMMAND_SERVER_UNHEALTHY", start_time)
    # Return only the inner data
    return build_success_response(response.get("data"), start_time) 

@network_bp.route("/session/start", methods=["POST"])
def start_session():
    data = request.get_json()
    router_id = data.get("routerId")
    session_id = data.get("sessionId") or str(uuid.uuid4())
    restart = data.get("restart", False)
    # TODO: Validate user and router_id as needed
    payload = {
        "sessionId": session_id,
        "routerId": router_id,
        "restart": restart
    }
    response = send_command_server_request("/start", method="POST", payload=payload)
    if response.get("session_id"):
        return build_success_response({
            "sessionId": response["session_id"],
            "routerReachable": response.get("router_reachable"),
            "infrastructureReady": response.get("infrastructure_ready"),
            "message": response.get("message")
        })
    else:
        return build_error_response(response.get("error", "Session start failed"), 400)

@network_bp.route("/session/end", methods=["POST"])
def end_session():
    data = request.get_json()
    session_id = data.get("sessionId")
    router_id = data.get("routerId")
    payload = {
        "sessionId": session_id,
        "routerId": router_id
    }
    response = send_command_server_request("/end", method="POST", payload=payload)
    if response.get("message"):
        return build_success_response({"message": response["message"]})
    else:
        return build_error_response(response.get("error", "Session end failed"), 400)

@network_bp.route("/session/refresh", methods=["POST"])
def refresh_session():
    data = request.get_json()
    session_id = data.get("sessionId")
    payload = {"sessionId": session_id}
    response = send_command_server_request("/refresh", method="POST", payload=payload)
    if response.get("message"):
        return build_success_response({"message": response["message"]})
    else:
        return build_error_response(response.get("error", "Session refresh failed"), 400)

@network_bp.route("/session/status", methods=["GET"])
def session_status():
    response = send_command_server_request("/status", method="GET")
    if response.get("sessions"):
        return build_success_response({
            "message": response.get("message"),
            "sessions": response["sessions"]
        })
    else:
        return build_error_response(response.get("error", "Session status fetch failed"), 400) 