from flask import Blueprint
from utils.response_helpers import success

health_bp = Blueprint('health', __name__)

''' 
    API endpoint for health checking.
    Returns a simple success message to confirm the server is running.
'''
@health_bp.route("/health", methods=["GET"])
def health():
    return success("Server is healthy")

@health_bp.route("/infrastructure", methods=["GET"])
def infrastructure_health():
    """
    Validates the NetPilot infrastructure setup.
    Returns detailed status of TC classes, filters, and iptables chains.
    """
    from services.router_setup_service import validate_infrastructure
    
    try:
        success_status, result = validate_infrastructure()
        if success_status:
            return success("Infrastructure validation completed", result)
        else:
            return success("Infrastructure validation failed", {"error": result})
    except Exception as e:
        return success("Infrastructure validation error", {"error": str(e)})

@health_bp.route("/device-chains", methods=["GET"])
def device_chains_health():
    """
    Validates the NetPilot device chains (NETPILOT_WHITELIST and NETPILOT_BLACKLIST).
    Returns detailed status of device rules and chain configuration.
    """
    from services.device_rule_service import validate_device_chains
    
    try:
        success_status, result = validate_device_chains()
        if success_status:
            return success("Device chains validation completed", result)
        else:
            return success("Device chains validation failed", {"error": result})
    except Exception as e:
        return success("Device chains validation error", {"error": str(e)})

@health_bp.route("/rebuild-chains", methods=["POST"])
def rebuild_chains():
    """
    Rebuilds all device chains from the current database state.
    Useful for troubleshooting when chains become out of sync.
    """
    from services.router_setup_service import rebuild_all_device_chains
    
    try:
        success_status, result = rebuild_all_device_chains()
        if success_status:
            return success("Device chains rebuilt successfully", result)
        else:
            return success("Device chains rebuild failed", {"error": result, "details": result if isinstance(result, dict) else None})
    except Exception as e:
        return success("Device chains rebuild error", {"error": str(e)})

@health_bp.route("/mode-activation", methods=["GET"])
def mode_activation_health():
    """
    Validates the NetPilot mode activation status.
    Returns detailed status of iptables jump rules and active mode.
    """
    from services.mode_activation_service import validate_mode_activation
    
    try:
        success_status, result = validate_mode_activation()
        if success_status:
            return success("Mode activation validation completed", result)
        else:
            return success("Mode activation validation failed", {"error": result})
    except Exception as e:
        return success("Mode activation validation error", {"error": str(e)})

@health_bp.route("/deactivate-all-modes", methods=["POST"])
def deactivate_all_modes():
    """
    Deactivates all modes by removing all iptables jump commands.
    Useful for troubleshooting when modes get stuck.
    """
    from services.mode_activation_service import deactivate_all_modes_rules
    
    try:
        success_status, result = deactivate_all_modes_rules()
        if success_status:
            return success("All modes deactivated successfully", {"result": result})
        else:
            return success("Failed to deactivate all modes", {"error": result})
    except Exception as e:
        return success("Mode deactivation error", {"error": str(e)})