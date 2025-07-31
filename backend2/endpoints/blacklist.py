from flask import Blueprint, request, g
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.blacklist_service import (
    get_blacklist,
    add_device_to_blacklist,
    remove_device_from_blacklist,
    set_blacklist_limit_rate,
    get_blacklist_limit_rate,
    activate_blacklist_mode,
    deactivate_blacklist_mode
)
from services.db_operations.blacklist_db import get_blacklist_mode_setting
import time
from utils.middleware import router_context_required

blacklist_bp = Blueprint('blacklist', __name__)
logger = get_logger('endpoints.blacklist')

@blacklist_bp.route("/devices", methods=["GET"])
@router_context_required
def get_blacklist_route():
    """Get the current list of blacklisted devices with full device information"""
    start_time = time.time()
    result, error = get_blacklist(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    
    # Format response to match frontend expectations
    response_data = {"devices": result or []}
    return build_success_response(response_data, start_time)

@blacklist_bp.route("/add", methods=["POST"])
@router_context_required
def add_to_blacklist_route():
    """Add a device to the blacklist by IP address and update iptables rules"""
    start_time = time.time()
    
    # Enhanced logging for blacklist add flow
    logger.info("🔍 BLACKLIST ADD ENDPOINT - Starting request processing")
    logger.info(f"  - Authenticated user_id: {getattr(g, 'user_id', 'NOT SET')}")
    logger.info(f"  - Router ID: {getattr(g, 'router_id', 'NOT SET')}")
    logger.info(f"  - Session ID: {getattr(g, 'session_id', 'NOT SET')}")
    
    data = request.get_json()
    logger.info(f"  - Request body: {data}")
    
    if not data or 'ip' not in data:
        logger.error("🔍 BLACKLIST ADD - Missing 'ip' in request body")
        return build_error_response("Missing 'ip' in request body", 400, "BAD_REQUEST", start_time)
    
    ip_address = data.get('ip')
    device_name = data.get('name')  # Extract name from request
    description = data.get('description')  # Extract description from request
    logger.info(f"🔍 BLACKLIST ADD - Calling service with IP: {ip_address}, name: {device_name}")
    
    result, error = add_device_to_blacklist(g.user_id, g.router_id, g.session_id, ip_address, device_name, description)
    
    if error:
        logger.error(f"🔍 BLACKLIST ADD - Service returned error: {error}")
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    
    logger.info(f"🔍 BLACKLIST ADD - Success! Result: {result}")
    return build_success_response(result, start_time)

@blacklist_bp.route("/remove", methods=["POST"])
@router_context_required
def remove_from_blacklist_route():
    """Remove a device from the blacklist by IP address and update iptables rules"""
    start_time = time.time()
    data = request.get_json()
    if not data or 'ip' not in data:
        return build_error_response("Missing 'ip' in request body", 400, "BAD_REQUEST", start_time)
    
    ip_address = data.get('ip')
    result, error = remove_device_from_blacklist(g.user_id, g.router_id, g.session_id, ip_address)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@blacklist_bp.route("/limit-rate", methods=["POST"])
@router_context_required
def set_limit_rate_route():
    """Set the bandwidth limit rate for blacklisted devices in limited mode"""
    start_time = time.time()
    data = request.get_json()
    if not data or 'rate' not in data:
        return build_error_response("Missing 'rate' in request body", 400, "BAD_REQUEST", start_time)
    
    bandwidth_rate = data.get('rate')
    result, error = set_blacklist_limit_rate(g.user_id, g.router_id, g.session_id, bandwidth_rate)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@blacklist_bp.route("/limit-rate", methods=["GET"])
@router_context_required
def get_limit_rate_route():
    """Get the current bandwidth limit rate for blacklisted devices in limited mode"""
    start_time = time.time()
    result, error = get_blacklist_limit_rate(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@blacklist_bp.route("/mode", methods=["GET"])
@router_context_required
def get_mode_status_route():
    """Get blacklist mode status"""
    start_time = time.time()
    is_active, error = get_blacklist_mode_setting(g.user_id, g.router_id)
    if error:
        return build_error_response(f"Failed to get mode status: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response({"active": is_active}, start_time)

@blacklist_bp.route("/mode", methods=["POST"])
@router_context_required
def activate_mode_route():
    """Activate blacklist mode where only blacklisted devices get limited access"""
    start_time = time.time()
    result, error = activate_blacklist_mode(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@blacklist_bp.route("/mode", methods=["DELETE"])
@router_context_required
def deactivate_mode_route():
    """Deactivate blacklist mode and return to normal network access"""
    start_time = time.time()
    result, error = deactivate_blacklist_mode(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)
