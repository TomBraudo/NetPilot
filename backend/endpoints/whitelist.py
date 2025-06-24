from flask import Blueprint, request, jsonify
from utils.logging_config import get_logger
from utils.response_helpers import error
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
logger = get_logger('whitelist.endpoints')

@whitelist_bp.route("/whitelist", methods=["GET"])
def get_whitelist():
    """Get all devices in the whitelist"""
    try:
        result = get_whitelist_devices()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting whitelist: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@whitelist_bp.route("/whitelist", methods=["POST"])
def add_to_whitelist():
    """Add a device to the whitelist"""
    try:
        data = request.get_json()
        ip = data.get("ip")
        if not ip:
            return jsonify(error("Missing 'ip' in request body", status_code=400))
            
        result = add_device_to_whitelist(ip)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error adding device to whitelist: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@whitelist_bp.route("/whitelist", methods=["DELETE"])
def remove_from_whitelist():
    """Remove a device from the whitelist"""
    try:
        data = request.get_json()
        ip = data.get("ip")
        if not ip:
            return jsonify(error("Missing 'ip' in request body", status_code=400))
            
        result = remove_device_from_whitelist(ip)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error removing device from whitelist: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@whitelist_bp.route("/whitelist/clear", methods=["POST"])
def clear_whitelist_route():
    """Clear all devices from the whitelist"""
    try:
        result = clear_whitelist()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error clearing whitelist: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@whitelist_bp.route("/whitelist/limit-rate", methods=["GET"])
def get_limit_rate():
    """Get the current whitelist bandwidth limit rate"""
    try:
        result = get_whitelist_limit_rate()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting whitelist limit rate: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@whitelist_bp.route("/whitelist/limit-rate", methods=["POST"])
def set_limit_rate():
    """Set the whitelist bandwidth limit rate"""
    try:
        data = request.get_json()
        rate = data.get("rate")
        if not rate:
            return jsonify(error("Missing 'rate' in request body", status_code=400))
            
        result = set_whitelist_limit_rate(rate)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error setting whitelist limit rate: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@whitelist_bp.route("/whitelist/full-rate", methods=["GET"])
def get_full_rate():
    """Get the current whitelist full bandwidth rate"""
    try:
        result = get_whitelist_full_rate()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting whitelist full rate: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@whitelist_bp.route("/whitelist/full-rate", methods=["POST"])
def set_full_rate():
    """Set the whitelist full bandwidth rate"""
    try:
        data = request.get_json()
        rate = data.get("rate")
        if not rate:
            return jsonify(error("Missing 'rate' in request body", status_code=400))
            
        result = set_whitelist_full_rate(rate)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error setting whitelist full rate: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@whitelist_bp.route("/whitelist/activate", methods=["POST"])
def activate():
    """Activate whitelist mode"""
    try:
        result = activate_whitelist_mode()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error activating whitelist mode: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@whitelist_bp.route("/whitelist/deactivate", methods=["POST"])
def deactivate():
    """Deactivate whitelist mode"""
    try:
        result = deactivate_whitelist_mode()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error deactivating whitelist mode: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@whitelist_bp.route("/whitelist/mode", methods=["GET"])
def get_mode():
    """Get the current whitelist mode status"""
    try:
        result = is_whitelist_mode()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting whitelist mode: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))


