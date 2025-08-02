import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from cryptography.fernet import Fernet
from models.user import User, User2FASettings, User2FAAttempt
from utils.logging_config import get_logger
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, text

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
        
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
            
        self.cipher = Fernet(encryption_key)
    
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
    
    def atomic_increment_failed_attempts(self, db_session: Session, user_id: str) -> Tuple[int, bool]:
        """
        Atomically increment failed attempts and determine if user should be locked.
        
        Returns:
            Tuple[int, bool]: (new_failed_attempts_count, should_lock)
        
        RACE CONDITION PROTECTION:
        - Uses database-level atomic increment
        - Single transaction to prevent race conditions between multiple verification attempts
        """
        try:
            # Use raw SQL for atomic increment to prevent race conditions
            result = db_session.execute(
                text("""
                UPDATE user_2fa_settings 
                SET failed_attempts = failed_attempts + 1,
                    updated_at = NOW()
                WHERE user_id = :user_id 
                RETURNING failed_attempts
                """),
                {"user_id": user_id}
            )
            
            new_attempts = result.fetchone()
            if new_attempts:
                failed_count = new_attempts[0]
                should_lock = self.should_lock_user(failed_count)
                
                # If should lock, update lockout timestamp atomically
                if should_lock:
                    lockout_duration = self.calculate_lockout_duration(failed_count)
                    lock_until = datetime.utcnow() + lockout_duration
                    
                    db_session.execute(
                        text("""
                        UPDATE user_2fa_settings 
                        SET locked_until = :lock_until,
                            updated_at = NOW()
                        WHERE user_id = :user_id
                        """),
                        {"user_id": user_id, "lock_until": lock_until}
                    )
                
                return failed_count, should_lock
            else:
                logger.error(f"Failed to increment attempts for user {user_id} - user not found")
                return 0, False
                
        except Exception as e:
            logger.error(f"Error in atomic_increment_failed_attempts for user {user_id}: {e}")
            raise
    
    def atomic_reset_failed_attempts(self, db_session: Session, user_id: str) -> bool:
        """
        Atomically reset failed attempts and unlock user.
        
        RACE CONDITION PROTECTION:
        - Single atomic update to prevent partial state
        """
        try:
            result = db_session.execute(
                text("""
                UPDATE user_2fa_settings 
                SET failed_attempts = 0,
                    locked_until = NULL,
                    last_used_at = NOW(),
                    updated_at = NOW()
                WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error in atomic_reset_failed_attempts for user {user_id}: {e}")
            raise
    
    def atomic_use_backup_code(self, db_session: Session, user_id: str, backup_hash: str) -> bool:
        """
        Atomically remove a backup code after successful verification.
        
        RACE CONDITION PROTECTION:
        - Uses array manipulation in single database operation
        - Prevents double-use of backup codes
        """
        try:
            # Use PostgreSQL array_remove function for atomic removal
            result = db_session.execute(
                text("""
                UPDATE user_2fa_settings 
                SET backup_codes = array_remove(backup_codes, :backup_hash),
                    updated_at = NOW()
                WHERE user_id = :user_id 
                AND :backup_hash = ANY(backup_codes)
                RETURNING array_length(backup_codes, 1) as remaining_codes
                """),
                {"user_id": user_id, "backup_hash": backup_hash}
            )
            
            result_row = result.fetchone()
            if result_row:
                remaining = result_row[0] or 0  # Handle None case
                logger.info(f"Backup code used for user {user_id}. Remaining codes: {remaining}")
                return True
            else:
                logger.warning(f"Backup code not found or already used for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error in atomic_use_backup_code for user {user_id}: {e}")
            raise
    
    def atomic_validate_and_expire_setup_token(self, db_session: Session, user_id: str, setup_token: str) -> Optional[User2FASettings]:
        """
        Atomically validate setup token and mark as expired.
        
        RACE CONDITION PROTECTION:
        - Single query to check and expire token
        - Prevents token reuse in concurrent requests
        """
        try:
            # Update and return in single operation
            result = db_session.execute(
                text("""
                UPDATE user_2fa_settings 
                SET setup_token = NULL,
                    setup_expires_at = NULL,
                    updated_at = NOW()
                WHERE user_id = :user_id 
                AND setup_token = :setup_token 
                AND setup_expires_at > NOW()
                RETURNING *
                """),
                {"user_id": user_id, "setup_token": setup_token}
            )
            
            row = result.fetchone()
            if row:
                # Convert row to User2FASettings object
                user_2fa = db_session.query(User2FASettings).filter_by(user_id=user_id).first()
                return user_2fa
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error in atomic_validate_and_expire_setup_token for user {user_id}: {e}")
            raise

# Initialize service
twofa_service = TwoFAService()