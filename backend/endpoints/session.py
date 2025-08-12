from flask import Blueprint, request, jsonify, current_app, g
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from utils.infrastructure_setup import setup_persistent_infrastructure, check_existing_infrastructure, InfrastructureComponent
import time

logger = get_logger('session.endpoints')

session_bp = Blueprint('session', __name__)

@session_bp.route("/start", methods=["POST"])
def start_session():
    """Starts a new session for a router; infrastructure setup deprecated (headless mode)."""
    execution_start_time = time.time()
    
    # The session context (g.session_id, g.router_id) is now expected to be set
    # by the session_context_middleware before this function is called.
    logger = current_app.logger
    
    # Get the restart flag from JSON body
    data = request.get_json() or {}
    restart = data.get('restart', False)
    
    logger.info(f"Attempting to start session for router {g.router_id} with session ID {g.session_id} (restart={restart})")

    # If the session is already active, reject the request.
    if current_app.router_connection_manager.get_session_status(g.session_id):
        logger.warning(f"Session {g.session_id} is already active – rejecting start request")
        return build_error_response("Session is already active", 400, "SESSION_ALREADY_ACTIVE", execution_start_time)

    # 1. Mark the session as active in the RouterConnectionManager first.
    current_app.router_connection_manager.start_session(g.session_id)

    # Headless mode: verify reachability and ensure monitoring (nlbw) is set up
    try:
        output, err = current_app.router_connection_manager.execute("echo 'NetPilot ping'", timeout=5)
        if err:
            logger.error(f"Router reachability check failed: {err}")
            return build_error_response(f"Router not reachable: {err}", 500, "ROUTER_UNREACHABLE", execution_start_time)

        # Ensure monitoring infra (scripts + daemon) is present and running
        from utils.infrastructure_setup import check_existing_infrastructure, setup_persistent_infrastructure, InfrastructureComponent
        infra_ok, missing_components, message = check_existing_infrastructure()
        if not infra_ok:
            # Only monitoring is supported; set it up if missing
            if InfrastructureComponent.MONITORING_SETUP in missing_components:
                success_status, error_msg = setup_persistent_infrastructure([InfrastructureComponent.MONITORING_SETUP])
                if not success_status:
                    return build_error_response(f"Monitoring setup failed: {error_msg}", 500, "INFRASTRUCTURE_SETUP_FAILED", execution_start_time)

        logger.info(f"Session established successfully for router {g.router_id} (headless mode, monitoring ready)")
        return build_success_response({
            "session_id": g.session_id,
            "router_reachable": True,
            "monitoring_ready": True,
            "message": "Session established successfully"
        }, execution_start_time)

    except Exception as e:
        logger.error(f"Session setup failed: {str(e)}")
        return build_error_response(f"Session setup failed: {str(e)}", 500, "SESSION_SETUP_FAILED", execution_start_time)

@session_bp.route("/end", methods=["POST"])
def end_session():
    """
    Ends the session for a router, cleaning up its connections.
    """
    execution_start_time = time.time()
    logger = current_app.logger
    logger.info(f"Ending session {g.session_id} for router {g.router_id}")
    
    current_app.router_connection_manager.end_session(g.session_id)
    
    return build_success_response({"message": "Session ended"}, execution_start_time)

@session_bp.route("/refresh", methods=["POST"])
def refresh_session():
    """Refreshes a session's activity timer."""
    execution_start_time = time.time()
    data = request.get_json()
    session_id = data.get('sessionId') if data else None
    if not session_id:
        return build_error_response("sessionId is required", 400, "MISSING_SESSION_ID", execution_start_time)

    try:
        refreshed = current_app.router_connection_manager.refresh_session(session_id)
        if refreshed:
            logger.info(f"Session refreshed: {session_id}")
            return build_success_response({"message": f"Session {session_id} refreshed"}, execution_start_time)
        else:
            logger.warning(f"Attempted to refresh non-existent session: {session_id}")
            return build_error_response("Session not found", 404, "SESSION_NOT_FOUND", execution_start_time)
    except Exception as e:
        logger.error(f"Error refreshing session {session_id}: {e}", exc_info=True)
        return build_error_response(str(e), 500, "SESSION_REFRESH_ERROR", execution_start_time)

@session_bp.route("/status", methods=["GET"])
def get_all_sessions_status():
    """
    Retrieves the status of all active sessions being managed.
    This is an admin-level endpoint and does not require session context.
    """
    execution_start_time = time.time()
    status = current_app.router_connection_manager.get_all_sessions_status()
    return build_success_response({"message": "Retrieved all session statuses", "sessions": status}, execution_start_time)