from flask import Blueprint, request, jsonify
from utils.logging_config import get_logger
from utils.response_helpers import error
from services.wifi_management import (
    enable_wifi,
    change_wifi_password,
    get_wifi_status,
    get_wifi_ssid,
    change_wifi_ssid
)

# Get logger for wifi endpoints
logger = get_logger('wifi.endpoints')

wifi_bp = Blueprint('wifi', __name__)

'''
    API endpoint to enable WiFi on the router
'''
@wifi_bp.route("/wifi/enable", methods=["POST"])
def enable_wifi_route():
    """Enable WiFi on the router"""
    try:
        result = enable_wifi()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error enabling WiFi: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

'''
    API endpoint to change the WiFi password
    Expects JSON: { "password": "<new_password>", "interface": <interface_number> }
'''
@wifi_bp.route("/wifi/password", methods=["POST"])
def change_password():
    """Change the WiFi password"""
    try:
        data = request.get_json()
        password = data.get("password")
        if not password:
            return jsonify(error("Missing 'password' in request body", status_code=400))
            
        result = change_wifi_password(password)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error changing WiFi password: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

'''
    API endpoint to get current WiFi status
'''
@wifi_bp.route("/wifi/status", methods=["GET"])
def get_status():
    """Get the current WiFi status"""
    try:
        result = get_wifi_status()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting WiFi status: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

'''
    API endpoint to get the current WiFi SSID
    Optional query param: interface (defaults to 0)
'''
@wifi_bp.route("/wifi/ssid", methods=["GET"])
def get_wifi_ssid_route():
    """Get the current WiFi SSID"""
    try:
        interface = request.args.get("interface", 0, type=int)
        result = get_wifi_ssid(interface)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting WiFi SSID: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

'''
    API endpoint to change the WiFi SSID
    Expects JSON: { "ssid": "<new_ssid>", "interface": <interface_number> }
'''
@wifi_bp.route("/wifi/ssid", methods=["POST"])
def change_ssid():
    """Change the WiFi SSID"""
    try:
        data = request.get_json()
        ssid = data.get("ssid")
        interface = data.get("interface", 0)
        
        if not ssid:
            return jsonify(error("Missing 'ssid' in request body", status_code=400))
            
        result = change_wifi_ssid(ssid, interface)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error changing WiFi SSID: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))