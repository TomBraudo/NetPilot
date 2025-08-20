"""
TwoFA DB operations using centralized session management.

All functions here must NOT commit/rollback/close the session.
They obtain the active session via managers.db_session_context.SessionContext.get().
Return values follow the (data, error) convention.
"""

from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import text, update, func, bindparam
from sqlalchemy.orm import Session

from managers.db_session_context import SessionContext
from services.db_operations.base import handle_db_errors
from utils.logging_config import get_logger
from models.user import User, User2FASettings, User2FAAttempt


logger = get_logger('db.twofa')


@handle_db_errors("2FA: start setup")
def start_setup(user_id: str, secret_encrypted: str, setup_token: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    session: Session = SessionContext.get()

    user: Optional[User] = session.query(User).filter_by(id=user_id).first()
    if not user:
        return None, "User not found"

    user_2fa: Optional[User2FASettings] = session.query(User2FASettings).filter_by(user_id=user_id).first()
    if not user_2fa:
        user_2fa = User2FASettings(
            user_id=user_id,
            totp_secret=secret_encrypted,
            setup_token=setup_token,
            setup_expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_enabled=False,
        )
        session.add(user_2fa)
    else:
        user_2fa.totp_secret = secret_encrypted
        user_2fa.setup_token = setup_token
        user_2fa.setup_expires_at = datetime.utcnow() + timedelta(minutes=10)
        user_2fa.is_enabled = False

    # No commit here; transaction manager will handle it
    return {
        "setup_token": setup_token,
        "expires_in": 600,
        "user_email": getattr(user, 'email', None),
    }, None


@handle_db_errors("2FA: validate and expire setup token")
def validate_and_expire_setup_token(user_id: str, setup_token: str) -> Tuple[Optional[User2FASettings], Optional[str]]:
    session: Session = SessionContext.get()

    # Atomic validation and expiration within current transaction
    user_2fa = session.query(User2FASettings).filter_by(
        user_id=user_id,
        setup_token=setup_token
    ).with_for_update().first()

    if not user_2fa:
        return None, None

    if user_2fa.setup_expires_at and user_2fa.setup_expires_at < datetime.utcnow():
        return None, None

    user_2fa.setup_token = None
    user_2fa.setup_expires_at = None
    user_2fa.updated_at = datetime.utcnow()

    return user_2fa, None


@handle_db_errors("2FA: enable 2FA and log attempt")
def enable_2fa_and_log_attempt(user_id: str, success: bool, ip_address: Optional[str], user_agent: Optional[str]) -> Tuple[bool, Optional[str]]:
    session: Session = SessionContext.get()
    user_2fa = session.query(User2FASettings).filter_by(user_id=user_id).first()
    if not user_2fa:
        return False, "2FA settings not found"

    user_2fa.is_enabled = True
    user_2fa.updated_at = datetime.utcnow()

    attempt = User2FAAttempt(
        user_id=user_id,
        attempt_type='totp',
        success=success,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(attempt)

    return True, None


@handle_db_errors("2FA: get settings and user")
def get_settings_and_user(user_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    session: Session = SessionContext.get()
    user: Optional[User] = session.query(User).filter_by(id=user_id).first()
    user_2fa: Optional[User2FASettings] = session.query(User2FASettings).filter_by(user_id=user_id).first()

    return {
        "user": user,
        "user_2fa": user_2fa,
    }, None


@handle_db_errors("2FA: log attempt only")
def log_attempt(user_id: str, success: bool, ip_address: Optional[str], user_agent: Optional[str]) -> Tuple[bool, Optional[str]]:
    session: Session = SessionContext.get()
    attempt = User2FAAttempt(
        user_id=user_id,
        attempt_type='totp',
        success=success,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(attempt)
    return True, None


@handle_db_errors("2FA: disable and clear requirements")
def disable_2fa(user_id: str) -> Tuple[bool, Optional[str]]:
    session: Session = SessionContext.get()
    user_2fa = session.query(User2FASettings).filter_by(user_id=user_id).first()
    if user_2fa:
        session.delete(user_2fa)

    user = session.query(User).filter_by(id=user_id).first()
    if user and not getattr(user, 'twofa_enforced_at', None):
        user.requires_2fa = False

    return True, None


@handle_db_errors("2FA: reset settings")
def reset_settings(user_id: str) -> Tuple[bool, Optional[str]]:
    session: Session = SessionContext.get()
    user_2fa = session.query(User2FASettings).filter_by(user_id=user_id).first()
    if user_2fa:
        session.delete(user_2fa)
    return True, None


@handle_db_errors("2FA: replace backup codes")
def replace_backup_codes(user_id: str, hashed_codes: List[str]) -> Tuple[bool, Optional[str]]:
    session: Session = SessionContext.get()
    user_2fa = session.query(User2FASettings).filter_by(user_id=user_id).first()
    if not user_2fa:
        return False, "2FA settings not found"
    user_2fa.backup_codes = hashed_codes
    user_2fa.updated_at = datetime.utcnow()
    return True, None


# ===== Additional atomic operations migrated from service =====

@handle_db_errors("2FA: increment failed attempts")
def increment_failed_attempts(user_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    session: Session = SessionContext.get()
    # Atomic increment using SQLAlchemy Core with RETURNING
    stmt = (
        update(User2FASettings)
        .where(User2FASettings.user_id == user_id)
        .values(
            failed_attempts=User2FASettings.failed_attempts + 1,
            updated_at=func.now(),
        )
        .returning(User2FASettings.failed_attempts)
    )
    row = session.execute(stmt).fetchone()
    if not row:
        return None, "User 2FA settings not found"
    failed_count = row[0]

    # Determine if should lock and set lock timestamp if needed
    should_lock = failed_count >= 3
    if should_lock:
        # Exponential backoff tiers as in service
        if failed_count == 3:
            delta = timedelta(minutes=5)
        elif failed_count == 4:
            delta = timedelta(minutes=15)
        elif failed_count == 5:
            delta = timedelta(hours=1)
        else:
            delta = timedelta(hours=24)
        lock_until = datetime.utcnow() + delta
        session.execute(
            update(User2FASettings)
            .where(User2FASettings.user_id == user_id)
            .values(locked_until=lock_until, updated_at=func.now())
        )

    return {"failed_attempts": failed_count, "should_lock": should_lock}, None


@handle_db_errors("2FA: reset failed attempts")
def reset_failed_attempts(user_id: str) -> Tuple[bool, Optional[str]]:
    session: Session = SessionContext.get()
    result = session.execute(
        update(User2FASettings)
        .where(User2FASettings.user_id == user_id)
        .values(
            failed_attempts=0,
            locked_until=None,
            last_used_at=func.now(),
            updated_at=func.now(),
        )
    )
    return (result.rowcount or 0) > 0, None


@handle_db_errors("2FA: use backup code")
def use_backup_code(user_id: str, backup_hash: str) -> Tuple[bool, Optional[str]]:
    session: Session = SessionContext.get()
    # Remove one matching backup code atomically using SQLAlchemy func
    stmt = (
        update(User2FASettings)
        .where(
            User2FASettings.user_id == user_id,
            bindparam("backup_hash") == func.any(User2FASettings.backup_codes),
        )
        .values(
            backup_codes=func.array_remove(User2FASettings.backup_codes, bindparam("backup_hash")),
            updated_at=func.now(),
        )
        .returning(func.array_length(User2FASettings.backup_codes, 1))
    )
    row = session.execute(stmt, {"backup_hash": backup_hash}).fetchone()
    if not row:
        return False, None
    return True, None


