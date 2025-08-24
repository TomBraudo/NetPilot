"""
SessionContext - contextvars-backed holder for the current SQLAlchemy session.

Usage:
  from managers.db_session_context import SessionContext
  SessionContext.set(session)
  session = SessionContext.get()  # Now automatically creates session if none exists
  SessionContext.clear()

Optional helpers:
  with with_session(session):
      ...
"""

from contextlib import contextmanager
from typing import Optional, Any
import contextvars
from utils.logging_config import get_logger

logger = get_logger('managers.db_session_context')

_session_var: contextvars.ContextVar[Optional[Any]] = contextvars.ContextVar("np_db_session", default=None)


class SessionContext:
    @staticmethod
    def set(session: Any) -> None:
        _session_var.set(session)

    @staticmethod
    def get() -> Any:
        """
        Get the current database session, creating a new one if none exists.
        
        This allows the same code to work in both HTTP request contexts (where
        a session is already set) and scheduled task contexts (where no session exists).
        
        Returns:
            SQLAlchemy session object (never None)
        """
        session = _session_var.get()
        
        if session is None:
            # This should rarely happen if TransactionManager is used correctly
            logger.warning("SessionContext.get() auto-creating session - this may indicate a transaction management issue")
            try:
                from database.connection import db
                session = db.get_session()
                logger.debug("Auto-created database session for SessionContext.get()")
                # Don't set it in context - let the caller manage it explicitly
            except Exception as e:
                logger.error(f"Failed to create new database session: {e}")
                raise RuntimeError(f"Could not create database session: {e}")
        
        return session

    @staticmethod
    def clear() -> None:
        _session_var.set(None)

    @staticmethod
    def get_existing() -> Optional[Any]:
        """
        Get the existing session without creating a new one.
        Use this when you specifically want to check if a session exists.
        
        Returns:
            SQLAlchemy session object or None if no session exists
        """
        return _session_var.get()

    @staticmethod
    def is_managed() -> bool:
        """
        Check if we're currently in a managed transaction context.
        
        Returns:
            True if there's an active session in context, False otherwise
        """
        return _session_var.get() is not None

    @staticmethod
    def ensure_managed() -> None:
        """
        Ensure we're in a managed transaction context.
        
        Raises:
            RuntimeError: If no session is active in context
        """
        if not SessionContext.is_managed():
            raise RuntimeError("Database operation attempted outside managed transaction context")


@contextmanager
def with_session(session: Any):
    prev = _session_var.get()
    try:
        _session_var.set(session)
        yield session
    finally:
        _session_var.set(prev)


