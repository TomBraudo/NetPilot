from flask import Blueprint, request, jsonify
from utils.logging_config import get_logger
from utils.response_helpers import error
from services.config_service import (
    set_admin_credentials,
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