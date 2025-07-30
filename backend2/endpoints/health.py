from flask import Blueprint, g
from utils.response_helpers import success, error, build_success_response, build_error_response
from utils.logging_config import get_logger
from managers.commands_server_manager import commands_server_manager
import time

health_bp = Blueprint('health', __name__)
logger = get_logger('endpoints.health')

@health_bp.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint.
    
    This endpoint is exempted from router_id/session_id requirements.
    It checks basic connectivity to the commands server without requiring
    specific router or session context.
    """
    start_time = time.time()
    
    try:
        logger.info("Performing basic health check")
        
        # Check if commands server is connected (basic connectivity test)
        if not commands_server_manager.is_connected():
            return build_error_response(
                "Commands server is not accessible",
                503,
                "SERVICE_UNAVAILABLE",
                start_time
            )
        
        # Health check successful - both backend2 and commands server are accessible
        health_data = {
            "status": "healthy",
            "backend2": "running",
            "commands_server": "accessible",
            "commands_server_url": commands_server_manager.base_url
        }
        
        logger.info("Health check completed successfully")
        return build_success_response(health_data, start_time)
        
    except Exception as e:
        logger.error(f"Unexpected error during health check: {e}", exc_info=True)
        return build_error_response(
            "Health check failed due to unexpected error",
            500,
            "INTERNAL_SERVER_ERROR",
            start_time
        ) 