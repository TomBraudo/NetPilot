from flask import Blueprint, request, jsonify
from services.device_protection import protect_device
from db.device_repository import get_protected_devices
from utils.response_helpers import success, error

protection_bp = Blueprint('protection', __name__)

'''
    API endpoint to mark a device as protected or unprotected
    Expects JSON: {
        "mac": "string",
        "protected": boolean  # Optional, defaults to true
    }
'''
@protection_bp.route("/api/devices/protect", methods=["POST"])
def protect_device_route():
    data = request.get_json()
    
    if not data:
        return jsonify(error("Missing request body"))
        
    mac = data.get("mac")
    protected = data.get("protected", True)
    
    if not mac:
        return jsonify(error("Missing 'mac' in request body"))
        
    return jsonify(protect_device(mac, protected))

'''
    API endpoint to get all protected devices
'''
@protection_bp.route("/api/devices/protected", methods=["GET"])
def get_protected_devices_route():
    devices = get_protected_devices()
    formatted_devices = []
    
    for device in devices:
        formatted_devices.append({
            "mac": device.get('mac', ''),
            "ip": device.get('ip', ''),
            "hostname": device.get('hostname', ''),
            "device_name": device.get('device_name', '')
        })
    
    return jsonify(success(data=formatted_devices)) 