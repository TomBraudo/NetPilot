from contextlib import contextmanager
from database.connection import db

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = db.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_db():
    """Dependency for FastAPI/Flask"""
    session = db.get_session()
    try:
        yield session
    finally:
        session.close() 