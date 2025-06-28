from flask import Blueprint, request
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.blacklist_service import (
    add_device_to_blacklist,
    remove_device_from_blacklist,
    set_blacklist_limit_rate,
    activate_blacklist_mode,
    deactivate_blacklist_mode,
)
import time
from utils.middleware import router_context_required
from managers.router_connection_manager import RouterConnectionManager

blacklist_bp = Blueprint('blacklist', __name__)
logger = get_logger('endpoints.blacklist')
router_connection_manager = RouterConnectionManager()

@blacklist_bp.route("/add", methods=["POST"])
@router_context_required
def add_to_blacklist_route():
    """Add a device to the blacklist by its MAC address."""
    start_time = time.time()
    data = request.get_json()
    mac = data.get('mac')

    if not mac:
        return build_error_response("Missing 'mac' in request body", 400, "BAD_REQUEST", start_time)

    result, error = add_device_to_blacklist(mac)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@blacklist_bp.route("/remove", methods=["POST"])
@router_context_required
def remove_from_blacklist_route():
    """Remove a device from the blacklist by its MAC address."""
    start_time = time.time()
    data = request.get_json()
    mac = data.get('mac')

    if not mac:
        return build_error_response("Missing 'mac' in request body", 400, "BAD_REQUEST", start_time)

    result, error = remove_device_from_blacklist(mac)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@blacklist_bp.route("/limit-rate", methods=["POST"])
@router_context_required
def set_limit_rate():
    """Set the blacklist bandwidth limit rate"""
    start_time = time.time()
    try:
        data = request.get_json()
        rate = data.get("rate")
        if not rate:
            return build_error_response("Missing 'rate' in request body", 400, "BAD_REQUEST", start_time)
            
        result, error = set_blacklist_limit_rate(rate)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error setting blacklist limit rate: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@blacklist_bp.route("/mode/activate", methods=["POST"])
@router_context_required
def activate():
    """Activate blacklist mode"""
    start_time = time.time()
    try:
        result, error = activate_blacklist_mode()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error activating blacklist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@blacklist_bp.route("/mode/deactivate", methods=["POST"])
@router_context_required
def deactivate():
    """Deactivate blacklist mode"""
    start_time = time.time()
    try:
        result, error = deactivate_blacklist_mode()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error deactivating blacklist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time) 