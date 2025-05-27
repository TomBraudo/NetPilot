from flask import Blueprint, request, jsonify
from utils.logging_config import get_logger
from utils.response_helpers import error
from db.device_repository import (
    get_all_devices,
    get_device_by_mac,
    update_device_name,
    clear_devices
)

# Get logger for db endpoints
logger = get_logger('db.endpoints')

db_bp = Blueprint('database', __name__)

''' 
    API endpoint to retrieve all devices from the database.
'''
@db_bp.route("/db/devices", methods=["GET"])
def get_devices():
    """Get all devices from the database."""
    try:
        result = get_all_devices()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting devices: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@db_bp.route("/db/devices/<mac>", methods=["GET"])
def get_device(mac):
    """Get a specific device by MAC address."""
    try:
        result = get_device_by_mac(mac)
        if not result:
            return jsonify(error("Device not found", status_code=404))
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting device: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

''' 
    API endpoint to update a user-defined name for a device.
    Expects JSON: { "mac": "<mac_address>", "device_name": "<name>" }
'''
@db_bp.route("/db/devices/<mac>", methods=["PUT"])
def update_device(mac):
    """Update a device's name."""
    try:
        data = request.get_json()
        name = data.get("name")
        if not name:
            return jsonify(error("Missing 'name' in request body", status_code=400))
            
        result = update_device_name(mac, name)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error updating device: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

''' 
    API endpoint to clear all device records from the database.
'''
@db_bp.route("/db/clear", methods=["DELETE"])
def clear_devices_route():
    """Clear all device records from the database."""
    try:
        result = clear_devices()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error clearing devices: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))