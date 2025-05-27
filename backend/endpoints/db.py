from flask import Blueprint, request, jsonify
from utils.response_helpers import success, error
from utils.logging_config import get_logger
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
        devices = get_all_devices()
        return jsonify(success(data=devices))
    except Exception as e:
        logger.error(f"Error getting devices: {str(e)}", exc_info=True)
        return jsonify(error(str(e))), 500

@db_bp.route("/db/devices/<mac>", methods=["GET"])
def get_device(mac):
    """Get a specific device by MAC address."""
    try:
        device = get_device_by_mac(mac)
        if not device:
            raise ValueError("Device not found")
        return jsonify(success(data=device))
    except ValueError as e:
        logger.error(f"Device not found: {str(e)}")
        return jsonify(error(str(e))), 404
    except Exception as e:
        logger.error(f"Error getting device: {str(e)}", exc_info=True)
        return jsonify(error(str(e))), 500

''' 
    API endpoint to update a user-defined name for a device.
    Expects JSON: { "mac": "<mac_address>", "device_name": "<name>" }
'''
@db_bp.route("/db/devices/<mac>/name", methods=["PUT"])
def update_device(mac):
    """Update a device's name."""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify(error("Name is required")), 400
            
        if not update_device_name(mac, None, data['name']):
            raise ValueError("Device not found")
        return jsonify(success("Device name updated"))
    except ValueError as e:
        logger.error(f"Device not found: {str(e)}")
        return jsonify(error(str(e))), 404
    except Exception as e:
        logger.error(f"Error updating device: {str(e)}", exc_info=True)
        return jsonify(error(str(e))), 500

''' 
    API endpoint to clear all device records from the database.
'''
@db_bp.route("/db/clear", methods=["DELETE"])
def clear_devices_route():
    """Clear all device records from the database."""
    try:
        if not clear_devices():
            raise RuntimeError("Failed to clear devices")
        return jsonify(success("All devices cleared from the database"))
    except Exception as e:
        logger.error(f"Error clearing devices: {str(e)}", exc_info=True)
        return jsonify(error(str(e))), 500

'''
    API endpoint to retrieve all device groups.
'''
@db_bp.route("/db/groups", methods=["GET"])
def get_groups():
    """Get all device groups."""
    try:
        groups = get_all_groups()
        return jsonify(success(data=groups))
    except Exception as e:
        logger.error(f"Error getting groups: {str(e)}", exc_info=True)
        return jsonify(error(str(e))), 500

''' 
    API endpoint to retrieve all devices in a specific group.
    Expects query param: ?group_name=<group_name>
'''
@db_bp.route("/db/groups/<group_id>/members", methods=["GET"])
def get_group_members_route(group_id):
    """Get all members of a device group."""
    try:
        members = get_group_members(group_id)
        return jsonify(success(data=members))
    except Exception as e:
        logger.error(f"Error getting group members: {str(e)}", exc_info=True)
        return jsonify(error(str(e))), 500

'''
    API endpoint to retrieve all rules for a specific device.
    Expects query params: ?mac=<mac_address>&ip=<ip_address>
'''
@db_bp.route("/db/devices/<mac>/rules", methods=["GET"])
def get_device_rules(mac):
    """Get all rules for a specific device."""
    try:
        rules = get_rules_for_device(mac)
        return jsonify(success(data=rules))
    except Exception as e:
        logger.error(f"Error getting device rules: {str(e)}", exc_info=True)
        return jsonify(error(str(e))), 500