"""
SessionContext - contextvars-backed holder for the current SQLAlchemy session.

Usage:
  from managers.db_session_context import SessionContext
  SessionContext.set(session)
  session = SessionContext.get()
  SessionContext.clear()

Optional helpers:
  with with_session(session):
      ...
"""

from contextlib import contextmanager
from typing import Optional, Any
import contextvars


_session_var: contextvars.ContextVar[Optional[Any]] = contextvars.ContextVar("np_db_session", default=None)


class SessionContext:
    @staticmethod
    def set(session: Any) -> None:
        _session_var.set(session)

    @staticmethod
    def get() -> Optional[Any]:
        return _session_var.get()

    @staticmethod
    def clear() -> None:
        _session_var.set(None)


@contextmanager
def with_session(session: Any):
    prev = _session_var.get()
    try:
        _session_var.set(session)
        yield session
    finally:
        _session_var.set(prev)


