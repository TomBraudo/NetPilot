from functools import wraps
from flask import g, request
import time
from utils.response_helpers import build_error_response
from utils.logging_config import get_logger

logger = get_logger('middleware')

def router_context_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        # Allow OPTIONS requests (CORS preflight) to pass through immediately
        if request.method == 'OPTIONS':
            return '', 200
        
        # 1. Validate user authentication first
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            logger.warning("Router context request without user authentication")
            return build_error_response("User authentication required", 401, "UNAUTHENTICATED", start_time)
        
        # 2. Extract routerId (still required from client)
        router_id = request.args.get('routerId') or (request.json or {}).get('routerId')
        if not router_id:
            logger.warning(f"Router context request missing routerId for user {user_id}")
            return build_error_response("routerId is required", 400, "BAD_REQUEST", start_time)
        
        # 3. Use user_id as session_id (no longer extract sessionId from client)
        g.session_id = str(user_id)  # User ID becomes session ID
        g.router_id = router_id
        
        logger.debug(f"Router context established: user_id={user_id}, router_id={router_id}, session_id={g.session_id}")
        
        # 4. Optional: Validate router belongs to user (future enhancement)
        # validate_user_router_access(user_id, router_id)
        
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Unexpected error for router {router_id} and user {user_id}: {e}", exc_info=True)
            return build_error_response("An unexpected server error occurred", 500, "UNEXPECTED_SERVER_ERROR", start_time)
            
    return decorated_function 