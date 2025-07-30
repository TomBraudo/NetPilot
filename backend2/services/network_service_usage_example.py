"""
Example Usage of Network Service

This file demonstrates how to use the network service with the new conductor-based architecture.
All service functions require user_id, router_id, and session_id as the first three parameters.

This service focuses exclusively on network scanning functionality.
"""

from services.network_service import scan_network

# Example usage patterns:

def example_network_operations():
    """
    Example of how to use the network service functions.
    """
    # Required parameters for all service functions
    user_id = "123e4567-e89b-12d3-a456-426614174000"  # User UUID
    router_id = "987fcdeb-51a2-43d1-9876-ba9876543210"  # Router UUID
    session_id = "456e7890-e12b-34d5-a678-123456789abc"  # Session UUID
    
    # Example: Scan network for connected devices
    print("=== Scanning network for connected devices ===")
    devices, error = scan_network(user_id, router_id, session_id)
    if error:
        print(f"Error scanning network: {error}")
    else:
        print(f"Network scan successful, found {len(devices)} devices:")
        for device in devices:
            ip = device.get('ip', 'Unknown IP')
            mac = device.get('mac', 'Unknown MAC')
            hostname = device.get('hostname', 'Unknown hostname')
            print(f"  - {ip} ({mac}) - {hostname}")


def example_error_handling():
    """
    Example of error handling patterns with the network service.
    """
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    router_id = "987fcdeb-51a2-43d1-9876-ba9876543210"
    session_id = "456e7890-e12b-34d5-a678-123456789abc"
    
    print("\n=== Error Handling Examples ===")
    
    # Network service functions return (result, error) tuples
    # Always check the error value first
    result, error = scan_network(user_id, router_id, session_id)
    
    if error is not None:
        print(f"Network scan failed: {error}")
        # Handle error appropriately (log, retry, return error response, etc.)
        return
    
    # Only proceed if no error occurred
    print(f"Network scan succeeded, found {len(result)} devices")
    
    # Process the results
    for device in result:
        print(f"Device: {device}")


def example_api_endpoint_usage():
    """
    Example of how the network service would be used in API endpoints.
    """
    from flask import g, request
    from utils.response_helpers import build_success_response, build_error_response
    import time
    
    def scan_network_endpoint():
        """Example API endpoint using network service"""
        start_time = time.time()
        
        # Use context from middleware (user_id, router_id, session_id from g object)
        result, error = scan_network(g.user_id, g.router_id, g.session_id)
        
        if error:
            return build_error_response(f"Network scan failed: {error}", 500, "NETWORK_SCAN_FAILED", start_time)
        
        return build_success_response(result, start_time)
    
    print("Network service integrated into API endpoints")


if __name__ == "__main__":
    # Note: This is just an example, the actual functions require proper authentication
    # and commands server setup to work
    print("Network Service Usage Examples")
    print("=" * 50)
    
    try:
        example_network_operations()
        example_error_handling()
        example_api_endpoint_usage()
    except ImportError as e:
        print(f"Could not run examples due to missing dependencies: {e}")
        print("This is expected if not running in the full application context")
