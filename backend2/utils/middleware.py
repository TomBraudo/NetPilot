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
        session_id = request.args.get('sessionId') or (request.json or {}).get('sessionId')
        router_id = request.args.get('routerId') or (request.json or {}).get('routerId')

        if not session_id or not router_id:
            return build_error_response("sessionId and routerId are required", 400, "BAD_REQUEST", start_time)

        g.session_id = session_id
        g.router_id = router_id
        
        # For now, we'll just validate that the parameters exist
        # In a real implementation, you would validate the session here
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Unexpected error for router {router_id}: {e}", exc_info=True)
            return build_error_response("An unexpected server error occurred", 500, "UNEXPECTED_SERVER_ERROR", start_time)
            
    return decorated_function 