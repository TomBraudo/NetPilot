from flask import Blueprint, request, jsonify, current_app, g
from utils.logging_config import get_logger
from utils.response_helpers import success, error
from services.router_setup_service import setup_router_infrastructure

logger = get_logger('session.endpoints')

session_bp = Blueprint('session', __name__)

@session_bp.route("/start", methods=["POST"])
def start_session():
    """
    Starts a new session for a router and sets up the required infrastructure.
    This endpoint now requires the session context from the middleware.
    """
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
        return error("Session is already active", status_code=400)

    # 1. Mark the session as active in the RouterConnectionManager first.
    current_app.router_connection_manager.start_session(g.session_id)

    # 2. Quick reachability check and state file setup only (skip heavy infrastructure)
    logger.info("Performing quick router reachability check...")
    
    try:
        # Test basic connectivity with short timeout
        output, err = current_app.router_connection_manager.execute("echo 'NetPilot ping'", timeout=5)
        if err:
            logger.error(f"Router reachability check failed: {err}")
            return error(f"Router not reachable: {err}", status_code=500)
        
        # Quick state file check only (don't create heavy infrastructure)
        logger.info("Checking state file status...")
        state_output, state_err = current_app.router_connection_manager.execute(
            "[ -f /etc/config/netpilot_state.json ] && echo 'exists' || echo 'missing'", timeout=3)
        
        state_status = state_output.strip() if state_output else "unknown"
        logger.info(f"State file status: {state_status}")
        
        logger.info(f"Session established successfully for router {g.router_id} (lightweight setup)")
        return success("Session established successfully", data={
            "session_id": g.session_id,
            "router_reachable": True,
            "state_file_status": state_status,
            "note": "Infrastructure will be set up on first mode activation"
        })
        
    except Exception as e:
        logger.error(f"Session setup failed: {str(e)}")
        return error(f"Session setup failed: {str(e)}", status_code=500)

@session_bp.route("/end", methods=["POST"])
def end_session():
    """
    Ends the session for a router, cleaning up its connections.
    """
    logger = current_app.logger
    logger.info(f"Ending session {g.session_id} for router {g.router_id}")
    
    current_app.router_connection_manager.close_connection(g.session_id, g.router_id)
    
    return success("Session ended.")

@session_bp.route("/refresh", methods=["POST"])
def refresh_session():
    """Refreshes a session's activity timer."""
    data = request.get_json()
    session_id = data.get('sessionId')
    if not session_id:
        return jsonify(error("sessionId is required", 400))

    try:
        refreshed = current_app.router_connection_manager.refresh_session(session_id)
        if refreshed:
            logger.info(f"Session refreshed: {session_id}")
            return jsonify(success(f"Session {session_id} refreshed."))
        else:
            logger.warning(f"Attempted to refresh non-existent session: {session_id}")
            return jsonify(error("Session not found", 404))
    except Exception as e:
        logger.error(f"Error refreshing session {session_id}: {e}", exc_info=True)
        return jsonify(error(str(e), 500))

@session_bp.route("/status", methods=["GET"])
def get_all_sessions_status():
    """
    Retrieves the status of all active sessions being managed.
    This is an admin-level endpoint and does not require session context.
    """
    status = current_app.router_connection_manager.get_all_sessions_status()
    return success("Retrieved all session statuses.", status) 