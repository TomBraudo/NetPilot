from flask import Blueprint, request, g, session, jsonify
from utils.response_helpers import build_success_response, build_error_response
from services.twofa_service import twofa_service
from models.user import User, User2FASettings, User2FAAttempt
from database.connection import db
from utils.logging_config import get_logger
from auth import login_required
import time
import secrets
from datetime import datetime, timedelta

twofa_bp = Blueprint('twofa', __name__)
logger = get_logger('twofa_endpoints')

@twofa_bp.route('/setup/start', methods=['POST'])
@login_required
def start_2fa_setup():
    """Initialize 2FA setup process"""
    start_time = time.time()
    user_id = g.user_id
    
    db_session = db.get_session()
    try:
        # Generate new secret and setup token
        secret = twofa_service.generate_totp_secret()
        setup_token = secrets.token_urlsafe(32)
        
        # Check if user already has 2FA settings
        user_2fa = db_session.query(User2FASettings).filter_by(user_id=user_id).first()
        user = db_session.query(User).filter_by(id=user_id).first()
        
        if not user:
            return build_error_response("User not found", 404, "USER_NOT_FOUND", start_time)
        
        if not user_2fa:
            user_2fa = User2FASettings(
                user_id=user_id,
                totp_secret=twofa_service.encrypt_secret(secret),
                setup_token=setup_token,
                setup_expires_at=datetime.utcnow() + timedelta(minutes=10)
            )
            db_session.add(user_2fa)
        else:
            # Update existing settings for re-setup
            user_2fa.totp_secret = twofa_service.encrypt_secret(secret)
            user_2fa.setup_token = setup_token
            user_2fa.setup_expires_at = datetime.utcnow() + timedelta(minutes=10)
            user_2fa.is_enabled = False  # Disable until setup is complete
        
        db_session.commit()
        
        # Generate QR code
        qr_code = twofa_service.generate_qr_code(user.email, secret)
        
        response_data = {
            "qr_code": qr_code,
            "secret": secret,  # For manual entry
            "setup_token": setup_token,
            "expires_in": 600  # 10 minutes
        }
        
        logger.info(f"2FA setup started for user {user_id}")
        return build_success_response(response_data, start_time)
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"2FA setup start failed for user {user_id}: {e}")
        return build_error_response("Failed to start 2FA setup", 500, "SETUP_FAILED", start_time)
    finally:
        db_session.close()

@twofa_bp.route('/setup/verify', methods=['POST'])
@login_required
def verify_2fa_setup():
    """Verify and complete 2FA setup - RACE CONDITION PROTECTED"""
    start_time = time.time()
    user_id = g.user_id
    
    data = request.get_json()
    code = data.get('code')
    setup_token = data.get('setup_token')
    
    if not code or not setup_token:
        return build_error_response("Code and setup token required", 400, "MISSING_DATA", start_time)
    
    db_session = db.get_session()
    try:
        # RACE CONDITION PROTECTION: Atomic token validation and expiration
        user_2fa = twofa_service.atomic_validate_and_expire_setup_token(
            db_session, user_id, setup_token
        )
        
        if not user_2fa:
            return build_error_response("Invalid or expired setup token", 400, "INVALID_TOKEN", start_time)
        
        # Verify the code
        secret = twofa_service.decrypt_secret(user_2fa.totp_secret)
        if not twofa_service.verify_totp_code(secret, code):
            return build_error_response("Invalid verification code", 400, "INVALID_CODE", start_time)
        
        # Generate backup codes
        backup_codes = twofa_service.generate_backup_codes()
        hashed_backup_codes = [twofa_service.hash_backup_code(code) for code in backup_codes]
        
        # Complete setup atomically
        user_2fa.is_enabled = True
        user_2fa.backup_codes = hashed_backup_codes
        user_2fa.failed_attempts = 0
        user_2fa.locked_until = None
        user_2fa.updated_at = datetime.utcnow()
        
        # Log successful setup attempt
        attempt = User2FAAttempt(
            user_id=user_id,
            attempt_type='totp',
            success=True,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db_session.add(attempt)
        
        db_session.commit()
        
        response_data = {
            "success": True,
            "backup_codes": backup_codes,  # Show these only once
            "message": "2FA setup completed successfully"
        }
        
        logger.info(f"2FA setup completed successfully for user {user_id}")
        return build_success_response(response_data, start_time)
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"2FA setup verification failed for user {user_id}: {e}")
        return build_error_response("Failed to verify 2FA setup", 500, "VERIFICATION_FAILED", start_time)
    finally:
        db_session.close()

