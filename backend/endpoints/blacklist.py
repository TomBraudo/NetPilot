from flask import Blueprint, request
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.blacklist_service import (
    get_blacklist_devices,
    add_device_to_blacklist,
    remove_device_from_blacklist,
    set_blacklist_limit_rate,
    clear_blacklist,
    is_blacklist_mode,
    activate_blacklist_mode,
    deactivate_blacklist_mode,
)
import time

blacklist_bp = Blueprint('blacklist', __name__)
logger = get_logger('blacklist.endpoints')

@blacklist_bp.route("/blacklist", methods=["GET"])
def get_blacklist():
    """Get all devices in the blacklist"""
    start_time = time.time()
    try:
        result, error = get_blacklist_devices()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error getting blacklist: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error getting blacklist: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@blacklist_bp.route("/blacklist", methods=["POST"])
def add_to_blacklist():
    """Add a device to the blacklist"""
    start_time = time.time()
    try:
        data = request.get_json()
        ip = data.get("ip")
        if not ip:
            return build_error_response("Missing 'ip' in request body", 400, "BAD_REQUEST", start_time)
            
        result, error = add_device_to_blacklist(ip)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error adding to blacklist: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error adding to blacklist: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@blacklist_bp.route("/blacklist", methods=["DELETE"])
def remove_from_blacklist():
    """Remove a device from the blacklist"""
    start_time = time.time()
    try:
        data = request.get_json()
        ip = data.get("ip")
        if not ip:
            return build_error_response("Missing 'ip' in request body", 400, "BAD_REQUEST", start_time)
            
        result, error = remove_device_from_blacklist(ip)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error removing from blacklist: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error removing from blacklist: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@blacklist_bp.route("/blacklist/limit-rate", methods=["POST"])
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

@blacklist_bp.route("/blacklist/clear", methods=["POST"])
def clear_blacklist_route():
    """Clear all devices from the blacklist"""
    start_time = time.time()
    try:
        result, error = clear_blacklist()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error clearing blacklist: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error clearing blacklist: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@blacklist_bp.route("/blacklist/mode", methods=["GET"])
def get_mode():
    """Get the current blacklist mode status"""
    start_time = time.time()
    try:
        result, error = is_blacklist_mode()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error getting blacklist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error getting blacklist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@blacklist_bp.route("/blacklist/mode", methods=["POST"])
def activate():
    """Activate blacklist mode"""
    start_time = time.time()
    try:
        result, error = activate_blacklist_mode()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error activating blacklist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error activating blacklist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@blacklist_bp.route("/blacklist/mode", methods=["DELETE"])
def deactivate():
    """Deactivate blacklist mode"""
    start_time = time.time()
    try:
        result, error = deactivate_blacklist_mode()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error deactivating blacklist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error deactivating blacklist mode: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time) 