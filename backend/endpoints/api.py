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

network_bp = Blueprint('network', __name__)
logger = get_logger('endpoints.network')

@network_bp.route("/blocked", methods=["GET"])
def get_blocked():
    """Get all currently blocked devices"""
    start_time = time.time()
    try:
        result, error = get_blocked_devices_list()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error getting blocked devices: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error getting blocked devices: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@network_bp.route("/block", methods=["POST"])
def block():
    """Block a device by IP address"""
    start_time = time.time()
    try:
        data = request.get_json()
        ip = data.get("ip")
        if not ip:
            return build_error_response("Missing 'ip' in request body", 400, "BAD_REQUEST", start_time)
        
        result, error = block_device(ip)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error blocking device: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error blocking device: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@network_bp.route("/unblock", methods=["POST"])
def unblock():
    """Unblock a device by IP address"""
    start_time = time.time()
    try:
        data = request.get_json()
        ip = data.get("ip")
        if not ip:
            return build_error_response("Missing 'ip' in request body", 400, "BAD_REQUEST", start_time)
        
        result, error = unblock_device(ip)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error unblocking device: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error unblocking device: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@network_bp.route("/reset", methods=["POST"])
def reset():
    """Reset all network rules"""
    start_time = time.time()
    try:
        result, error = reset_network_rules()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error resetting network rules: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error resetting network rules: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

@network_bp.route("/scan", methods=["GET"])
def scan_router():
    """Scan the network via router"""
    start_time = time.time()
    try:
        result, error = scan_network_via_router()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error scanning network via router: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error scanning network via router: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)