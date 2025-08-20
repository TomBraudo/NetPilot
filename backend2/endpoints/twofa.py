from flask import Blueprint, request, g, session, jsonify
from utils.response_helpers import build_success_response, build_error_response
from services.twofa_service import (
    twofa_service,
    start_2fa_setup,
    verify_2fa_setup as svc_verify_2fa_setup,
    verify_2fa_login as svc_verify_2fa_login,
    get_2fa_status_service,
    disable_2fa_service,
    reset_2fa_service,
    generate_backup_codes_service,
)
from utils.logging_config import get_logger
from auth import login_required
import time
import secrets
from datetime import datetime, timedelta
from managers.transaction_manager import TransactionManager

twofa_bp = Blueprint('twofa', __name__)
logger = get_logger('twofa_endpoints')

@twofa_bp.route('/setup/start', methods=['POST'])
@login_required
def start_2fa_setup():
    """Initialize 2FA setup process"""
    start_time = time.time()
    user_id = g.user_id
    
    # Generate new secret and setup token
    result, error = TransactionManager.run(lambda: start_2fa_setup(user_id))
    if error:
        logger.error(f"2FA setup start failed for user {user_id}: {error}")
        return build_error_response("Failed to start 2FA setup. Please try again.", 500, "SETUP_FAILED", start_time)

    logger.info(f"2FA setup started for user {user_id}")
    return build_success_response(result, start_time)

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
        return build_error_response("Please enter the 6-digit code from your authenticator app", 400, "MISSING_DATA", start_time)
    
    result, error = TransactionManager.run(lambda: svc_verify_2fa_setup(user_id, code, setup_token, request.remote_addr, request.headers.get('User-Agent')))
    if error:
        if error == "SETUP_EXPIRED":
            return build_error_response("Setup session expired. Please start the setup process again.", 400, "SETUP_EXPIRED", start_time)
        if error == "WRONG_PIN":
            return build_error_response("Wrong PIN, try again", 400, "WRONG_PIN", start_time)
        logger.error(f"2FA setup verification failed for user {user_id}: {error}")
        return build_error_response("Failed to verify 2FA setup. Please try again.", 500, "VERIFICATION_FAILED", start_time)

    logger.info(f"2FA setup completed successfully for user {user_id}")
    return build_success_response(result, start_time)

@twofa_bp.route('/verify', methods=['POST'])
@login_required
def verify_2fa():
    """Verify 2FA code during login - RACE CONDITION PROTECTED"""
    start_time = time.time()
    user_id = g.user_id
    
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return build_error_response("Please enter your 6-digit authenticator code", 400, "MISSING_CODE", start_time)
    
    result, error = TransactionManager.run(lambda: svc_verify_2fa_login(user_id, code, request.remote_addr, request.headers.get('User-Agent')))
    if error:
        if error == "2FA_NOT_ENABLED":
            return build_error_response("Two-factor authentication is not set up for your account", 400, "2FA_NOT_ENABLED", start_time)
        if error == "WRONG_PIN":
            return build_error_response("Wrong PIN, try again", 400, "WRONG_PIN", start_time)
        logger.error(f"2FA verification failed for user {user_id}: {error}")
        return build_error_response("Verification failed", 500, "VERIFICATION_ERROR", start_time)

    logger.info(f"2FA verification successful for user {user_id} using TOTP")
    return build_success_response(result, start_time)

@twofa_bp.route('/status', methods=['GET'])
@login_required
def get_2fa_status():
    """Get user's 2FA status"""
    start_time = time.time()
    user_id = g.user_id
    
    svc_result, error = TransactionManager.run(lambda: get_2fa_status_service(user_id))
    if error:
        logger.error(f"Failed to get 2FA status for user {user_id}: {error}")
        return build_error_response("Failed to get 2FA status", 500, "STATUS_ERROR", start_time)
    status = svc_result[0] if isinstance(svc_result, tuple) else svc_result
    status["is_verified"] = session.get('2fa_verified', False)
    return build_success_response(status, start_time)

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
    
    result, error = TransactionManager.run(lambda: disable_2fa_service(user_id, confirmation_code))
    if error:
        if error == "2FA_NOT_ENABLED":
            return build_error_response("2FA not enabled", 400, "2FA_NOT_ENABLED", start_time)
        if error == "WRONG_PIN":
            return build_error_response("Wrong PIN, try again", 400, "WRONG_PIN", start_time)
        logger.error(f"Failed to disable 2FA for user {user_id}: {error}")
        return build_error_response("Failed to disable 2FA", 500, "DISABLE_ERROR", start_time)

    logger.info(f"2FA disabled for user {user_id}")
    session.pop('2fa_verified', None)
    session.pop('2fa_verified_at', None)
    return build_success_response(result, start_time)

@twofa_bp.route('/reset', methods=['POST'])
@login_required
def reset_2fa():
    """Reset 2FA settings and start fresh setup"""
    start_time = time.time()
    user_id = g.user_id
    
    result, error = TransactionManager.run(lambda: reset_2fa_service(user_id))
    if error:
        logger.error(f"Failed to reset 2FA for user {user_id}: {error}")
        return build_error_response("Failed to reset 2FA", 500, "RESET_ERROR", start_time)

    logger.info(f"2FA reset for user {user_id}")
    session.pop('2fa_verified', None)
    session.pop('2fa_verified_at', None)
    return build_success_response(result, start_time)

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
    
    result, error = TransactionManager.run(lambda: generate_backup_codes_service(user_id, confirmation_code))
    if error:
        if error == "2FA_NOT_ENABLED":
            return build_error_response("2FA not enabled", 400, "2FA_NOT_ENABLED", start_time)
        if error == "INVALID_CODE":
            return build_error_response("Invalid 2FA code", 400, "INVALID_CODE", start_time)
        logger.error(f"Failed to generate backup codes for user {user_id}: {error}")
        return build_error_response("Failed to generate backup codes", 500, "GENERATION_ERROR", start_time)

    logger.info(f"New backup codes generated for user {user_id}")
    return build_success_response(result, start_time)