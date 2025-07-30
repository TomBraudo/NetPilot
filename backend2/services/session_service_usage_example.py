"""
Example Usage of Session Service

This file demonstrates how to use the session service with the new conductor-based architecture.
All service functions now require user_id, router_id, and session_id as the first three parameters.
"""

from services.session_service import (
    start_session,
    end_session,
    refresh_session
)

# Example usage patterns:

def example_session_operations():
    """
    Example of how to use the session service functions.
    """
    # Required parameters for all service functions
    user_id = "123e4567-e89b-12d3-a456-426614174000"  # User UUID
    router_id = "987fcdeb-51a2-43d1-9876-ba9876543210"  # Router UUID
    session_id = "456e7890-e12b-34d5-a678-123456789abc"  # Session UUID
    
    # Example 1: Start a session
    print("=== Starting session ===")
    result, error = start_session(user_id, router_id, session_id, restart=False)
    if error:
        print(f"Error starting session: {error}")
    else:
        print(f"Session started successfully: {result}")
    
    # Example 2: Start a session with restart flag
    print("\n=== Starting session with restart ===")
    result, error = start_session(user_id, router_id, session_id, restart=True)
    if error:
        print(f"Error starting session: {error}")
    else:
        print(f"Session restarted successfully: {result}")
    
    # Example 3: Refresh a session
    print("\n=== Refreshing session ===")
    result, error = refresh_session(user_id, router_id, session_id)
    if error:
        print(f"Error refreshing session: {error}")
    else:
        print(f"Session refreshed successfully: {result}")
    
    # Example 4: End a session
    print("\n=== Ending session ===")
    result, error = end_session(user_id, router_id, session_id)
    if error:
        print(f"Error ending session: {error}")
    else:
        print(f"Session ended successfully: {result}")


def example_error_handling():
    """
    Example of error handling patterns with the session service.
    """
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    router_id = "987fcdeb-51a2-43d1-9876-ba9876543210"
    session_id = "456e7890-e12b-34d5-a678-123456789abc"
    
    print("\n=== Error Handling Examples ===")
    
    # All session service functions return (result, error) tuples
    # Always check the error value first
    result, error = start_session(user_id, router_id, session_id)
    
    if error is not None:
        print(f"Operation failed: {error}")
        # Handle error appropriately (log, retry, return error response, etc.)
        return
    
    # Only proceed if no error occurred
    print(f"Operation succeeded: {result}")
    
    # Error checking pattern for all operations
    operations = [
        ("Start session", lambda: start_session(user_id, router_id, session_id)),
        ("Refresh session", lambda: refresh_session(user_id, router_id, session_id)),
        ("End session", lambda: end_session(user_id, router_id, session_id))
    ]
    
    for operation_name, operation_func in operations:
        result, error = operation_func()
        if error:
            print(f"{operation_name} failed: {error}")
        else:
            print(f"{operation_name} succeeded: {result}")


def example_api_endpoint_usage():
    """
    Example of how the session service would be used in API endpoints.
    """
    from flask import g, request
    from utils.response_helpers import build_success_response, build_error_response
    import time
    
    def start_session_endpoint():
        """Example API endpoint using session service"""
        start_time = time.time()
        
        # Get parameters from request
        data = request.get_json() or {}
        restart = data.get('restart', False)
        
        # Use context from middleware (user_id, router_id, session_id from g object)
        result, error = start_session(g.user_id, g.router_id, g.session_id, restart)
        
        if error:
            return build_error_response(f"Session start failed: {error}", 500, "SESSION_START_FAILED", start_time)
        
        return build_success_response(result, start_time)
    
    def end_session_endpoint():
        """Example API endpoint using session service"""
        start_time = time.time()
        
        # Use context from middleware
        result, error = end_session(g.user_id, g.router_id, g.session_id)
        
        if error:
            return build_error_response(f"Session end failed: {error}", 500, "SESSION_END_FAILED", start_time)
        
        return build_success_response(result, start_time)
    
    print("Session service integrated into API endpoints")


if __name__ == "__main__":
    # Note: This is just an example, the actual functions require proper authentication
    # and commands server setup to work
    print("Session Service Usage Examples")
    print("=" * 50)
    
    try:
        example_session_operations()
        example_error_handling()
        example_api_endpoint_usage()
    except ImportError as e:
        print(f"Could not run examples due to missing dependencies: {e}")
        print("This is expected if not running in the full application context")
