from flask import Blueprint, request, jsonify
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.wifi_management import (
    enable_wifi,
    change_wifi_password,
    get_wifi_status,
    get_wifi_ssid,
    change_wifi_ssid
)
import time

# Get logger for wifi endpoints
logger = get_logger('wifi.endpoints')

wifi_bp = Blueprint('wifi', __name__)

'''
    API endpoint to enable WiFi on the router
'''
@wifi_bp.route("/wifi/enable", methods=["POST"])
def enable_wifi_route():
    """Enable WiFi on the router"""
    start_time = time.time()
    try:
        result, error = enable_wifi()
        if error:
            # Command execution returned an error string
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error enabling WiFi: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error enabling WiFi: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

'''
    API endpoint to change the WiFi password
    Expects JSON: { "password": "<new_password>", "interface": <interface_number> }
'''
@wifi_bp.route("/wifi/password", methods=["POST"])
def change_password():
    """Change the WiFi password"""
    start_time = time.time()
    try:
        data = request.get_json()
        password = data.get("password")
        if not password:
            return build_error_response("Missing 'password' in request body", 400, "BAD_REQUEST", start_time)
            
        result, error = change_wifi_password(password)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error changing WiFi password: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Error changing WiFi password: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

'''
    API endpoint to get current WiFi status
'''
@wifi_bp.route("/wifi/status", methods=["GET"])
def get_status():
    """Get the current WiFi status"""
    start_time = time.time()
    try:
        result, error = get_wifi_status()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error getting WiFi status: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error getting WiFi status: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

'''
    API endpoint to get the current WiFi SSID
    Optional query param: interface (defaults to 0)
'''
@wifi_bp.route("/wifi/ssid", methods=["GET"])
def get_wifi_ssid_route():
    """Get the current WiFi SSID"""
    start_time = time.time()
    try:
        interface = request.args.get("interface", 0, type=int)
        result, error = get_wifi_ssid(interface)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error getting WiFi SSID: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Error getting WiFi SSID: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)

'''
    API endpoint to change the WiFi SSID
    Expects JSON: { "ssid": "<new_ssid>", "interface": <interface_number> }
'''
@wifi_bp.route("/wifi/ssid", methods=["POST"])
def change_ssid():
    """Change the WiFi SSID"""
    start_time = time.time()
    try:
        data = request.get_json()
        ssid = data.get("ssid")
        
        if not ssid:
            return build_error_response("Missing 'ssid' in request body", 400, "BAD_REQUEST", start_time)
            
        result, error = change_wifi_ssid(ssid)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except RuntimeError as e:
        logger.error(f"Error changing WiFi SSID: {str(e)}", exc_info=True)
        return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
    except Exception as e:
        logger.error(f"Unexpected error changing WiFi SSID: {str(e)}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)