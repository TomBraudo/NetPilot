from flask import Blueprint, request, jsonify
from utils.logging_config import get_logger
from services.blacklist_service import (
    get_blacklist_devices,
    add_device_to_blacklist,
    remove_device_from_blacklist,
    clear_blacklist,
    get_blacklist_limit_rate,
    set_blacklist_limit_rate,
    get_blacklist_full_rate,
    set_blacklist_full_rate,
    activate_blacklist_mode,
    deactivate_blacklist_mode,
    is_blacklist_mode
)

blacklist_bp = Blueprint('blacklist', __name__)
logger = get_logger('endpoints.blacklist')

@blacklist_bp.route("/blacklist", methods=["GET"])
def get_blacklist():
    """Get all devices in the blacklist"""
    try:
        devices = get_blacklist_devices()
        return jsonify({"devices": devices})
    except Exception as e:
        logger.error(f"Error getting blacklist: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@blacklist_bp.route("/blacklist/<ip>", methods=["POST"])
def add_to_blacklist(ip):
    """Add a device to the blacklist"""
    try:
        result = add_device_to_blacklist(ip)
        if result:
            return jsonify({"message": f"Device {ip} added to blacklist"})
        return jsonify({"error": "Failed to add device to blacklist"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error adding device to blacklist: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@blacklist_bp.route("/blacklist/<ip>", methods=["DELETE"])
def remove_from_blacklist(ip):
    """Remove a device from the blacklist"""
    try:
        result = remove_device_from_blacklist(ip)
        if result:
            return jsonify({"message": f"Device {ip} removed from blacklist"})
        return jsonify({"error": "Failed to remove device from blacklist"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error removing device from blacklist: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@blacklist_bp.route("/blacklist/limit-rate", methods=["GET"])
def get_limit_rate():
    """Get the current blacklist bandwidth limit rate"""
    try:
        rate = get_blacklist_limit_rate()
        return jsonify({"rate": rate})
    except Exception as e:
        logger.error(f"Error getting blacklist limit rate: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@blacklist_bp.route("/blacklist/limit-rate/<rate>", methods=["POST"])
def set_limit_rate(rate):
    """Set the blacklist bandwidth limit rate"""
    try:
        new_rate = set_blacklist_limit_rate(rate)
        return jsonify({"rate": new_rate})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error setting blacklist limit rate: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@blacklist_bp.route("/blacklist/full-rate", methods=["GET"])
def get_full_rate():
    """Get the current blacklist full bandwidth rate"""
    try:
        rate = get_blacklist_full_rate()
        return jsonify({"rate": rate})
    except Exception as e:
        logger.error(f"Error getting blacklist full rate: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@blacklist_bp.route("/blacklist/full-rate/<rate>", methods=["POST"])
def set_full_rate(rate):
    """Set the blacklist full bandwidth rate"""
    try:
        new_rate = set_blacklist_full_rate(rate)
        return jsonify({"rate": new_rate})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error setting blacklist full rate: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@blacklist_bp.route("/blacklist/mode/activate", methods=["POST"])
def activate_mode():
    """Activate blacklist mode"""
    try:
        if activate_blacklist_mode():
            return jsonify({"message": "Blacklist mode activated successfully"})
        return jsonify({"error": "Failed to activate blacklist mode"}), 400
    except Exception as e:
        logger.error(f"Error activating blacklist mode: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@blacklist_bp.route("/blacklist/mode/deactivate", methods=["POST"])
def deactivate_mode():
    """Deactivate blacklist mode"""
    try:
        if deactivate_blacklist_mode():
            return jsonify({"message": "Blacklist mode deactivated successfully"})
        return jsonify({"error": "Failed to deactivate blacklist mode"}), 400
    except Exception as e:
        logger.error(f"Error deactivating blacklist mode: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@blacklist_bp.route("/blacklist/mode", methods=["GET"])
def get_mode():
    """Get the current blacklist mode status"""
    try:
        is_active = is_blacklist_mode()
        return jsonify({"active": is_active})
    except Exception as e:
        logger.error(f"Error getting blacklist mode: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@blacklist_bp.route("/blacklist", methods=["DELETE"])
def clear_blacklist_route():
    """Clear all devices from the blacklist"""
    try:
        result = clear_blacklist()
        if result:
            return jsonify({"message": "Blacklist cleared successfully"})
        return jsonify({"error": "Failed to clear blacklist"}), 400
    except Exception as e:
        logger.error(f"Error clearing blacklist: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500 