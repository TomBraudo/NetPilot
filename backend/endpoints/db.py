from flask import Blueprint, request, jsonify
from utils.logging_config import get_logger
from utils.response_helpers import error
from db.device_repository import (
    get_all_devices,
    get_device_by_mac,
    update_device_name,
    clear_devices
)
from db.device_groups_repository import (
    get_all_groups,
    get_group_members,
    get_rules_for_device
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

'''
    API endpoint to retrieve all device groups.
'''
@db_bp.route("/db/groups", methods=["GET"])
def get_groups():
    """Get all device groups."""
    try:
        result = get_all_groups()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting groups: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

''' 
    API endpoint to retrieve all devices in a specific group.
    Expects query param: ?group_name=<group_name>
'''
@db_bp.route("/db/groups/<group_id>/members", methods=["GET"])
def get_group_members_route(group_id):
    """Get all members of a device group."""
    try:
        result = get_group_members(group_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting group members: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

'''
    API endpoint to retrieve all rules for a specific device.
    Expects query params: ?mac=<mac_address>&ip=<ip_address>
'''
@db_bp.route("/db/devices/<mac>/rules", methods=["GET"])
def get_device_rules(mac):
    """Get all rules for a specific device."""
    try:
        result = get_rules_for_device(mac)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting device rules: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))