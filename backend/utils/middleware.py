from functools import wraps
from flask import g, request
import time
from utils.response_helpers import build_error_response
from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager

logger = get_logger('middleware')
router_connection_manager = RouterConnectionManager()

def router_context_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        session_id = request.args.get('sessionId') or request.json.get('sessionId')
        router_id = request.args.get('routerId') or request.json.get('routerId')

        if not session_id or not router_id:
            return build_error_response("sessionId and routerId are required", 400, "BAD_REQUEST", start_time)

        g.session_id = session_id
        g.router_id = router_id
        
        if not router_connection_manager.get_session_status(session_id):
            return build_error_response("Session is not active or has expired", 401, "SESSION_INVALID", start_time)
            
        try:
            # The decorated function will now have session_id and router_id in `g`
            # and can call manager.execute() safely.
            # The try-except for RuntimeError is now handled inside the service calls 
            # or can be wrapped here if we want to catch it at the middleware level.
            # For now, let's assume services handle the execute() call and its exceptions.
            return f(*args, **kwargs)
        except RuntimeError as e:
            logger.error(f"Connection error for router {router_id} in session {session_id}: {e}", exc_info=True)
            return build_error_response(str(e), 503, "TUNNEL_OR_ROUTER_UNAVAILABLE", start_time)
        except Exception as e:
            logger.error(f"Unexpected error for router {router_id}: {e}", exc_info=True)
            return build_error_response("An unexpected server error occurred", 500, "UNEXPECTED_SERVER_ERROR", start_time)
            
    return decorated_function 