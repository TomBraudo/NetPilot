import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from cryptography.fernet import Fernet
from models.user import User2FASettings
from utils.logging_config import get_logger
from .base import handle_service_errors, log_service_operation
from services.db_operations.twofa_db import (
    start_setup as db_start_setup,
    validate_and_expire_setup_token as db_validate_and_expire_setup_token,
    enable_2fa_and_log_attempt as db_enable_2fa_and_log_attempt,
    get_settings_and_user as db_get_settings_and_user,
    log_attempt as db_log_attempt,
    disable_2fa as db_disable_2fa,
    reset_settings as db_reset_settings,
    replace_backup_codes as db_replace_backup_codes,
    increment_failed_attempts as db_increment_failed_attempts,
    reset_failed_attempts as db_reset_failed_attempts,
    use_backup_code as db_use_backup_code,
)

logger = get_logger('2fa_service')

class TwoFAService:
    def __init__(self):
        # Initialize encryption key for TOTP secrets
        encryption_key = os.getenv('TOTP_ENCRYPTION_KEY')
        if not encryption_key:
            # Generate key if not provided (store this securely!)
            encryption_key = Fernet.generate_key().decode()
            logger.warning(f"Generated new TOTP encryption key: {encryption_key}")
            logger.warning("Store this key securely in your environment variables!")
            logger.warning("Add TOTP_ENCRYPTION_KEY to your .env file to persist this key!")
        else:
            logger.info("TOTP encryption key loaded from environment variables")
        
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
            
        try:
            self.cipher = Fernet(encryption_key)
            logger.info("TOTP encryption cipher initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TOTP encryption cipher: {e}")
            raise
    
    def encrypt_secret(self, secret: str) -> str:
        """Encrypt TOTP secret for database storage"""
        return self.cipher.encrypt(secret.encode()).decode()
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt TOTP secret from database"""
        return self.cipher.decrypt(encrypted_secret.encode()).decode()
    
    def generate_totp_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="NetPilot"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        # Convert to base64 image
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_totp_code(self, secret: str, code: str, window: int = 1) -> bool:
        """Verify TOTP code with tolerance window"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    
    def generate_backup_codes(self, count: int = 8) -> List[str]:
        """Generate backup codes for 2FA recovery"""
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = secrets.token_hex(4).upper()
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """Hash backup code for secure storage"""
        # Normalize code before hashing (remove dashes, uppercase)
        clean_code = code.replace('-', '').upper()
        return hashlib.sha256(clean_code.encode()).hexdigest()
    
    def verify_backup_code(self, stored_hash: str, provided_code: str) -> bool:
        """Verify backup code against stored hash"""
        # Clean the provided code (remove dashes, make uppercase)
        clean_code = provided_code.replace('-', '').upper()
        return hashlib.sha256(clean_code.encode()).hexdigest() == stored_hash
    
    def is_user_locked(self, user_2fa: User2FASettings) -> bool:
        """Check if user is locked due to failed attempts"""
        if not user_2fa.locked_until:
            return False
        return datetime.utcnow() < user_2fa.locked_until
    
    def should_lock_user(self, failed_attempts: int) -> bool:
        """Determine if user should be locked based on failed attempts"""
        return failed_attempts >= 3  # Lock after 3 failed attempts
    
    def calculate_lockout_duration(self, failed_attempts: int) -> timedelta:
        """Calculate lockout duration based on failed attempts"""
        # Exponential backoff: 5 min, 15 min, 1 hour, 24 hours
        durations = [
            timedelta(minutes=5),
            timedelta(minutes=15),
            timedelta(hours=1),
            timedelta(hours=24)
        ]
        index = min(failed_attempts - 3, len(durations) - 1)
        return durations[index]
    
    # ===== RACE CONDITION PROTECTED METHODS =====
    
    def atomic_increment_failed_attempts(self, user_id: str) -> Tuple[int, bool]:
        """
        Atomically increment failed attempts and determine if user should be locked.
        
        Returns:
            Tuple[int, bool]: (new_failed_attempts_count, should_lock)
        
        RACE CONDITION PROTECTION:
        - Uses database-level atomic increment
        - Single transaction to prevent race conditions between multiple verification attempts
        """
        try:
            data, err = db_increment_failed_attempts(user_id)
            if err or not data:
                logger.error(f"Failed to increment attempts for user {user_id}: {err}")
                return 0, False
            return int(data.get('failed_attempts', 0)), bool(data.get('should_lock', False))
        except Exception as e:
            logger.error(f"Error in atomic_increment_failed_attempts for user {user_id}: {e}")
            raise
    
    def atomic_reset_failed_attempts(self, user_id: str) -> bool:
        """
        Atomically reset failed attempts and unlock user.
        
        RACE CONDITION PROTECTION:
        - Single atomic update to prevent partial state
        """
        try:
            ok, err = db_reset_failed_attempts(user_id)
            if err:
                logger.error(f"Failed to reset attempts for user {user_id}: {err}")
            return bool(ok)
        except Exception as e:
            logger.error(f"Error in atomic_reset_failed_attempts for user {user_id}: {e}")
            raise
    
    def atomic_use_backup_code(self, user_id: str, backup_hash: str) -> bool:
        """
        Atomically remove a backup code after successful verification.
        
        RACE CONDITION PROTECTION:
        - Uses array manipulation in single database operation
        - Prevents double-use of backup codes
        """
        try:
            ok, err = db_use_backup_code(user_id, backup_hash)
            if not ok:
                logger.warning(f"Backup code not found or already used for user {user_id}")
            if err:
                logger.error(f"Error in atomic_use_backup_code for user {user_id}: {err}")
            return bool(ok)
        except Exception as e:
            logger.error(f"Error in atomic_use_backup_code for user {user_id}: {e}")
            raise
    
    def atomic_validate_and_expire_setup_token(self, user_id: str, setup_token: str) -> Optional[User2FASettings]:
        """
        Atomically validate setup token and mark as expired.
        
        RACE CONDITION PROTECTION:
        - Single query to check and expire token
        - Prevents token reuse in concurrent requests
        """
        try:
            user_2fa, err = db_validate_and_expire_setup_token(user_id, setup_token)
            if err:
                logger.error(f"Failed to validate/expire setup token for user {user_id}: {err}")
                return None
            return user_2fa
        except Exception as e:
            logger.error(f"Error in atomic_validate_and_expire_setup_token for user {user_id}: {e}")
            raise

