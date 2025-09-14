from flask import Blueprint
from utils.response_helpers import build_success_response, build_error_response
import time
from services.monitor_service import check_nlbwmon_status

health_bp = Blueprint('health', __name__)

''' 
    API endpoint for health checking.
    Returns a simple success message to confirm the server is running.
'''
@health_bp.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint to verify server is running.
    Returns a simple success message.
    """
    execution_start_time = time.time()
    return build_success_response({"message": "Server is healthy"}, execution_start_time)

@health_bp.route("/monitoring", methods=["GET"])
def monitoring_health():
    """Checks nlbwmon status via monitor service."""
    execution_start_time = time.time()
    try:
        status, error = check_nlbwmon_status()
        if error:
            return build_error_response(f"Monitoring check failed: {error}", 500, "MONITORING_CHECK_FAILED", execution_start_time)
        return build_success_response(status or {"running": False}, execution_start_time)
    except Exception as e:
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", execution_start_time)

@health_bp.route("/device-chains", methods=["GET"])
def device_chains_health():
    """Deprecated: iptables chains not used."""
    execution_start_time = time.time()
    return build_success_response({"message": "Not applicable"}, execution_start_time)

@health_bp.route("/rebuild-chains", methods=["POST"])
def rebuild_chains():
    """Deprecated: iptables chains not used."""
    execution_start_time = time.time()
    return build_success_response({"message": "Not applicable"}, execution_start_time)

@health_bp.route("/mode-activation", methods=["GET"])
def mode_activation_health():
    """Deprecated: mode activation (iptables) not used."""
    execution_start_time = time.time()
    return build_success_response({"message": "Not applicable"}, execution_start_time)

@health_bp.route("/deactivate-all-modes", methods=["POST"])
def deactivate_all_modes():
    """Deprecated: mode activation (iptables) not used."""
    execution_start_time = time.time()
    return build_success_response({"message": "Not applicable"}, execution_start_time)