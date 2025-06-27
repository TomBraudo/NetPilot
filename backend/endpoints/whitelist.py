from flask import Blueprint, request
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.whitelist_service import (
    get_whitelist,
    add_to_whitelist,
    remove_from_whitelist,
    set_whitelist_limit_rate,
    clear_whitelist,
    is_whitelist_mode,
    activate_whitelist_mode,
    deactivate_whitelist_mode,
)
import time
from utils.middleware import router_context_required

whitelist_bp = Blueprint('whitelist', __name__)
logger = get_logger('endpoints.whitelist')

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
    """Add a device to the whitelist"""
    start_time = time.time()
    data = request.get_json()
    if not data or 'ip' not in data:
        return build_error_response("Missing 'ip' in request body", 400, "BAD_REQUEST", start_time)
    
    result, error = add_to_whitelist(data['ip'], data.get('mac'), data.get('device_name'))
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@whitelist_bp.route("/remove", methods=["POST"])
@router_context_required
def remove_from_whitelist_route():
    """Remove a device from the whitelist"""
    start_time = time.time()
    data = request.get_json()
    if not data or 'ip' not in data:
        return build_error_response("Missing 'ip' in request body", 400, "BAD_REQUEST", start_time)

    result, error = remove_from_whitelist(data['ip'])
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@whitelist_bp.route("/whitelist/limit-rate", methods=["POST"])
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

@whitelist_bp.route("/whitelist/clear", methods=["POST"])
def clear_whitelist_route():
    """Clear all devices from the whitelist"""
    start_time = time.time()
    try:
        result, error = clear_whitelist()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error clearing whitelist: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error clearing whitelist: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@whitelist_bp.route("/whitelist/mode", methods=["GET"])
def get_mode():
    """Get the current whitelist mode status"""
    start_time = time.time()
    try:
        result, error = is_whitelist_mode()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error getting whitelist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error getting whitelist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@whitelist_bp.route("/whitelist/mode", methods=["POST"])
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

@whitelist_bp.route("/whitelist/mode", methods=["DELETE"])
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


