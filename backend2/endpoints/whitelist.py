from flask import Blueprint, request, g
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.whitelist_service import (
    get_whitelist,
    add_device_to_whitelist,
    remove_device_from_whitelist,
    set_whitelist_limit_rate,
    get_whitelist_limit_rate,
    activate_whitelist_mode,
    deactivate_whitelist_mode
)
from services.db_operations.whitelist_db import get_whitelist_mode_setting
import time
from utils.middleware import router_context_required

whitelist_bp = Blueprint('whitelist', __name__)
logger = get_logger('endpoints.whitelist')

@whitelist_bp.route("/", methods=["GET"])
@router_context_required
def get_whitelist_route():
    """Get the current list of whitelisted device IP addresses"""
    start_time = time.time()
    result, error = get_whitelist(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@whitelist_bp.route("/add", methods=["POST"])
@router_context_required
def add_to_whitelist_route():
    """Add a device to the whitelist by IP address and update iptables rules"""
    start_time = time.time()
    
    # Enhanced logging for whitelist add flow
    logger.info("🔍 WHITELIST ADD ENDPOINT - Starting request processing")
    logger.info(f"  - Authenticated user_id: {getattr(g, 'user_id', 'NOT SET')}")
    logger.info(f"  - Router ID: {getattr(g, 'router_id', 'NOT SET')}")
    logger.info(f"  - Session ID: {getattr(g, 'session_id', 'NOT SET')}")
    
    data = request.get_json()
    logger.info(f"  - Request body: {data}")
    
    if not data or 'ip' not in data:
        logger.error("🔍 WHITELIST ADD - Missing 'ip' in request body")
        return build_error_response("Missing 'ip' in request body", 400, "BAD_REQUEST", start_time)
    
    ip_address = data.get('ip')
    logger.info(f"🔍 WHITELIST ADD - Calling service with IP: {ip_address}")
    
    result, error = add_device_to_whitelist(g.user_id, g.router_id, g.session_id, ip_address)
    
    if error:
        logger.error(f"🔍 WHITELIST ADD - Service returned error: {error}")
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    
    logger.info(f"🔍 WHITELIST ADD - Success! Result: {result}")
    return build_success_response(result, start_time)

@whitelist_bp.route("/remove", methods=["POST"])
@router_context_required
def remove_from_whitelist_route():
    """Remove a device from the whitelist by IP address and update iptables rules"""
    start_time = time.time()
    data = request.get_json()
    if not data or 'ip' not in data:
        return build_error_response("Missing 'ip' in request body", 400, "BAD_REQUEST", start_time)
    
    ip_address = data.get('ip')
    result, error = remove_device_from_whitelist(g.user_id, g.router_id, g.session_id, ip_address)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@whitelist_bp.route("/limit-rate", methods=["POST"])
@router_context_required
def set_limit_rate_route():
    """Set the bandwidth limit rate for whitelisted devices in limited mode"""
    start_time = time.time()
    data = request.get_json()
    if not data or 'rate' not in data:
        return build_error_response("Missing 'rate' in request body", 400, "BAD_REQUEST", start_time)
    
    bandwidth_rate = data.get('rate')
    result, error = set_whitelist_limit_rate(g.user_id, g.router_id, g.session_id, bandwidth_rate)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@whitelist_bp.route("/limit-rate", methods=["GET"])
@router_context_required
def get_limit_rate_route():
    """Get the current bandwidth limit rate for whitelisted devices in limited mode"""
    start_time = time.time()
    result, error = get_whitelist_limit_rate(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@whitelist_bp.route("/mode", methods=["GET"])
@router_context_required
def get_mode_status_route():
    """Get whitelist mode status"""
    start_time = time.time()
    is_active, error = get_whitelist_mode_setting(g.user_id, g.router_id)
    if error:
        return build_error_response(f"Failed to get mode status: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response({"active": is_active}, start_time)

@whitelist_bp.route("/mode", methods=["POST"])
@router_context_required
def activate_mode_route():
    """Activate whitelist mode where only whitelisted devices get unlimited access"""
    start_time = time.time()
    result, error = activate_whitelist_mode(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@whitelist_bp.route("/mode", methods=["DELETE"])
@router_context_required
def deactivate_mode_route():
    """Deactivate whitelist mode and return to normal network access"""
    start_time = time.time()
    result, error = deactivate_whitelist_mode(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)