"""
Example Usage of Whitelist Service

This file demonstrates how to use the whitelist service with the new decorator-based architecture.
All service functions now require user_id, router_id, and session_id as the first three parameters.
"""

from services.whitelist_service import (
    get_whitelist,
    add_device_to_whitelist,
    remove_device_from_whitelist,
    get_whitelist_limit_rate,
    set_whitelist_limit_rate,
    activate_whitelist_mode,
    deactivate_whitelist_mode
)

# Example usage patterns:

def example_whitelist_operations():
    """
    Example of how to use the whitelist service functions.
    """
    # Required parameters for all service functions
    user_id = "123e4567-e89b-12d3-a456-426614174000"  # User UUID
    router_id = "987fcdeb-51a2-43d1-9876-ba9876543210"  # Router UUID
    session_id = "456e7890-e12b-34d5-a678-123456789abc"  # Session UUID
    
    # Example 1: Get current whitelist
    print("=== Getting current whitelist ===")
    whitelist, error = get_whitelist(user_id, router_id, session_id)
    if error:
        print(f"Error getting whitelist: {error}")
    else:
        print(f"Current whitelist: {whitelist}")
    
    # Example 2: Add a device to whitelist
    print("\n=== Adding device to whitelist ===")
    device_ip = "192.168.1.100"
    result, error = add_device_to_whitelist(user_id, router_id, session_id, device_ip)
    if error:
        print(f"Error adding device: {error}")
    else:
        print(f"Device added successfully: {result}")
    
    # Example 3: Remove a device from whitelist
    print("\n=== Removing device from whitelist ===")
    result, error = remove_device_from_whitelist(user_id, router_id, session_id, device_ip)
    if error:
        print(f"Error removing device: {error}")
    else:
        print(f"Device removed successfully: {result}")
    
    # Example 4: Get whitelist rate limit
    print("\n=== Getting whitelist rate limit ===")
    rate, error = get_whitelist_limit_rate(user_id, router_id, session_id)
    if error:
        print(f"Error getting rate limit: {error}")
    else:
        print(f"Current rate limit: {rate} Mbps")
    
    # Example 5: Set whitelist rate limit
    print("\n=== Setting whitelist rate limit ===")
    new_rate = 100  # 100 Mbps
    result, error = set_whitelist_limit_rate(user_id, router_id, session_id, new_rate)
    if error:
        print(f"Error setting rate limit: {error}")
    else:
        print(f"Rate limit set successfully: {result}")
    
    # Example 6: Activate whitelist mode
    print("\n=== Activating whitelist mode ===")
    result, error = activate_whitelist_mode(user_id, router_id, session_id)
    if error:
        print(f"Error activating whitelist mode: {error}")
    else:
        print(f"Whitelist mode activated: {result}")
    
    # Example 7: Deactivate whitelist mode
    print("\n=== Deactivating whitelist mode ===")
    result, error = deactivate_whitelist_mode(user_id, router_id, session_id)
    if error:
        print(f"Error deactivating whitelist mode: {error}")
    else:
        print(f"Whitelist mode deactivated: {result}")


def example_error_handling():
    """
    Example of error handling patterns with the service.
    """
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    router_id = "987fcdeb-51a2-43d1-9876-ba9876543210" 
    session_id = "456e7890-e12b-34d5-a678-123456789abc"
    
    # Example with invalid IP address
    result, error = add_device_to_whitelist(user_id, router_id, session_id, "invalid.ip")
    if error:
        print(f"Expected error for invalid IP: {error}")
    
    # Example with invalid rate
    result, error = set_whitelist_limit_rate(user_id, router_id, session_id, -1)
    if error:
        print(f"Expected error for invalid rate: {error}")
    
    # Example with missing parameters
    try:
        result, error = get_whitelist("", router_id, session_id)
        if error:
            print(f"Expected error for missing user_id: {error}")
    except Exception as e:
        print(f"Exception for missing parameters: {e}")


def example_api_endpoint_usage():
    """
    Example of how the service would be used in API endpoints.
    """
    def whitelist_endpoint_handler(request):
        """
        Example API endpoint handler using the whitelist service.
        """
        try:
            # Extract from request (example)
            user_id = request.user.id  # From authentication
            router_id = request.json.get('router_id')
            session_id = request.headers.get('Session-ID')
            
            # Validate required parameters
            if not all([user_id, router_id, session_id]):
                return {"error": "Missing required parameters"}, 400
            
            # Get whitelist using service
            whitelist, error = get_whitelist(user_id, router_id, session_id)
            if error:
                return {"error": error}, 500
            
            return {"whitelist": whitelist}, 200
            
        except Exception as e:
            return {"error": f"Internal server error: {str(e)}"}, 500
    
    def add_device_endpoint_handler(request):
        """
        Example API endpoint handler for adding devices.
        """
        try:
            # Extract from request
            user_id = request.user.id
            router_id = request.json.get('router_id')
            session_id = request.headers.get('Session-ID')
            device_ip = request.json.get('ip')
            
            # Validate parameters
            if not all([user_id, router_id, session_id, device_ip]):
                return {"error": "Missing required parameters"}, 400
            
            # Add device using service
            result, error = add_device_to_whitelist(user_id, router_id, session_id, device_ip)
            if error:
                return {"error": error}, 400 if "already" in error else 500
            
            return {"result": result}, 200
            
        except Exception as e:
            return {"error": f"Internal server error: {str(e)}"}, 500


if __name__ == "__main__":
    # Note: This is just an example, the actual functions require proper authentication
    # and database/commands server setup to work
    print("Whitelist Service Usage Examples")
    print("=" * 50)
    
    # Uncomment to run examples (requires proper setup):
    # example_whitelist_operations()
    # example_error_handling()
    
    print("\nService functions are ready to use with the following signature:")
    print("function_name(user_id: str, router_id: str, session_id: str, *other_params)")
    print("\nAll functions return: (result, error) tuple")
    print("If error is None, the operation succeeded")
    print("If error is not None, the operation failed with the given error message")
