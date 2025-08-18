"""
Response Unpacking Helper

This helper provides functions to unpack responses from the commands server
which uses a standardized format with 'success', 'data', 'error', and 'metadata' fields.

Special Cases:
- SESSION_ALREADY_ACTIVE errors are treated as success to prevent retry loops
- This allows the session service to handle already-active sessions gracefully
"""

from typing import Dict, Any, Optional, Tuple
from utils.logging_config import get_logger

logger = get_logger('utils.response_unpack')

def unpack_commands_server_response(response_data: Optional[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Unpack a commands server response into data and error.
    
    Args:
        response_data: The response dictionary from the commands server
        
    Returns:
        Tuple of (data, error_message)
        - If successful: (data, None)
        - If error: (None, error_message)
    """
    if not response_data:
        return None, "No response data received"
    
    try:
        # Check if the response has the expected structure
        if not isinstance(response_data, dict):
            return None, "Invalid response format - not a dictionary"
        
        # Check for success field
        if 'success' not in response_data:
            return None, "Invalid response format - missing 'success' field"
        
        success = response_data.get('success', False)
        
        if success:
            # Extract data on success
            data = response_data.get('data')
            if data is None:
                logger.warning("Successful response but no data field")
                return {}, None
            return data, None
        else:
            # Extract error information on failure
            error_info = response_data.get('error', {})
            if isinstance(error_info, dict):
                error_message = error_info.get('message', 'Unknown error')
                error_code = error_info.get('code', 'UNKNOWN')
                
                # Special case: SESSION_ALREADY_ACTIVE should be treated as success
                if "SESSION_ALREADY_ACTIVE" in error_message:
                    logger.info(f"Treating SESSION_ALREADY_ACTIVE as success: {error_message}")
                    # Return the error info as data so the session service can handle it
                    return error_info, None
                
                return None, f"[{error_code}] {error_message}"
            else:
                # Check if the error string contains SESSION_ALREADY_ACTIVE
                if isinstance(error_info, str) and "SESSION_ALREADY_ACTIVE" in error_info:
                    logger.info(f"Treating SESSION_ALREADY_ACTIVE as success: {error_info}")
                    return {"message": error_info, "code": "SESSION_ALREADY_ACTIVE"}, None
                
                return None, "Command failed - no error details available"
                
    except Exception as e:
        logger.error(f"Error unpacking commands server response: {e}")
        return None, f"Error unpacking response: {str(e)}" 