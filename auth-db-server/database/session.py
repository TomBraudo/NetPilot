from contextlib import contextmanager
from managers.db_session_context import SessionContext

@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    
    Now uses SessionContext.get() which automatically creates a session if needed.
    The session will be automatically managed by the TransactionManager in HTTP requests.
    """
    session = SessionContext.get()
    try:
        yield session
        # Note: commit/rollback is handled by TransactionManager in HTTP requests
        # For standalone usage, you may need to manually commit
    except Exception:
        # Note: rollback is handled by TransactionManager in HTTP requests
        # For standalone usage, you may need to manually rollback
        raise
    finally:
        # Note: session cleanup is handled by TransactionManager in HTTP requests
        # For standalone usage, you may need to manually close
        pass

def get_db():
    """
    Dependency for FastAPI/Flask.
    
    Now uses SessionContext.get() which automatically creates a session if needed.
    The session will be automatically managed by the TransactionManager in HTTP requests.
    """
    session = SessionContext.get()
    try:
        yield session
    finally:
        # Note: session cleanup is handled by TransactionManager in HTTP requests
        # For standalone usage, you may need to manually close
        pass 