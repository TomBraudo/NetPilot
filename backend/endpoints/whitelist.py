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

def _get_mac_from_ip(ip):
    """Helper to get MAC address from an IP via the router's ARP table."""
    if not ip:
        return None, "IP address is required"
    arp_cmd = f"arp -n | grep '{ip}' | awk '{{print $3}}'"
    mac, err = router_connection_manager.execute(arp_cmd)
    if err or not mac:
        return None, f"Could not find MAC for IP {ip}"
    return mac.strip(), None

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
    
    mac, err = _get_mac_from_ip(data['ip'])
    if err:
        return build_error_response(err, 404, "MAC_NOT_FOUND", start_time)

    result, error = add_device_to_whitelist(mac)
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

    mac, err = _get_mac_from_ip(data['ip'])
    if err:
        return build_error_response(err, 404, "MAC_NOT_FOUND", start_time)

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


