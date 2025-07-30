"""
Base Service Layer - Service Orchestration Framework

This module provides the core orchestration framework for services that coordinate
between database operations and commands server operations.

This follows the 3-layer architecture:
1. Services (this layer) - orchestration and business logic
2. services/db_operations/ - Database operations
3. services/commands_server_operations/ - Router command execution
"""

from functools import wraps
from typing import Any, Callable, TypeVar, ParamSpec, Optional, Tuple
from utils.logging_config import get_logger

logger = get_logger('services.base')

# Type hints for decorators
P = ParamSpec('P')
T = TypeVar('T')


def require_user_context(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to validate user context is provided.
    
    This decorator ensures that user_id, router_id, and session_id are provided
    and valid before executing the service function.
    
    Usage:
        @require_user_context
        def my_service_function(user_id: str, router_id: str, session_id: str, other_param: str):
            # Function implementation
            pass
    
    Args:
        func: Function that requires user context
        
    Returns:
        Wrapped function with user context validation
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if len(args) < 3:
            return None, "Missing required parameters: user_id, router_id, session_id"
        
        user_id = args[0]
        router_id = args[1]
        session_id = args[2]
        
        # Validate user context
        if not user_id:
            return None, "user_id is required"
        if not router_id:
            return None, "router_id is required" 
        if not session_id:
            return None, "session_id is required"
        
        # Validate UUID format if needed
        try:
            import uuid
            uuid.UUID(user_id)
            uuid.UUID(router_id)
            uuid.UUID(session_id)
        except (ValueError, TypeError):
            return None, "Invalid UUID format for user_id, router_id, or session_id"
        
        return func(*args, **kwargs)
    
    return wrapper


def handle_service_errors(operation_name: str):
    """
    Decorator for consistent service error handling and logging.
    
    Args:
        operation_name: Name of the operation for logging purposes
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"{operation_name} failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return None, error_msg
        return wrapper
    return decorator


def validate_ip_address(ip_address: str) -> bool:
    """
    Validate IP address format.
    
    Args:
        ip_address: IP address string to validate
        
    Returns:
        True if valid IP address, False otherwise
    """
    try:
        import ipaddress
        ipaddress.ip_address(ip_address)
        return True
    except (ValueError, TypeError):
        return False


def validate_rate_limit(rate: int) -> bool:
    """
    Validate rate limit value.
    
    Args:
        rate: Rate limit in Mbps
        
    Returns:
        True if valid rate, False otherwise
    """
    try:
        rate_int = int(rate)
        return 1 <= rate_int <= 1000  # Reasonable range for rate limits
    except (ValueError, TypeError):
        return False


def log_service_operation(operation_name: str, user_id: str, router_id: str, 
                         session_id: str, params: Optional[dict] = None,
                         success: bool = True, error: Optional[str] = None):
    """
    Log service operation for audit and debugging purposes.
    
    Args:
        operation_name: Name of the operation
        user_id: User ID
        router_id: Router ID
        session_id: Session ID
        params: Operation parameters
        success: Whether the operation succeeded
        error: Error message if operation failed
    """
    try:
        log_data = {
            'operation': operation_name,
            'user_id': user_id,
            'router_id': router_id,
            'session_id': session_id,
            'params': params or {},
            'success': success
        }
        
        if success:
            logger.info(f"Service operation completed: {operation_name}", extra=log_data)
        else:
            logger.error(f"Service operation failed: {operation_name} - {error}", extra=log_data)
            
    except Exception as e:
        logger.error(f"Failed to log service operation: {e}")
