from flask import Blueprint, request, jsonify
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.wifi_management import (
    enable_wifi,
    change_wifi_password,
    get_wifi_status,
    get_wifi_ssid,
    change_wifi_ssid,
)
import time
from utils.middleware import router_context_required

# Get logger for wifi endpoints
logger = get_logger('wifi.endpoints')

wifi_bp = Blueprint('wifi', __name__)

'''
    API endpoint to enable WiFi on the router
'''
@wifi_bp.route("/enable", methods=["POST"])
@router_context_required
def enable_wifi_route():
    """Enable WiFi on the router"""
    start_time = time.time()
    result, error = enable_wifi()
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

'''
    API endpoint to change the WiFi password
    Expects JSON: { "password": "<new_password>", "interface": <interface_number> }
'''
@wifi_bp.route("/password", methods=["POST"])
@router_context_required
def change_password():
    """Change the WiFi password"""
    start_time = time.time()
    data = request.get_json()
    password = data.get("password")
    if not password:
        return build_error_response("Missing 'password' in request body", 400, "BAD_REQUEST", start_time)
    
    result, error = change_wifi_password(password)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

'''
    API endpoint to get current WiFi status
'''
@wifi_bp.route("/status", methods=["GET"])
@router_context_required
def get_status():
    """Get the current WiFi status"""
    start_time = time.time()
    result, error = get_wifi_status()
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

'''
    API endpoint to get the current WiFi SSID
    Optional query param: interface (defaults to 0)
'''
@wifi_bp.route("/ssid", methods=["GET"])
@router_context_required
def get_wifi_ssid_route():
    """Get the current WiFi SSID"""
    start_time = time.time()
    interface = request.args.get("interface", 0, type=int)
    result, error = get_wifi_ssid(interface)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

'''
    API endpoint to change the WiFi SSID
    Expects JSON: { "ssid": "<new_ssid>", "interface": <interface_number> }
'''
@wifi_bp.route("/ssid", methods=["POST"])
@router_context_required
def change_ssid():
    """Change the WiFi SSID"""
    start_time = time.time()
    data = request.get_json()
    ssid = data.get("ssid")
    
    if not ssid:
        return build_error_response("Missing 'ssid' in request body", 400, "BAD_REQUEST", start_time)
    
    result, error = change_wifi_ssid(ssid)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@wifi_bp.route("/disable", methods=["POST"])
@router_context_required
def disable_wifi_route():
    """Disable WiFi on the router"""
    start_time = time.time()
    # In the new implementation, there is no separate 'disable' function.
    # We will need to add one to the service layer. For now, return 'not implemented'.
    return build_error_response("Disabling WiFi is not currently supported.", 501, "NOT_IMPLEMENTED", start_time)