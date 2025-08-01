from flask import Blueprint, request, g, session
from utils.response_helpers import build_success_response, build_error_response
from services.settings_service import save_router_id_setting, set_wifi_password
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
    
@settings_bp.route('/wifi-name', methods=['GET'])
def get_wifi_name():
    start_time = time.time()
    logger.info(f"=== Starting get_wifi_name endpoint ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request URL: {request.url}")
    
    # Get user_id from session
    user_id = getattr(g, 'user_id', None)
    logger.info(f"User ID from session: {user_id}")
    
    if not user_id:
        logger.error("User not authenticated - no user_id found in session")
        return build_error_response('User not authenticated', 401, 'UNAUTHORIZED', start_time)

    # Get router_id from query parameter or use a default
    router_id = request.args.get('routerId')
    if not router_id:
        # You can either require routerId as a parameter or get it from user context
        logger.error("Missing routerId parameter")
        return build_error_response('Router ID is required', 400, 'ROUTER_ID_MISSING', start_time)
    
    logger.info(f"Using router ID: {router_id}")
    
    # Use user_id as session_id
    session_id = user_id
    logger.info(f"Using session_id: {session_id}")

    logger.info(f"Calling get_wifi_name service with user_id={user_id}, router_id={router_id}, session_id={session_id}")
    
    try:
        from services.settings_service import get_wifi_name
        result, error = get_wifi_name(user_id, router_id, session_id)
        logger.info(f"Service call completed - result: {result}, error: {error}")
        
        if error:
            logger.warning(f"Service returned error: {error}")
            return build_error_response(error, 400, 'GET_WIFI_NAME_FAILED', start_time)
        
        # Format the response properly
        response_data = {
            'wifi_name': result,
            'ssid': result  # Provide both keys for compatibility
        }
        
        logger.info(f"Service call successful, returning result: {response_data}")
        logger.info(f"=== get_wifi_name endpoint completed successfully ===")
        return build_success_response(response_data, start_time)
        
    except Exception as e:
        logger.error(f"Exception occurred in endpoint: {str(e)}", exc_info=True)
        logger.error(f"=== get_wifi_name endpoint failed ===")
        return build_error_response(f'Internal server error: {str(e)}', 500, 'INTERNAL_ERROR', start_time)

@settings_bp.route('/wifi-name', methods=['POST'])
def update_wifi_name():
    start_time = time.time()
    logger.info(f"=== Starting update_wifi_name endpoint ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request URL: {request.url}")
    
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
    
    # Extract wifi_name and router_id from request
    wifi_name = data.get('wifi_name')
    router_id = data.get('router_id')
    
    logger.info(f"WiFi name extracted from request: {wifi_name}")
    logger.info(f"Router ID extracted from request: {router_id}")
    
    if not wifi_name:
        logger.error("Missing wifi_name in request body")
        return build_error_response('Missing wifi_name', 400, 'BAD_REQUEST', start_time)
    
    if not router_id:
        logger.error("Missing router_id in request body")
        return build_error_response('Missing router_id', 400, 'BAD_REQUEST', start_time)
    
    # Use user_id as session_id (same as GET method)
    session_id = user_id
    logger.info(f"Using session_id: {session_id}")
    
    logger.info(f"Calling update_wifi_name service with user_id={user_id}, router_id={router_id}, session_id={session_id}, wifi_name={wifi_name}")
    
    try:
        from services.settings_service import update_wifi_name
        result, error = update_wifi_name(user_id, router_id, session_id, wifi_name)
        logger.info(f"Service call completed - result: {result}, error: {error}")
        
        if error:
            logger.warning(f"Service returned error: {error}")
            return build_error_response(error, 400, 'UPDATE_WIFI_NAME_FAILED', start_time)
        
        # Format the response properly
        response_data = {
            'wifi_name': wifi_name,
            'message': 'WiFi name updated successfully'
        }
        
        logger.info(f"Service call successful, returning result: {response_data}")
        logger.info(f"=== update_wifi_name endpoint completed successfully ===")
        return build_success_response(response_data, start_time)
        
    except Exception as e:
        logger.error(f"Exception occurred in endpoint: {str(e)}", exc_info=True)
        logger.error(f"=== update_wifi_name endpoint failed ===")
        return build_error_response(f'Internal server error: {str(e)}', 500, 'INTERNAL_ERROR', start_time)
    

@settings_bp.route('/wifi-password', methods=['POST'])
def set_wifi_password_endpoint():
    start_time = time.time()
    logger.info(f"=== Starting set_wifi_password endpoint ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request URL: {request.url}")
    
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
    
    # Extract password from request (as per user requirement: {password: <password>})
    wifi_password = data.get('password')
    router_id = data.get('router_id')  # Keep router_id for backward compatibility, but make it optional
    
    logger.info(f"WiFi password extracted from request: {wifi_password}")
    logger.info(f"Router ID extracted from request: {router_id}")
    
    if not wifi_password:
        logger.error("Missing password in request body")
        return build_error_response('Missing password', 400, 'BAD_REQUEST', start_time)
    
    # If router_id not provided in body, try to get it from user's stored settings
    if not router_id:
        logger.info("No router_id in request body, trying to get from user's stored settings")
        try:
            from services.settings_service import get_router_id_setting
            router_result, router_error = get_router_id_setting(g.db_session, user_id)
            if router_error or not router_result:
                logger.error("No router_id found in request and no stored router_id for user")
                return build_error_response('Router ID is required. Please set your router ID first.', 400, 'ROUTER_ID_REQUIRED', start_time)
            router_id = router_result.get('router_id')
            logger.info(f"Retrieved stored router_id for user: {router_id}")
        except Exception as e:
            logger.error(f"Error retrieving stored router_id: {str(e)}")
            return build_error_response('Router ID is required', 400, 'ROUTER_ID_REQUIRED', start_time)
    
    # Use user_id as session_id (same as GET method)
    session_id = user_id
    logger.info(f"Using session_id: {session_id}")
    
    logger.info(f"Calling set_wifi_password service with user_id={user_id}, router_id={router_id}, session_id={session_id}, wifi_password={wifi_password}")
    
    try:
        result, error = set_wifi_password(user_id, router_id, session_id, wifi_password)
        logger.info(f"Service call completed - result: {result}, error: {error}")
        if error:
            logger.warning(f"Service returned error: {error}")
            return build_error_response(error, 400, 'SET_WIFI_PASSWORD_FAILED', start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Exception occurred in service call: {str(e)}", exc_info=True)
        return build_error_response(f'Internal server error: {str(e)}', 500, 'INTERNAL_ERROR', start_time)