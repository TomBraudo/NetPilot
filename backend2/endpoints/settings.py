from flask import Blueprint, request, g
from utils.response_helpers import build_success_response, build_error_response
from services.settings_service import save_router_id_setting
from utils.logging_config import get_logger
import time

# Set up logging
logger = get_logger(__name__)

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/router-id', methods=['POST'])
def save_router_id():
    start_time = time.time()
    logger.info(f"=== Starting save_router_id endpoint ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    # Get database session
    session = g.db_session
    logger.info(f"Database session obtained: {session}")
    
    # Get user_id from session
    user_id = getattr(g, 'user_id', None)
    logger.info(f"User ID from session: {user_id}")
    
    if not user_id:
        logger.error("User not authenticated - no user_id found in session")
        return build_error_response('User not authenticated', 401, 'UNAUTHORIZED', start_time)
    
    # Parse request body
    logger.info("Parsing request JSON body...")
    try:
        data = request.get_json()
        logger.info(f"Request body parsed: {data}")
    except Exception as e:
        logger.error(f"Failed to parse request JSON: {str(e)}")
        return build_error_response('Invalid JSON in request body', 400, 'BAD_REQUEST', start_time)
    
    if not data:
        logger.error("Request body is empty or None")
        return build_error_response('Missing request body', 400, 'BAD_REQUEST', start_time)
    
    # Extract router_id from request
    router_id = data.get('routerId')
    logger.info(f"Router ID extracted from request: {router_id}")
    
    if not router_id:
        logger.error("Missing routerId in request body")
        return build_error_response('Missing routerId', 400, 'BAD_REQUEST', start_time)
    
    logger.info(f"Calling save_router_id_setting service with user_id={user_id}, router_id={router_id}")
    
    # Call service logic
    try:
        result, error = save_router_id_setting(session, user_id, router_id)
        logger.info(f"Service call completed - result: {result}, error: {error}")
        
        if error:
            logger.error(f"Service returned error: {error}")
            return build_error_response(error, 400, 'SAVE_FAILED', start_time)
        
        logger.info(f"Service call successful, returning result: {result}")
        logger.info(f"=== save_router_id endpoint completed successfully ===")
        return build_success_response(result, start_time)
        
    except Exception as e:
        logger.error(f"Exception occurred in endpoint: {str(e)}", exc_info=True)
        logger.error(f"=== save_router_id endpoint failed ===")
        return build_error_response(f'Internal server error: {str(e)}', 500, 'INTERNAL_ERROR', start_time)

@settings_bp.route('/router-id', methods=['GET'])
def get_router_id():
    start_time = time.time()
    logger.info(f"=== Starting get_router_id endpoint ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Remote address: {request.remote_addr}")
    logger.info(f"User agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    # Get database session
    session = g.db_session
    logger.info(f"Database session obtained: {session}")
    
    # Get user_id from session
    user_id = getattr(g, 'user_id', None)
    logger.info(f"User ID from session: {user_id}")
    
    if not user_id:
        logger.error("User not authenticated - no user_id found in session")
        logger.error("Session attributes: %s", [attr for attr in dir(g) if not attr.startswith('_')])
        return build_error_response('User not authenticated', 401, 'UNAUTHORIZED', start_time)
    
    logger.info(f"Calling get_router_id_setting service with user_id={user_id}")
    
    try:
        from services.settings_service import get_router_id_setting
        result, error = get_router_id_setting(session, user_id)
        logger.info(f"Service call completed - result: {result}, error: {error}")
        
        if error:
            logger.warning(f"Service returned error: {error}")
            logger.info(f"No router ID found for user {user_id} - this is normal for first-time users")
            return build_error_response(error, 404, 'NOT_FOUND', start_time)
        
        logger.info(f"Service call successful, returning result: {result}")
        logger.info(f"=== get_router_id endpoint completed successfully ===")
        return build_success_response(result, start_time)
        
    except Exception as e:
        logger.error(f"Exception occurred in endpoint: {str(e)}", exc_info=True)
        logger.error(f"=== get_router_id endpoint failed ===")
        return build_error_response(f'Internal server error: {str(e)}', 500, 'INTERNAL_ERROR', start_time) 