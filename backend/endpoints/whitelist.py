from flask import Blueprint, request, jsonify
from utils.logging_config import get_logger
from services.whitelist_service import (
    get_whitelist_devices,
    add_device_to_whitelist,
    remove_device_from_whitelist,
    clear_whitelist,
    get_whitelist_limit_rate,
    set_whitelist_limit_rate,
    get_whitelist_full_rate,
    set_whitelist_full_rate,
    activate_whitelist_mode,
    deactivate_whitelist_mode,
    is_whitelist_mode
)

whitelist_bp = Blueprint('whitelist', __name__)
logger = get_logger('endpoints.whitelist')

@whitelist_bp.route("/whitelist", methods=["GET"])
def get_whitelist():
    """Get all devices in the whitelist"""
    try:
        devices = get_whitelist_devices()
        return jsonify({"devices": devices})
    except Exception as e:
        logger.error(f"Error getting whitelist: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@whitelist_bp.route("/whitelist/<ip>", methods=["POST"])
def add_to_whitelist(ip):
    """Add a device to the whitelist"""
    try:
        result = add_device_to_whitelist(ip)
        if result:
            return jsonify({"message": f"Device {ip} added to whitelist"})
        return jsonify({"error": "Failed to add device to whitelist"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error adding device to whitelist: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@whitelist_bp.route("/whitelist/<ip>", methods=["DELETE"])
def remove_from_whitelist(ip):
    """Remove a device from the whitelist"""
    try:
        result = remove_device_from_whitelist(ip)
        if result:
            return jsonify({"message": f"Device {ip} removed from whitelist"})
        return jsonify({"error": "Failed to remove device from whitelist"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error removing device from whitelist: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@whitelist_bp.route("/whitelist/limit-rate", methods=["GET"])
def get_limit_rate():
    """Get the current whitelist bandwidth limit rate"""
    try:
        rate = get_whitelist_limit_rate()
        return jsonify({"rate": rate})
    except Exception as e:
        logger.error(f"Error getting whitelist limit rate: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@whitelist_bp.route("/whitelist/limit-rate/<rate>", methods=["POST"])
def set_limit_rate(rate):
    """Set the whitelist bandwidth limit rate"""
    try:
        new_rate = set_whitelist_limit_rate(rate)
        return jsonify({"rate": new_rate})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error setting whitelist limit rate: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@whitelist_bp.route("/whitelist/full-rate", methods=["GET"])
def get_full_rate():
    """Get the current whitelist full bandwidth rate"""
    try:
        rate = get_whitelist_full_rate()
        return jsonify({"rate": rate})
    except Exception as e:
        logger.error(f"Error getting whitelist full rate: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@whitelist_bp.route("/whitelist/full-rate/<rate>", methods=["POST"])
def set_full_rate(rate):
    """Set the whitelist full bandwidth rate"""
    try:
        new_rate = set_whitelist_full_rate(rate)
        return jsonify({"rate": new_rate})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error setting whitelist full rate: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@whitelist_bp.route("/whitelist/mode/activate", methods=["POST"])
def activate_mode():
    """Activate whitelist mode"""
    try:
        if activate_whitelist_mode():
            return jsonify({"message": "Whitelist mode activated successfully"})
        return jsonify({"error": "Failed to activate whitelist mode"}), 400
    except Exception as e:
        logger.error(f"Error activating whitelist mode: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@whitelist_bp.route("/whitelist/mode/deactivate", methods=["POST"])
def deactivate_mode():
    """Deactivate whitelist mode"""
    try:
        if deactivate_whitelist_mode():
            return jsonify({"message": "Whitelist mode deactivated successfully"})
        return jsonify({"error": "Failed to deactivate whitelist mode"}), 400
    except Exception as e:
        logger.error(f"Error deactivating whitelist mode: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@whitelist_bp.route("/whitelist/mode", methods=["GET"])
def get_mode():
    """Get the current whitelist mode status"""
    try:
        is_active = is_whitelist_mode()
        return jsonify({"active": is_active})
    except Exception as e:
        logger.error(f"Error getting whitelist mode: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@whitelist_bp.route("/whitelist", methods=["DELETE"])
def clear_whitelist_route():
    """Clear all devices from the whitelist"""
    try:
        result = clear_whitelist()
        if result:
            return jsonify({"message": "Whitelist cleared successfully"})
        return jsonify({"error": "Failed to clear whitelist"}), 400
    except Exception as e:
        logger.error(f"Error clearing whitelist: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


