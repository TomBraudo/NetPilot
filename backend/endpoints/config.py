from flask import Blueprint, request, jsonify
from utils.logging_config import get_logger
from utils.response_helpers import error
from services.config_service import (
    set_admin_credentials,
    get_admin_credentials,
    set_router_credentials,
    get_router_credentials
)

config_bp = Blueprint('config', __name__)
logger = get_logger('config.endpoints')

@config_bp.route("/config/admin", methods=["POST"])
def set_admin():
    """Set the admin username and password for the web interface."""
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return jsonify(error("Missing 'username' or 'password' in request body", status_code=400))
            
        result = set_admin_credentials(username, password)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error setting admin credentials: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@config_bp.route("/config/admin", methods=["GET"])
def get_admin():
    """Get the current admin credentials."""
    try:
        result = get_admin_credentials()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting admin credentials: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@config_bp.route("/config/router", methods=["POST"])
def set_router():
    """Set the router credentials."""
    try:
        data = request.get_json()
        ip = data.get("ip")
        username = data.get("username")
        password = data.get("password")
        
        if not ip or not username or not password:
            return jsonify(error("Missing required fields in request body", status_code=400))
            
        result = set_router_credentials(ip, username, password)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error setting router credentials: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))

@config_bp.route("/config/router", methods=["GET"])
def get_router():
    """Get the current router credentials."""
    try:
        result = get_router_credentials()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting router credentials: {str(e)}", exc_info=True)
        return jsonify(error(str(e), status_code=500))