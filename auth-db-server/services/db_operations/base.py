"""
Base database utilities

Provides shared utilities for DB operation modules. Session and transaction
management are centralized via `managers/transaction_manager.py` and
`managers/db_session_context.py`. DB ops must NOT commit/rollback/close.
"""

from functools import wraps
from typing import Any, Callable, TypeVar, ParamSpec
from utils.logging_config import get_logger

logger = get_logger('services.db_operations.base')

# Type hints for decorator
P = ParamSpec('P')
T = TypeVar('T')


# Session lifecycle has been centralized. No session helpers here by design.


def safe_dict_conversion(model_instance, exclude_fields=None):
    """
    Safely convert SQLAlchemy model instance to dictionary.
    
    Handles UUID serialization and excludes sensitive fields.
    
    Args:
        model_instance: SQLAlchemy model instance
        exclude_fields: List of field names to exclude from conversion
        
    Returns:
        Dictionary representation of the model
    """
    if not model_instance:
        return None
    
    exclude_fields = exclude_fields or []
    result = {}
    
    try:
        for column in model_instance.__table__.columns:
            if column.name in exclude_fields:
                continue
                
            value = getattr(model_instance, column.name)
            
            # Handle UUID serialization
            if hasattr(value, 'hex'):  # UUID objects
                result[column.name] = str(value)
            else:
                result[column.name] = value
                
        return result
    except Exception as e:
        logger.error(f"Failed to convert model to dict: {e}")
        return None


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID string format.
    
    Args:
        uuid_string: String to validate as UUID
        
    Returns:
        True if valid UUID, False otherwise
    """
    try:
        import uuid
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False


def handle_db_errors(operation_name: str):
    """
    Decorator for consistent database error handling.
    
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
