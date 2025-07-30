"""
Base commands server operations and communication management

Provides shared commands server communication utilities for all commands server operations.
This module ensures consistent command execution, error handling, and response processing
across all commands server operation services.
"""

from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, ParamSpec
from utils.logging_config import get_logger

logger = get_logger('services.commands_server_operations.base')

# Type hints for decorator
P = ParamSpec('P')
T = TypeVar('T')


def with_commands_server(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to inject commands server manager into function.
    
    This decorator automatically provides access to the commands server manager
    for functions that need to communicate with the commands server.
    
    Usage:
        @with_commands_server
        def my_command_function(commands_server, router_id: str, command: str):
            return commands_server.execute_router_command(router_id, command)
    
    Args:
        func: Function that expects commands_server as first parameter
        
    Returns:
        Wrapped function with automatic commands server injection
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Lazy import to avoid circular dependency
        from managers.commands_server_manager import commands_server_manager
        # Inject commands server manager as first argument
        return func(commands_server_manager, *args, **kwargs)
    return wrapper


def handle_commands_errors(operation_name: str):
    """
    Decorator for consistent commands server error handling.
    
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


def validate_router_connection(commands_server, router_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that the router is connected and reachable.
    
    Args:
        commands_server: Commands server manager instance
        router_id: Router ID to validate
        
    Returns:
        Tuple of (is_connected, error_message)
    """
    try:
        # Test connection to the router
        is_connected, error = commands_server.test_connection()
        if not is_connected:
            return False, f"Commands server connection failed: {error}"
        
        # Check router status
        status, error = commands_server.get_router_status(router_id)
        if not status:
            return False, f"Router {router_id} is not accessible: {error}"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Router connection validation failed: {e}", exc_info=True)
        return False, f"Router connection validation error: {str(e)}"


def format_command_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format and standardize command response data.
    
    Args:
        response_data: Raw response data from commands server
        
    Returns:
        Formatted response dictionary
    """
    if not response_data:
        return {'success': False, 'message': 'No response data'}
    
    try:
        # Standard response format
        formatted_response = {
            'success': response_data.get('success', False),
            'message': response_data.get('message', ''),
            'data': response_data.get('data', {}),
            'timestamp': response_data.get('timestamp'),
            'router_id': response_data.get('router_id'),
            'command': response_data.get('command')
        }
        
        # Include any error information
        if 'error' in response_data:
            formatted_response['error'] = response_data['error']
        
        return formatted_response
        
    except Exception as e:
        logger.error(f"Failed to format command response: {e}")
        return {
            'success': False, 
            'message': f'Response formatting error: {str(e)}',
            'raw_data': response_data
        }


def log_command_execution(router_id: str, command: str, params: Optional[Dict[str, Any]] = None, 
                         success: bool = True, error: Optional[str] = None):
    """
    Log command execution for audit and debugging purposes.
    
    Args:
        router_id: Router ID where command was executed
        command: Command that was executed
        params: Command parameters
        success: Whether the command succeeded
        error: Error message if command failed
    """
    try:
        log_data = {
            'router_id': router_id,
            'command': command,
            'params': params or {},
            'success': success
        }
        
        if success:
            logger.info(f"Command executed successfully on router {router_id}: {command}", extra=log_data)
        else:
            logger.error(f"Command failed on router {router_id}: {command} - {error}", extra=log_data)
            
    except Exception as e:
        logger.error(f"Failed to log command execution: {e}")


def execute_router_command(commands_server, router_id: str, session_id: str, command: str, 
                          sub_command: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Execute a command on a router through the commands server.
    
    Args:
        commands_server: Commands server manager instance
        router_id: Router ID to execute command on
        session_id: Session ID for the command
        command: Main command to execute
        sub_command: Sub-command if applicable
        params: Command parameters
        
    Returns:
        Tuple of (response_data, error_message)
    """
    try:
        # If commands_server is None, use lazy import
        if commands_server is None:
            from managers.commands_server_manager import commands_server_manager
            commands_server = commands_server_manager
            
        # Validate router connection first
        is_connected, conn_error = validate_router_connection(commands_server, router_id)
        if not is_connected:
            log_command_execution(router_id, command, params, False, conn_error)
            return None, conn_error
        
        # Execute the command
        response_data, error = commands_server.execute_router_command(
            router_id, session_id, command, sub_command, params
        )
        
        if response_data:
            formatted_response = format_command_response(response_data)
            log_command_execution(router_id, command, params, True)
            return formatted_response, None
        else:
            log_command_execution(router_id, command, params, False, error)
            return None, error
            
    except Exception as e:
        error_msg = f"Router command execution failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        log_command_execution(router_id, command, params, False, error_msg)
        return None, error_msg


def get_router_status(commands_server, router_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Get the current status of a router.
    
    Args:
        commands_server: Commands server manager instance
        router_id: Router ID to get status for
        
    Returns:
        Tuple of (status_data, error_message)
    """
    try:
        # If commands_server is None, use lazy import
        if commands_server is None:
            from managers.commands_server_manager import commands_server_manager
            commands_server = commands_server_manager
            
        status_data, error = commands_server.get_router_status(router_id)
        
        if status_data:
            return status_data, None
        else:
            return None, error
            
    except Exception as e:
        error_msg = f"Failed to get router status: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg
