from flask import Blueprint, request, jsonify
from utils.logging_config import get_logger
from utils.response_helpers import error
from services.network_service import (
    get_blocked_devices_list,
    block_device,
    unblock_device,
    reset_all_network_rules,
    scan_network,
    scan_network_via_router,
    run_ookla_speedtest
)

network_bp = Blueprint('network', __name__)
logger = get_logger('endpoints.network')

@network_bp.route("/api/blocked", methods=["GET"])
def get_blocked():
    """Get all currently blocked devices"""
    try:
        result = get_blocked_devices_list()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting blocked devices: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@network_bp.route("/api/block", methods=["POST"])
def block():
    """Block a device by IP address"""
    try:
        data = request.get_json()
        ip = data.get("ip")
        if not ip:
            return jsonify(error("Missing 'ip' in request body", status_code=400))
        
        result = block_device(ip)
        return jsonify(result)
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify(error(str(e), status_code=404))
    except Exception as e:
        logger.error(f"Error blocking device: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@network_bp.route("/api/unblock", methods=["POST"])
def unblock():
    """Unblock a device by IP address"""
    try:
        data = request.get_json()
        ip = data.get("ip")
        if not ip:
            return jsonify(error("Missing 'ip' in request body", status_code=400))
        
        result = unblock_device(ip)
        return jsonify(result)
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify(error(str(e), status_code=404))
    except Exception as e:
        logger.error(f"Error unblocking device: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@network_bp.route("/api/reset", methods=["POST"])
def reset():
    """Reset all network rules"""
    try:
        result = reset_all_network_rules()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error resetting network rules: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@network_bp.route("/api/scan", methods=["GET"])
def scan():
    """Scan the network for devices"""
    try:
        result = scan_network()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error scanning network: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@network_bp.route("/api/scan/router", methods=["GET"])
def scan_router():
    """Scan the network via router"""
    try:
        result = scan_network_via_router()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error scanning network via router: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@network_bp.route("/api/speedtest", methods=["GET"])
def speedtest():
    """Run a speed test"""
    try:
        result = run_ookla_speedtest()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error running speed test: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))