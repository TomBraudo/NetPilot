from flask import Blueprint
from utils.response_helpers import success, error, build_success_response, build_error_response
from utils.logging_config import get_logger
from managers.commands_server_manager import commands_server_manager
import time

health_bp = Blueprint('health', __name__)
logger = get_logger('endpoints.health')

@health_bp.route("/health", methods=["GET"])
def health():
    """
    Comprehensive health check endpoint.
    
    Checks:
    1. Backend2 server health
    2. Commands server connectivity
    3. Commands server health status
    
    Returns detailed health information for monitoring and debugging.
    """
    start_time = time.time()
    
    try:
        # Backend2 server is healthy if we reach this point
        backend2_status = {
            "status": "healthy",
            "message": "Backend2 server is running"
        }
        
        # Check commands server connection and health
        logger.info("Checking commands server health")
        
        # Test connection to commands server
        is_connected, connection_error = commands_server_manager.test_connection()
        
        if not is_connected:
            logger.warning(f"Commands server health check failed: {connection_error}")
            
            # Return partial health - backend2 is healthy but commands server is not
            health_data = {
                "backend2": backend2_status,
                "commands_server": {
                    "status": "unhealthy",
                    "connected": False,
                    "error": connection_error or "Connection failed"
                },
                "overall_status": "degraded",
                "message": "Backend2 is healthy but commands server is not accessible"
            }
            
            return build_error_response(
                "Commands server is not accessible", 
                503, 
                "SERVICE_UNAVAILABLE", 
                start_time
            )
        
        # Get detailed commands server info
        server_info, info_error = commands_server_manager.get_server_info()
        
        commands_server_status = {
            "status": "healthy",
            "connected": True,
            "url": commands_server_manager.base_url
        }
        
        # Add server info if available
        if server_info:
            commands_server_status["server_info"] = server_info
        elif info_error:
            commands_server_status["info_warning"] = f"Could not get server info: {info_error}"
        
        # All systems healthy
        health_data = {
            "backend2": backend2_status,
            "commands_server": commands_server_status,
            "overall_status": "healthy",
            "message": "All systems are healthy and operational"
        }
        
        logger.info("Health check completed - all systems healthy")
        return build_success_response(health_data, start_time)
        
    except Exception as e:
        logger.error(f"Unexpected error during health check: {e}", exc_info=True)
        
        error_data = {
            "backend2": {
                "status": "unknown",
                "message": "Unexpected error during health check"
            },
            "commands_server": {
                "status": "unknown",
                "connected": False,
                "error": "Could not test connection due to server error"
            },
            "overall_status": "unhealthy",
            "message": "Health check failed due to unexpected error"
        }
        
        return build_error_response(
            "Health check failed due to unexpected error", 
            500, 
            "INTERNAL_SERVER_ERROR", 
            start_time
        )

@health_bp.route("/health/simple", methods=["GET"])
def health_simple():
    """
    Simple health check endpoint for basic monitoring.
    
    Returns a simple success/error response without detailed information.
    This is useful for load balancers and basic monitoring that just need
    to know if the service is up.
    """
    try:
        # Check if commands server is connected
        if not commands_server_manager.is_connected():
            return error("Commands server is not connected", 503)
        
        return success("Server is healthy")
        
    except Exception as e:
        logger.error(f"Simple health check failed: {e}")
        return error("Health check failed", 500)

@health_bp.route("/health/commands-server", methods=["GET"])
def health_commands_server():
    """
    Commands server specific health check.
    
    Returns detailed information about the commands server status.
    """
    start_time = time.time()
    
    try:
        logger.info("Checking commands server health specifically")
        
        # Test connection
        is_connected, connection_error = commands_server_manager.test_connection()
        
        if not is_connected:
            return build_error_response(
                f"Commands server is not accessible: {connection_error}",
                503,
                "SERVICE_UNAVAILABLE",
                start_time
            )
        
        # Get server info
        server_info, info_error = commands_server_manager.get_server_info()
        
        health_data = {
            "status": "healthy",
            "connected": True,
            "url": commands_server_manager.base_url,
            "server_info": server_info if server_info else None,
            "info_error": info_error if info_error else None
        }
        
        return build_success_response(health_data, start_time)
        
    except Exception as e:
        logger.error(f"Commands server health check failed: {e}", exc_info=True)
        return build_error_response(
            "Commands server health check failed",
            500,
            "INTERNAL_SERVER_ERROR",
            start_time
        ) 