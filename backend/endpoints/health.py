from flask import Blueprint
from utils.response_helpers import build_success_response, build_error_response
import time

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

@health_bp.route("/infrastructure", methods=["GET"])
def infrastructure_health():
    """
    Validates the NetPilot infrastructure setup.
    Returns detailed status of TC classes, filters, and iptables chains.
    """
    execution_start_time = time.time()
    from services.router_setup_service import validate_infrastructure
    
    try:
        success_status, result = validate_infrastructure()
        if success_status:
            return build_success_response(result, execution_start_time)
        else:
            return build_error_response(
                "Infrastructure validation failed",
                status_code=500,
                error_code="INFRA_VALIDATION_FAILED",
                execution_start_time=execution_start_time
            )
    except Exception as e:
        return build_error_response(
            f"Infrastructure validation error: {str(e)}",
            status_code=500,
            error_code="INFRA_VALIDATION_ERROR",
            execution_start_time=execution_start_time
        )

@health_bp.route("/device-chains", methods=["GET"])
def device_chains_health():
    """
    Validates the NetPilot device chains (NETPILOT_WHITELIST and NETPILOT_BLACKLIST).
    Returns detailed status of device rules and chain configuration.
    """
    execution_start_time = time.time()
    from services.device_rule_service import validate_device_chains
    
    try:
        success_status, result = validate_device_chains()
        if success_status:
            return build_success_response({"message": "Device chains validation completed", "details": result}, execution_start_time)
        else:
            return build_error_response(
                "Device chains validation failed", 
                status_code=500, 
                error_code="DEVICE_CHAINS_VALIDATION_FAILED", 
                execution_start_time=execution_start_time
            )
    except Exception as e:
        return build_error_response(
            f"Device chains validation error: {str(e)}", 
            status_code=500, 
            error_code="DEVICE_CHAINS_VALIDATION_ERROR", 
            execution_start_time=execution_start_time
        )

@health_bp.route("/rebuild-chains", methods=["POST"])
def rebuild_chains():
    """
    Rebuilds all device chains from the current database state.
    Useful for troubleshooting when chains become out of sync.
    """
    execution_start_time = time.time()
    from services.router_setup_service import rebuild_all_device_chains
    
    try:
        success_status, result = rebuild_all_device_chains()
        if success_status:
            return build_success_response({"message": "Device chains rebuilt successfully", "details": result}, execution_start_time)
        else:
            details = result if isinstance(result, dict) else {"error": result}
            return build_error_response(
                "Device chains rebuild failed", 
                status_code=500, 
                error_code="DEVICE_CHAINS_REBUILD_FAILED", 
                execution_start_time=execution_start_time
            )
    except Exception as e:
        return build_error_response(
            f"Device chains rebuild error: {str(e)}", 
            status_code=500, 
            error_code="DEVICE_CHAINS_REBUILD_ERROR", 
            execution_start_time=execution_start_time
        )

@health_bp.route("/mode-activation", methods=["GET"])
def mode_activation_health():
    """
    Validates the NetPilot mode activation status.
    Returns detailed status of iptables jump rules and active mode.
    """
    execution_start_time = time.time()
    from services.mode_activation_service import validate_mode_activation
    
    try:
        success_status, result = validate_mode_activation()
        if success_status:
            return build_success_response({"message": "Mode activation validation completed", "details": result}, execution_start_time)
        else:
            return build_error_response(
                "Mode activation validation failed", 
                status_code=500, 
                error_code="MODE_ACTIVATION_VALIDATION_FAILED", 
                execution_start_time=execution_start_time
            )
    except Exception as e:
        return build_error_response(
            f"Mode activation validation error: {str(e)}", 
            status_code=500, 
            error_code="MODE_ACTIVATION_VALIDATION_ERROR", 
            execution_start_time=execution_start_time
        )

@health_bp.route("/deactivate-all-modes", methods=["POST"])
def deactivate_all_modes():
    """
    Deactivates all modes by removing all iptables jump commands.
    Useful for troubleshooting when modes get stuck.
    """
    execution_start_time = time.time()
    from services.mode_activation_service import deactivate_all_modes_rules
    
    try:
        success_status, result = deactivate_all_modes_rules()
        if success_status:
            return build_success_response({"message": "All modes deactivated successfully", "details": result}, execution_start_time)
        else:
            return build_error_response(
                "Failed to deactivate all modes", 
                status_code=500, 
                error_code="MODE_DEACTIVATION_FAILED", 
                execution_start_time=execution_start_time
            )
    except Exception as e:
        return build_error_response(
            f"Mode deactivation error: {str(e)}", 
            status_code=500, 
            error_code="MODE_DEACTIVATION_ERROR", 
            execution_start_time=execution_start_time
        )