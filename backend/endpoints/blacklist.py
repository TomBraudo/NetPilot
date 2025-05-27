from flask import Blueprint, request, jsonify
from utils.logging_config import get_logger
from utils.response_helpers import error
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
logger = get_logger('blacklist.endpoints')

@blacklist_bp.route("/blacklist", methods=["GET"])
def get_blacklist():
    """Get all devices in the blacklist"""
    try:
        result = get_blacklist_devices()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting blacklist: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@blacklist_bp.route("/blacklist", methods=["POST"])
def add_to_blacklist():
    """Add a device to the blacklist"""
    try:
        data = request.get_json()
        ip = data.get("ip")
        if not ip:
            return jsonify(error("Missing 'ip' in request body", status_code=400))
            
        result = add_device_to_blacklist(ip)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error adding device to blacklist: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@blacklist_bp.route("/blacklist", methods=["DELETE"])
def remove_from_blacklist():
    """Remove a device from the blacklist"""
    try:
        data = request.get_json()
        ip = data.get("ip")
        if not ip:
            return jsonify(error("Missing 'ip' in request body", status_code=400))
            
        result = remove_device_from_blacklist(ip)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error removing device from blacklist: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@blacklist_bp.route("/blacklist/clear", methods=["POST"])
def clear_blacklist_route():
    """Clear all devices from the blacklist"""
    try:
        result = clear_blacklist()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error clearing blacklist: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@blacklist_bp.route("/blacklist/limit-rate", methods=["GET"])
def get_limit_rate():
    """Get the current blacklist bandwidth limit rate"""
    try:
        result = get_blacklist_limit_rate()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting blacklist limit rate: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@blacklist_bp.route("/blacklist/limit-rate", methods=["POST"])
def set_limit_rate():
    """Set the blacklist bandwidth limit rate"""
    try:
        data = request.get_json()
        rate = data.get("rate")
        if not rate:
            return jsonify(error("Missing 'rate' in request body", status_code=400))
            
        result = set_blacklist_limit_rate(rate)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error setting blacklist limit rate: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@blacklist_bp.route("/blacklist/full-rate", methods=["GET"])
def get_full_rate():
    """Get the current blacklist full bandwidth rate"""
    try:
        result = get_blacklist_full_rate()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting blacklist full rate: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@blacklist_bp.route("/blacklist/full-rate", methods=["POST"])
def set_full_rate():
    """Set the blacklist full bandwidth rate"""
    try:
        data = request.get_json()
        rate = data.get("rate")
        if not rate:
            return jsonify(error("Missing 'rate' in request body", status_code=400))
            
        result = set_blacklist_full_rate(rate)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error setting blacklist full rate: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@blacklist_bp.route("/blacklist/activate", methods=["POST"])
def activate():
    """Activate blacklist mode"""
    try:
        result = activate_blacklist_mode()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error activating blacklist mode: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@blacklist_bp.route("/blacklist/deactivate", methods=["POST"])
def deactivate():
    """Deactivate blacklist mode"""
    try:
        result = deactivate_blacklist_mode()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error deactivating blacklist mode: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@blacklist_bp.route("/blacklist/mode", methods=["GET"])
def get_mode():
    """Get the current blacklist mode status"""
    try:
        result = is_blacklist_mode()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting blacklist mode: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500)) 