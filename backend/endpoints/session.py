from flask import Blueprint, request, jsonify, current_app
from utils.logging_config import get_logger
from utils.response_helpers import success, error

logger = get_logger('session.endpoints')

session_bp = Blueprint('session', __name__)

@session_bp.route("/start", methods=["POST"])
def start_session():
    """Starts a new session in the connection manager."""
    data = request.get_json()
    session_id = data.get('sessionId')
    if not session_id:
        return jsonify(error("sessionId is required", 400))
    
    try:
        current_app.router_connection_manager.start_session(session_id)
        logger.info(f"Session started: {session_id}")
        return jsonify(success(f"Session {session_id} started successfully."))
    except Exception as e:
        logger.error(f"Error starting session {session_id}: {e}", exc_info=True)
        return jsonify(error(str(e), 500))

@session_bp.route("/end", methods=["POST"])
def end_session():
    """Ends a session, closing all associated router connections."""
    data = request.get_json()
    session_id = data.get('sessionId')
    if not session_id:
        return jsonify(error("sessionId is required", 400))

    try:
        current_app.router_connection_manager.end_session(session_id)
        logger.info(f"Session ended: {session_id}")
        return jsonify(success(f"Session {session_id} ended successfully."))
    except Exception as e:
        logger.error(f"Error ending session {session_id}: {e}", exc_info=True)
        return jsonify(error(str(e), 500))

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
def session_status():
    """Gets the status of a specific session or all sessions."""
    session_id = request.args.get('sessionId')
    
    try:
        if session_id:
            status = current_app.router_connection_manager.get_session_status(session_id)
            if status:
                return jsonify(success("Session status retrieved.", status))
            else:
                return jsonify(error("Session not found", 404))
        else:
            status = current_app.router_connection_manager.get_all_sessions_status()
            return jsonify(success("All sessions status retrieved.", status))
    except Exception as e:
        logger.error(f"Error getting session status: {e}", exc_info=True)
        return jsonify(error(str(e), 500)) 