"""
Base database operations and session management

Provides shared database session management and utilities for all DB operations.
This module ensures consistent session handling, transaction management, and error handling
across all database operation services.
"""

from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, TypeVar, ParamSpec
from database.session import get_db_session as _get_db_session
from utils.logging_config import get_logger

logger = get_logger('services.db_operations.base')

# Type hints for decorator
P = ParamSpec('P')
T = TypeVar('T')


@contextmanager
def get_db_session():
    """
    Get database session with automatic cleanup and transaction management.
    
    This context manager ensures proper session lifecycle:
    - Automatic commit on success
    - Automatic rollback on exception
    - Proper session cleanup
    
    Usage:
        with get_db_session() as session:
            # Perform database operations
            result = session.query(Model).all()
    
    Yields:
        SQLAlchemy session object
    """
    session = _get_db_session()
    try:
        logger.debug("Database session started")
        yield session
        session.commit()
        logger.debug("Database session committed successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Database operation failed, rolled back: {e}")
        raise
    finally:
        session.close()
        logger.debug("Database session closed")


def with_db_session(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to inject database session as the first parameter into function.
    
    This decorator automatically handles session management for database operation functions.
    The decorated function will receive a session as its first parameter.
    
    Usage:
        @with_db_session
        def my_db_function(session, user_id: str, other_param: str):
            return session.query(User).filter_by(id=user_id).first()
    
    Args:
        func: Function that expects session as first parameter
        
    Returns:
        Wrapped function with automatic session injection
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_db_session() as session:
            # Inject session as first argument
            return func(session, *args, **kwargs)
    return wrapper


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
