"""
TransactionManager - centralizes DB session lifecycle and transaction policy
for both HTTP requests and scheduler jobs.

Web API:
  begin_request()                -> create session and bind to SessionContext
  finalize_response(response)    -> commit on success, rollback on error
  teardown()                     -> close session and clear context

Scheduler API:
  run(callable_fn) -> (result, error)
    - Create session, bind to SessionContext
    - Call fn()
    - Commit if success; rollback on error/exception
    - Always close and clear
"""

from typing import Any, Callable, Optional, Tuple
from decouple import config
from database.connection import db
from managers.db_session_context import SessionContext
from utils.logging_config import get_logger

logger = get_logger('managers.transaction_manager')


class TransactionManager:
    # -------- Web lifecycle --------
    @staticmethod
    def begin_request() -> None:
        session = db.get_session()
        SessionContext.set(session)

    @staticmethod
    def finalize_response(response: Any) -> Any:
        session = SessionContext.get_existing()  # Use get_existing to avoid auto-creation
        if session is None:
            return response

        try:
            # Expect JSON with {'success': bool} per project convention
            data = None
            try:
                data = response.get_json()
            except Exception:
                data = None

            is_success = False
            if isinstance(data, dict) and 'success' in data:
                is_success = bool(data.get('success'))
            else:
                # Fallback on HTTP status code
                is_success = int(getattr(response, 'status_code', 500)) < 400

            if is_success:
                session.commit()
            else:
                session.rollback()
        except Exception:
            try:
                session.rollback()
            except Exception:
                pass
        return response

    @staticmethod
    def teardown() -> None:
        session = SessionContext.get_existing()  # Use get_existing to avoid auto-creation
        if session is not None:
            try:
                session.close()
            finally:
                SessionContext.clear()

    # -------- Scheduler wrapper --------
    @staticmethod
    def run(fn: Callable[[], Tuple[Optional[Any], Optional[str]]]) -> Tuple[Optional[Any], Optional[str]]:
        # Create and set session for the entire task context - this ensures
        # all database operations in the task use the same session
        session = db.get_session()
        SessionContext.set(session)
        logger.debug("Created and set database session for scheduled task context")
        
        try:
            result, error = fn()
            
            if error is None:
                session.commit()
                logger.debug("Committed scheduled task transaction")
            else:
                session.rollback()
                logger.debug(f"Rolled back scheduled task transaction due to error: {error}")
            
            return result, error
        except Exception as e:
            try:
                session.rollback()
                logger.debug(f"Rolled back scheduled task transaction due to exception: {e}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback transaction: {rollback_error}")
            return None, str(e)
        finally:
            # Clean up the session
            try:
                session.close()
                logger.debug("Closed scheduled task database session")
            except Exception as close_error:
                logger.error(f"Failed to close session: {close_error}")
            SessionContext.clear()


