from flask import Blueprint, request
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.whitelist_service import (
    add_device_to_whitelist,
    remove_device_from_whitelist,
    set_whitelist_limit_rate,
    activate_whitelist_mode,
    deactivate_whitelist_mode,
)
import time
from utils.middleware import router_context_required
from managers.router_connection_manager import RouterConnectionManager

whitelist_bp = Blueprint('whitelist', __name__)
logger = get_logger('endpoints.whitelist')
router_connection_manager = RouterConnectionManager()

@whitelist_bp.route("/", methods=["GET"])
@router_context_required
def get_whitelist_route():
    """Get the current whitelist"""
    start_time = time.time()
    result, error = get_whitelist()
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@whitelist_bp.route("/add", methods=["POST"])
@router_context_required
def add_to_whitelist_route():
    """Add a device to the whitelist by its MAC address."""
    start_time = time.time()
    data = request.get_json()
    mac = data.get('mac')

    if not mac:
        return build_error_response("Missing 'mac' in request body", 400, "BAD_REQUEST", start_time)

    result, error = add_device_to_whitelist(mac)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@whitelist_bp.route("/remove", methods=["POST"])
@router_context_required
def remove_from_whitelist_route():
    """Remove a device from the whitelist by its MAC address."""
    start_time = time.time()
    data = request.get_json()
    mac = data.get('mac')

    if not mac:
        return build_error_response("Missing 'mac' in request body", 400, "BAD_REQUEST", start_time)

    result, error = remove_device_from_whitelist(mac)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@whitelist_bp.route("/limit-rate", methods=["POST"])
@router_context_required
def set_limit_rate():
    """Set the whitelist bandwidth limit rate"""
    start_time = time.time()
    try:
        data = request.get_json()
        rate = data.get("rate")
        if not rate:
            return build_error_response("Missing 'rate' in request body", 400, "BAD_REQUEST", start_time)
            
        result, error = set_whitelist_limit_rate(rate)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error setting whitelist limit rate: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error setting whitelist limit rate: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@whitelist_bp.route("/mode/activate", methods=["POST"])
@router_context_required
def activate():
    """Activate whitelist mode"""
    start_time = time.time()
    try:
        result, error = activate_whitelist_mode()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error activating whitelist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error activating whitelist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@whitelist_bp.route("/mode/deactivate", methods=["DELETE"])
@router_context_required
def deactivate():
    """Deactivate whitelist mode"""
    start_time = time.time()
    try:
        result, error = deactivate_whitelist_mode()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error deactivating whitelist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error deactivating whitelist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