@twofa_bp.route('/verify', methods=['POST'])
@login_required
def verify_2fa():
    """Verify 2FA code during login - RACE CONDITION PROTECTED"""
    start_time = time.time()
    user_id = g.user_id
    
    data = request.get_json()
    code = data.get('code')
    method = data.get('method', 'totp')  # 'totp', 'backup'
    
    if not code:
        return build_error_response("Verification code required", 400, "MISSING_CODE", start_time)
    
    db_session = db.get_session()
    try:
        user_2fa = db_session.query(User2FASettings).filter_by(user_id=user_id).first()
        
        if not user_2fa or not user_2fa.is_enabled:
            return build_error_response("2FA not enabled", 400, "2FA_NOT_ENABLED", start_time)
        
        # Check if user is locked
        if twofa_service.is_user_locked(user_2fa):
            return build_error_response("Account locked due to failed attempts", 403, "ACCOUNT_LOCKED", start_time)
        
        verification_success = False
        backup_hash_used = None
        
        if method == 'totp':
            secret = twofa_service.decrypt_secret(user_2fa.totp_secret)
            verification_success = twofa_service.verify_totp_code(secret, code)
        
        elif method == 'backup':
            # Check backup codes - find matching hash first
            if user_2fa.backup_codes:
                for stored_hash in user_2fa.backup_codes:
                    if twofa_service.verify_backup_code(stored_hash, code):
                        backup_hash_used = stored_hash
                        verification_success = True
                        break
        
        # Log attempt BEFORE modifying state
        attempt = User2FAAttempt(
            user_id=user_id,
            attempt_type=method,
            success=verification_success,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db_session.add(attempt)
        
        if verification_success:
            # RACE CONDITION PROTECTION: Atomic success handling
            if method == 'backup' and backup_hash_used:
                # Atomically remove used backup code
                backup_removed = twofa_service.atomic_use_backup_code(
                    db_session, user_id, backup_hash_used
                )
                if not backup_removed:
                    # Code was already used by concurrent request
                    return build_error_response("Backup code already used", 400, "CODE_ALREADY_USED", start_time)
            
            # Atomically reset failed attempts and unlock
            twofa_service.atomic_reset_failed_attempts(db_session, user_id)
            
            # Mark 2FA as verified in session
            session['2fa_verified'] = True
            session['2fa_verified_at'] = datetime.utcnow().isoformat()
            
            db_session.commit()
            
            logger.info(f"2FA verification successful for user {user_id} using {method}")
            return build_success_response({
                "success": True,
                "message": "2FA verification successful"
            }, start_time)
        
        else:
            # RACE CONDITION PROTECTION: Atomic failed attempt handling
            failed_count, should_lock = twofa_service.atomic_increment_failed_attempts(
                db_session, user_id
            )
            
            db_session.commit()
            
            attempts_remaining = max(0, 3 - failed_count)
            
            if should_lock:
                logger.warning(f"User {user_id} locked after {failed_count} failed 2FA attempts")
                return build_error_response(
                    "Account locked due to too many failed attempts",
                    403,
                    "ACCOUNT_LOCKED",
                    start_time
                )
            
            return build_error_response(
                f"Invalid code. {attempts_remaining} attempts remaining",
                400,
                "INVALID_CODE",
                start_time
            )
    
    except Exception as e:
        db_session.rollback()
        logger.error(f"2FA verification failed for user {user_id}: {e}")
        return build_error_response("Verification failed", 500, "VERIFICATION_ERROR", start_time)
    finally:
        db_session.close()

@twofa_bp.route('/status', methods=['GET'])
@login_required
def get_2fa_status():
    """Get user's 2FA status"""
    start_time = time.time()
    user_id = g.user_id
    
    db_session = db.get_session()
    try:
        user = db_session.query(User).filter_by(id=user_id).first()
        user_2fa = db_session.query(User2FASettings).filter_by(user_id=user_id).first()
        
        status = {
            "is_enabled": user_2fa.is_enabled if user_2fa else False,
            "is_required": user.requires_2fa if user else False,
            "is_verified": session.get('2fa_verified', False),
            "methods_available": [],
            "backup_codes_remaining": len(user_2fa.backup_codes) if user_2fa and user_2fa.backup_codes else 0,
            "is_locked": twofa_service.is_user_locked(user_2fa) if user_2fa else False
        }
        
        if user_2fa and user_2fa.is_enabled:
            status["methods_available"].append("totp")
            if user_2fa.backup_codes:
                status["methods_available"].append("backup")
        
        return build_success_response(status, start_time)
        
    except Exception as e:
        logger.error(f"Failed to get 2FA status for user {user_id}: {e}")
        return build_error_response("Failed to get 2FA status", 500, "STATUS_ERROR", start_time)
    finally:
        db_session.close()

@twofa_bp.route('/disable', methods=['POST'])
@login_required
def disable_2fa():
    """Disable 2FA for user (requires 2FA code confirmation)"""
    start_time = time.time()
    user_id = g.user_id
    
    data = request.get_json()
    confirmation_code = data.get('code')  # Require 2FA code to disable
    
    if not confirmation_code:
        return build_error_response("2FA code required to disable", 400, "MISSING_CODE", start_time)
    
    db_session = db.get_session()
    try:
        user_2fa = db_session.query(User2FASettings).filter_by(user_id=user_id).first()
        
        if not user_2fa or not user_2fa.is_enabled:
            return build_error_response("2FA not enabled", 400, "2FA_NOT_ENABLED", start_time)
        
        # Check if user is locked
        if twofa_service.is_user_locked(user_2fa):
            return build_error_response("Account locked - cannot disable 2FA", 403, "ACCOUNT_LOCKED", start_time)
        
        # Verify current 2FA code before disabling
        secret = twofa_service.decrypt_secret(user_2fa.totp_secret)
        if not twofa_service.verify_totp_code(secret, confirmation_code):
            # Increment failed attempts even for disable attempts
            twofa_service.atomic_increment_failed_attempts(db_session, user_id)
            db_session.commit()
            return build_error_response("Invalid 2FA code", 400, "INVALID_CODE", start_time)
        
        # Disable 2FA
        db_session.delete(user_2fa)
        
        # Update user requirements if not enforced by admin
        user = db_session.query(User).filter_by(id=user_id).first()
        if not user.twofa_enforced_at:  # Only if not enforced by admin
            user.requires_2fa = False
        
        db_session.commit()
        
        # Clear session verification
        session.pop('2fa_verified', None)
        session.pop('2fa_verified_at', None)
        
        logger.info(f"2FA disabled for user {user_id}")
        return build_success_response({
            "success": True,
            "message": "2FA disabled successfully"
        }, start_time)
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to disable 2FA for user {user_id}: {e}")
        return build_error_response("Failed to disable 2FA", 500, "DISABLE_ERROR", start_time)
    finally:
        db_session.close()

@twofa_bp.route('/generate-backup-codes', methods=['POST'])
@login_required
def generate_new_backup_codes():
    """Generate new backup codes (requires 2FA verification)"""
    start_time = time.time()
    user_id = g.user_id
    
    data = request.get_json()
    confirmation_code = data.get('code')
    
    if not confirmation_code:
        return build_error_response("2FA code required", 400, "MISSING_CODE", start_time)
    
    db_session = db.get_session()
    try:
        user_2fa = db_session.query(User2FASettings).filter_by(user_id=user_id).first()
        
        if not user_2fa or not user_2fa.is_enabled:
            return build_error_response("2FA not enabled", 400, "2FA_NOT_ENABLED", start_time)
        
        # Verify current 2FA code
        secret = twofa_service.decrypt_secret(user_2fa.totp_secret)
        if not twofa_service.verify_totp_code(secret, confirmation_code):
            return build_error_response("Invalid 2FA code", 400, "INVALID_CODE", start_time)
        
        # Generate new backup codes
        backup_codes = twofa_service.generate_backup_codes()
        hashed_backup_codes = [twofa_service.hash_backup_code(code) for code in backup_codes]
        
        # Replace old backup codes
        user_2fa.backup_codes = hashed_backup_codes
        user_2fa.updated_at = datetime.utcnow()
        
        db_session.commit()
        
        logger.info(f"New backup codes generated for user {user_id}")
        return build_success_response({
            "backup_codes": backup_codes,
            "message": "New backup codes generated successfully"
        }, start_time)
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to generate backup codes for user {user_id}: {e}")
        return build_error_response("Failed to generate backup codes", 500, "GENERATION_ERROR", start_time)
    finally:
        db_session.close()