# Initialize service
twofa_service = TwoFAService()


# ===== Orchestration functions (service layer) =====

@handle_service_errors("2FA: start setup")
def start_2fa_setup(user_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Generate secret and setup token, persist via DB ops, and return QR + metadata."""
    secret = twofa_service.generate_totp_secret()
    setup_token = secrets.token_urlsafe(32)
    db_result, db_error = db_start_setup(user_id, twofa_service.encrypt_secret(secret), setup_token)
    if db_error:
        return None, db_error
    user_email = (db_result or {}).get('user_email')
    qr_code = twofa_service.generate_qr_code(user_email, secret)
    return {
        "qr_code": qr_code,
        "secret": secret,
        "setup_token": setup_token,
        "expires_in": 600,
    }, None


@handle_service_errors("2FA: verify setup")
def verify_2fa_setup(user_id: str, code: str, setup_token: str, ip_address: Optional[str], user_agent: Optional[str]) -> Tuple[Optional[Dict], Optional[str]]:
    user_2fa, err = db_validate_and_expire_setup_token(user_id, setup_token)
    if err:
        return None, err
    if not user_2fa:
        return None, "SETUP_EXPIRED"
    secret_val = twofa_service.decrypt_secret(user_2fa.totp_secret)
    if not twofa_service.verify_totp_code(secret_val, code):
        return None, "WRONG_PIN"
    ok, err2 = db_enable_2fa_and_log_attempt(user_id, True, ip_address, user_agent)
    if err2 or not ok:
        return None, err2 or "ENABLE_FAILED"
    return {"success": True, "message": "2FA setup completed successfully"}, None


@handle_service_errors("2FA: verify login")
def verify_2fa_login(user_id: str, code: str, ip_address: Optional[str], user_agent: Optional[str]) -> Tuple[Optional[Dict], Optional[str]]:
    data, err = db_get_settings_and_user(user_id)
    if err:
        return None, err
    user_2fa = (data or {}).get('user_2fa')
    if not user_2fa or not user_2fa.is_enabled:
        return None, "2FA_NOT_ENABLED"
    secret_val = twofa_service.decrypt_secret(user_2fa.totp_secret)
    verification_success = twofa_service.verify_totp_code(secret_val, code)
    ok, err2 = db_log_attempt(user_id, verification_success, ip_address, user_agent)
    if err2 or not ok:
        return None, err2 or "LOG_ATTEMPT_FAILED"
    if not verification_success:
        return None, "WRONG_PIN"
    
    # Return session data that the endpoint should set
    return {
        "success": True, 
        "message": "2FA verification successful",
        "session_data": {
            "2fa_verified": True,
            "2fa_verified_at": datetime.utcnow().isoformat()
        }
    }, None


@handle_service_errors("2FA: status")
def get_2fa_status_service(user_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    data, err = db_get_settings_and_user(user_id)
    if err:
        return None, err
    user = (data or {}).get('user')
    user_2fa = (data or {}).get('user_2fa')
    status = {
        "is_enabled": bool(user_2fa.is_enabled) if user_2fa else False,
        "is_required": bool(getattr(user, 'requires_2fa', False)) if user else False,
        "methods_available": ["totp"] if user_2fa and user_2fa.is_enabled else []
    }
    return status, None


@handle_service_errors("2FA: disable")
def disable_2fa_service(user_id: str, confirmation_code: str) -> Tuple[Optional[Dict], Optional[str]]:
    data, err = db_get_settings_and_user(user_id)
    if err:
        return None, err
    user_2fa = (data or {}).get('user_2fa')
    if not user_2fa or not user_2fa.is_enabled:
        return None, "2FA_NOT_ENABLED"
    secret_val = twofa_service.decrypt_secret(user_2fa.totp_secret)
    if not twofa_service.verify_totp_code(secret_val, confirmation_code):
        return None, "WRONG_PIN"
    ok, err2 = db_disable_2fa(user_id)
    if err2 or not ok:
        return None, err2 or "DISABLE_FAILED"
    return {
        "success": True, 
        "message": "2FA disabled successfully",
        "session_data": {
            "2fa_verified": None,
            "2fa_verified_at": None
        }
    }, None


@handle_service_errors("2FA: reset")
def reset_2fa_service(user_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    ok, err = db_reset_settings(user_id)
    if err or not ok:
        return None, err or "RESET_FAILED"
    return {
        "success": True, 
        "message": "2FA reset successfully. You can now set up 2FA again.",
        "session_data": {
            "2fa_verified": None,
            "2fa_verified_at": None
        }
    }, None


@handle_service_errors("2FA: generate backup codes")
def generate_backup_codes_service(user_id: str, confirmation_code: str) -> Tuple[Optional[Dict], Optional[str]]:
    data, err = db_get_settings_and_user(user_id)
    if err:
        return None, err
    user_2fa = (data or {}).get('user_2fa')
    if not user_2fa or not user_2fa.is_enabled:
        return None, "2FA_NOT_ENABLED"
    secret_val = twofa_service.decrypt_secret(user_2fa.totp_secret)
    if not twofa_service.verify_totp_code(secret_val, confirmation_code):
        return None, "INVALID_CODE"
    backup_codes = twofa_service.generate_backup_codes()
    hashed_backup_codes = [twofa_service.hash_backup_code(code) for code in backup_codes]
    ok, err2 = db_replace_backup_codes(user_id, hashed_backup_codes)
    if err2 or not ok:
        return None, err2 or "REPLACE_FAILED"
    return {"backup_codes": backup_codes, "message": "New backup codes generated successfully"}, None
    