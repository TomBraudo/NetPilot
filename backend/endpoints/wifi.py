from flask import Blueprint, request, jsonify
from services.wifi_manager import enable_wifi, change_wifi_password, get_wifi_status
from utils.response_helpers import error

wifi_bp = Blueprint('wifi', __name__)

'''
    API endpoint to enable WiFi on the router
'''
@wifi_bp.route("/wifi/enable", methods=["POST"])
def enable_wifi_route():
    return jsonify(enable_wifi())

'''
    API endpoint to change the WiFi password
    Expects JSON: { "password": "<new_password>", "interface": <interface_number> }
'''
@wifi_bp.route("/wifi/change_password", methods=["POST"])
def change_wifi_password_route():
    data = request.get_json()
    password = data.get("password")
    interface = data.get("interface", 0)  # Default to interface 0
    
    if not password:
        return jsonify(error("Missing 'password' in request body"))
        
    return jsonify(change_wifi_password(password, interface))

'''
    API endpoint to get current WiFi status
'''
@wifi_bp.route("/wifi/status", methods=["GET"])
def get_wifi_status_route():
    return jsonify(get_wifi_status())