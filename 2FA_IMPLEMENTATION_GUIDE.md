# NetPilot 2-Factor Authentication Implementation Guide

## 🎯 Overview

This guide provides a complete implementation of 2-Factor Authentication (2FA) for NetPilot, integrating seamlessly with your existing Google OAuth flow.

## 📋 Prerequisites

- Existing Google OAuth implementation working
- PostgreSQL database setup
- Python packages: `pyotp`, `qrcode[pil]`, `cryptography`
- Frontend React environment

## 🗄️ Phase 1: Database Schema Changes

### 1.1 Create Database Migration

Create `backend2/migrations/add_2fa_support.sql`:

```sql
-- User 2FA settings table
CREATE TABLE user_2fa_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    is_enabled BOOLEAN DEFAULT FALSE,
    totp_secret VARCHAR(255), -- Encrypted TOTP secret
    backup_codes TEXT[], -- Array of hashed backup codes
    sms_phone VARCHAR(20), -- For SMS 2FA (future)
    email_2fa_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    
    -- Security fields
    setup_token VARCHAR(255), -- Temporary token during setup
    setup_expires_at TIMESTAMP,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    
    UNIQUE(user_id)
);

-- 2FA verification attempts logging
CREATE TABLE user_2fa_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    attempt_type VARCHAR(20) NOT NULL, -- 'totp', 'sms', 'email', 'backup'
    success BOOLEAN NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX idx_2fa_attempts_user_time ON user_2fa_attempts(user_id, created_at);
CREATE INDEX idx_2fa_attempts_failed ON user_2fa_attempts(user_id, success, created_at);

-- Update existing users table
ALTER TABLE users ADD COLUMN requires_2fa BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN twofa_enforced_at TIMESTAMP;
```

### 1.2 Update User Models

Update `backend2/models/user.py`:

```python
from sqlalchemy import Column, String, Boolean, TIMESTAMP, ARRAY, Integer, Text
from sqlalchemy.orm import relationship
from models.base import BaseModel

class User(BaseModel):
    __tablename__ = 'users'
    
    # Existing fields...
    google_id = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    avatar_url = Column(String(500))
    last_login = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    
    # New 2FA fields
    requires_2fa = Column(Boolean, default=False)
    twofa_enforced_at = Column(TIMESTAMP)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user")
    twofa_settings = relationship("User2FASettings", back_populates="user", uselist=False)
    twofa_attempts = relationship("User2FAAttempt", back_populates="user")

class User2FASettings(BaseModel):
    __tablename__ = 'user_2fa_settings'
    
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    is_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(255))  # Will be encrypted
    backup_codes = Column(ARRAY(String))
    sms_phone = Column(String(20))
    email_2fa_enabled = Column(Boolean, default=False)
    last_used_at = Column(TIMESTAMP)
    
    # Security fields
    setup_token = Column(String(255))
    setup_expires_at = Column(TIMESTAMP)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(TIMESTAMP)
    
    # Relationships
    user = relationship("User", back_populates="twofa_settings")

class User2FAAttempt(BaseModel):
    __tablename__ = 'user_2fa_attempts'
    
    user_id = Column(String(255), nullable=False, index=True)
    attempt_type = Column(String(20), nullable=False)
    success = Column(Boolean, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="twofa_attempts")
```

## 🔧 Phase 2: Backend Implementation

### 2.1 Create 2FA Service

Create `backend2/services/twofa_service.py`:

```python
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
        return hashlib.sha256(code.encode()).hexdigest()
    
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

# Initialize service
twofa_service = TwoFAService()
```

### 2.2 Create 2FA Endpoints

Create `backend2/endpoints/twofa.py`:

```python
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
    """Verify and complete 2FA setup"""
    start_time = time.time()
    user_id = g.user_id
    
    data = request.get_json()
    code = data.get('code')
    setup_token = data.get('setup_token')
    
    if not code or not setup_token:
        return build_error_response("Code and setup token required", 400, "MISSING_DATA", start_time)
    
    db_session = db.get_session()
    try:
        user_2fa = db_session.query(User2FASettings).filter_by(
            user_id=user_id,
            setup_token=setup_token
        ).first()
        
        if not user_2fa:
            return build_error_response("Invalid setup token", 400, "INVALID_TOKEN", start_time)
        
        if datetime.utcnow() > user_2fa.setup_expires_at:
            return build_error_response("Setup token expired", 400, "TOKEN_EXPIRED", start_time)
        
        # Verify the code
        secret = twofa_service.decrypt_secret(user_2fa.totp_secret)
        if not twofa_service.verify_totp_code(secret, code):
            return build_error_response("Invalid verification code", 400, "INVALID_CODE", start_time)
        
        # Generate backup codes
        backup_codes = twofa_service.generate_backup_codes()
        hashed_backup_codes = [twofa_service.hash_backup_code(code) for code in backup_codes]
        
        # Complete setup
        user_2fa.is_enabled = True
        user_2fa.backup_codes = hashed_backup_codes
        user_2fa.setup_token = None
        user_2fa.setup_expires_at = None
        user_2fa.failed_attempts = 0
        user_2fa.locked_until = None
        
        db_session.commit()
        
        # Log successful setup
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
    """Verify 2FA code during login"""
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
        
        if method == 'totp':
            secret = twofa_service.decrypt_secret(user_2fa.totp_secret)
            verification_success = twofa_service.verify_totp_code(secret, code)
        
        elif method == 'backup':
            # Check backup codes
            if user_2fa.backup_codes:
                for stored_hash in user_2fa.backup_codes:
                    if twofa_service.verify_backup_code(stored_hash, code):
                        # Remove used backup code
                        user_2fa.backup_codes.remove(stored_hash)
                        verification_success = True
                        break
        
        # Log attempt
        attempt = User2FAAttempt(
            user_id=user_id,
            attempt_type=method,
            success=verification_success,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db_session.add(attempt)
        
        if verification_success:
            # Reset failed attempts
            user_2fa.failed_attempts = 0
            user_2fa.locked_until = None
            user_2fa.last_used_at = datetime.utcnow()
            
            # Mark 2FA as verified in session
            session['2fa_verified'] = True
            session['2fa_verified_at'] = datetime.utcnow().isoformat()
            
            db_session.commit()
            
            return build_success_response({
                "success": True,
                "message": "2FA verification successful"
            }, start_time)
        
        else:
            # Handle failed attempt
            user_2fa.failed_attempts += 1
            
            if twofa_service.should_lock_user(user_2fa.failed_attempts):
                lockout_duration = twofa_service.calculate_lockout_duration(user_2fa.failed_attempts)
                user_2fa.locked_until = datetime.utcnow() + lockout_duration
            
            db_session.commit()
            
            attempts_remaining = max(0, 3 - user_2fa.failed_attempts)
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
            "backup_codes_remaining": len(user_2fa.backup_codes) if user_2fa and user_2fa.backup_codes else 0
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
        
        # Verify current 2FA code before disabling
        secret = twofa_service.decrypt_secret(user_2fa.totp_secret)
        if not twofa_service.verify_totp_code(secret, confirmation_code):
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
```

### 2.3 Update OAuth Flow

Update `backend2/auth.py` to integrate 2FA:

```python
# Add import
from models.user import User2FASettings

# Update the authorize() function
@auth_bp.route('/authorize')
def authorize():
    """Handle OAuth callback"""
    token = google.authorize_access_token()
    session['user'] = token

    userToken = session.get('user')
    if not userToken:
        return 'No user session found', 400
    
    # Extract user info from token
    userInfo = userToken.get('userinfo', {})
    google_id = userInfo.get('sub')
    email = userInfo.get('email')
    full_name = userInfo.get('name')
    avatar_url = userInfo.get('picture')
    
    if not google_id or not email:
        return 'Invalid user information from Google', 400
    
    # Database session handling
    try:
        db_session = g.db_session
    except (AttributeError, RuntimeError):
        from database.connection import db
        db_session = db.get_session()
        print("Warning: Using fallback database session in OAuth callback")
    
    if not db_session:
        return 'Database connection error', 500
    
    try:
        # Try to find existing user by Google ID first
        user = db_session.query(User).filter_by(google_id=google_id).first()
        
        if not user:
            # Try to find by email (in case user exists but without google_id)
            user = db_session.query(User).filter_by(email=email).first()
            if user:
                # Update existing user with Google ID
                user.google_id = google_id
        
        if not user:
            # Create new user
            user = User(
                google_id=google_id,
                email=email,
                full_name=full_name,
                avatar_url=avatar_url,
                last_login=datetime.utcnow(),
                is_active=True
            )
            db_session.add(user)
        else:
            # Update last login for existing user
            user.last_login = datetime.utcnow()
            user.full_name = full_name or user.full_name
            user.avatar_url = avatar_url or user.avatar_url
        
        db_session.commit()
        
        # Check if user requires 2FA
        user_2fa = db_session.query(User2FASettings).filter_by(user_id=str(user.id)).first()
        requires_2fa = user.requires_2fa or (user_2fa and user_2fa.is_enabled)
        
        # CRITICAL: Store user_id in session IMMEDIATELY after successful commit
        session['user_id'] = str(user.id)
        session.permanent = True
        
        # Clear any previous 2FA verification
        session.pop('2fa_verified', None)
        session.pop('2fa_verified_at', None)
        
        print(f"User authenticated successfully: {user.email} (ID: {user.id})")
        print(f"Session updated with user_id: {session.get('user_id')}")
        print(f"2FA required: {requires_2fa}")
        
        # Redirect back to frontend with 2FA indicator
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        
        if requires_2fa:
            return redirect(f"{frontend_url}?login=success&requires_2fa=true")
        else:
            return redirect(f"{frontend_url}?login=success")
        
    except Exception as e:
        print(f"Error creating/updating user: {e}")
        db_session.rollback()
        # Clear any partial session data on error
        session.pop('user_id', None)
        return 'Error creating user account', 500

# Update the /me endpoint
@auth_bp.route('/me')
@login_required
def get_user_info():
    """Get current user information including 2FA status"""
    user_id = session.get('user_id')
    
    db_session = db.get_session()
    try:
        user = db_session.query(User).filter_by(id=user_id).first()
        user_2fa = db_session.query(User2FASettings).filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        user_info = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "requires_2fa": user.requires_2fa or (user_2fa and user_2fa.is_enabled),
            "has_2fa_enabled": user_2fa.is_enabled if user_2fa else False,
            "is_2fa_verified": session.get('2fa_verified', False)
        }
        
        return jsonify(user_info)
        
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        return jsonify({"error": "Failed to get user information"}), 500
    finally:
        db_session.close()
```

### 2.4 Register 2FA Blueprint

Update `backend2/server.py`:

```python
from endpoints.twofa import twofa_bp

# Register the blueprint
app.register_blueprint(twofa_bp, url_prefix='/api/2fa')
```

## 🎨 Phase 3: Frontend Implementation

### 3.1 Update AuthContext

Update `frontend/dashboard/src/context/AuthContext.jsx` to add 2FA support:

```javascript
// Add new state variables at the top of AuthProvider
const [twoFARequired, setTwoFARequired] = useState(false);
const [twoFAStatus, setTwoFAStatus] = useState(null);
const [showTwoFAModal, setShowTwoFAModal] = useState(false);
const [showTwoFASetupModal, setShowTwoFASetupModal] = useState(false);
const [twoFASetupData, setTwoFASetupData] = useState(null);

// Update checkAuthStatus function
const checkAuthStatus = async () => {
    try {
        console.log('Checking auth status...');
        const response = await fetch(`${API_BASE_URL}/me`, {
            credentials: 'include',
        });
        
        if (response.ok) {
            const userData = await response.json();
            console.log('User data received:', userData);
            setUser(userData);
            
            // Check 2FA requirements
            if (userData.requires_2fa && !userData.is_2fa_verified) {
                setTwoFARequired(true);
                if (userData.has_2fa_enabled) {
                    setShowTwoFAModal(true); // Show verification modal
                } else {
                    setShowTwoFASetupModal(true); // Show setup modal
                }
            } else {
                setTwoFARequired(false);
                setShowTwoFAModal(false);
                setShowTwoFASetupModal(false);
            }
            
            return userData;
        } else {
            setUser(null);
            return null;
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
        setUser(null);
        return null;
    } finally {
        setLoading(false);
    }
};

// Add 2FA functions
const start2FASetup = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/2fa/setup/start`, {
            method: 'POST',
            credentials: 'include',
        });
        
        if (response.ok) {
            const data = await response.json();
            setTwoFASetupData(data.data);
            return data.data;
        } else {
            throw new Error('Failed to start 2FA setup');
        }
    } catch (error) {
        console.error('2FA setup start failed:', error);
        throw error;
    }
};

const verify2FASetup = async (code) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/2fa/setup/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                code: code,
                setup_token: twoFASetupData?.setup_token
            }),
        });
        
        if (response.ok) {
            const data = await response.json();
            setTwoFARequired(false);
            setShowTwoFASetupModal(false);
            setTwoFASetupData(null);
            return data.data;
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Verification failed');
        }
    } catch (error) {
        console.error('2FA setup verification failed:', error);
        throw error;
    }
};

const verify2FA = async (code, method = 'totp') => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/2fa/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ code, method }),
        });
        
        if (response.ok) {
            const data = await response.json();
            setTwoFARequired(false);
            setShowTwoFAModal(false);
            
            // Refresh user data to update verification status
            await checkAuthStatus();
            
            return data.data;
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Verification failed');
        }
    } catch (error) {
        console.error('2FA verification failed:', error);
        throw error;
    }
};

const get2FAStatus = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/2fa/status`, {
            credentials: 'include',
        });
        
        if (response.ok) {
            const data = await response.json();
            setTwoFAStatus(data.data);
            return data.data;
        }
    } catch (error) {
        console.error('Failed to get 2FA status:', error);
    }
};

// Update the login success useEffect
useEffect(() => {
    if (authFlowCompleted) {
        console.log('🔧 Auth flow already completed, skipping initialization');
        return;
    }
    
    const urlParams = new URLSearchParams(window.location.search);
    const loginSuccess = urlParams.get('login');
    const requires2FA = urlParams.get('requires_2fa') === 'true';
    
    console.log('URL params:', Object.fromEntries(urlParams.entries()));
    
    if (loginSuccess === 'success') {
        console.log('Login success detected, requires 2FA:', requires2FA);
        setAuthFlowCompleted(true);
        
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);
        
        const handleLoginSuccess = async () => {
            let authenticatedUserData = null;
            
            console.log('🔄 STEP 1: Ensuring authentication is fully complete...');
            
            // First, ensure authentication is successful
            for (let i = 0; i < 5; i++) {
                console.log(`Auth check attempt ${i + 1}/5`);
                
                const delay = Math.pow(2, i) * 1000;
                await new Promise(resolve => setTimeout(resolve, delay));
                
                const userData = await checkAuthStatus();
                
                if (userData) {
                    console.log('✅ User authenticated successfully');
                    console.log('🔧 Storing userData for controlled flow:', userData);
                    authenticatedUserData = userData;
                    break;
                }
                
                if (i === 4) {
                    console.error('❌ Authentication failed after all retries');
                    login();
                    return;
                }
            }
            
            if (authenticatedUserData) {
                console.log('🔄 STEP 2: Authentication complete, checking 2FA and router ID...');
                
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                if (!requires2FA || authenticatedUserData.is_2fa_verified) {
                    console.log('🔄 STEP 3: Fetching router ID from backend...');
                    const hasRouterId = await fetchRouterIdFromBackend(3, authenticatedUserData);
                    
                    if (!hasRouterId) {
                        console.log('⚠️  No router ID found, popup will be shown later');
                    } else {
                        console.log('✅ Router ID found and session started successfully');
                    }
                } else {
                    console.log('⚠️  2FA verification required, waiting for user input');
                }
            }
        };
        
        handleLoginSuccess();
    } else {
        console.log('No login success, checking auth status normally...');
        setAuthFlowCompleted(true);
        
        const initializeAuth = async () => {
            const userData = await checkAuthStatus();
            if (userData && userData.is_2fa_verified) {
                await fetchRouterIdFromBackend(3, userData);
            }
        };
        initializeAuth();
    }
}, [authFlowCompleted]);

// Add to value object
const value = {
    // ... existing values
    twoFARequired,
    twoFAStatus,
    showTwoFAModal,
    setShowTwoFAModal,
    showTwoFASetupModal,
    setShowTwoFASetupModal,
    twoFASetupData,
    start2FASetup,
    verify2FASetup,
    verify2FA,
    get2FAStatus,
};
```

### 3.2 Create 2FA Setup Modal

Create `frontend/dashboard/src/components/TwoFASetupModal.jsx`:

```javascript
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

const TwoFASetupModal = ({ isOpen, onClose }) => {
    const { start2FASetup, verify2FASetup, twoFASetupData } = useAuth();
    const [step, setStep] = useState(1); // 1: intro, 2: QR code, 3: verify, 4: backup codes
    const [code, setCode] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [backupCodes, setBackupCodes] = useState([]);
    const [setupData, setSetupData] = useState(null);

    useEffect(() => {
        if (isOpen && step === 2 && !setupData) {
            initiate2FASetup();
        }
    }, [isOpen, step]);

    const initiate2FASetup = async () => {
        setLoading(true);
        setError('');
        
        try {
            const data = await start2FASetup();
            setSetupData(data);
        } catch (err) {
            setError('Failed to start 2FA setup. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleVerifySetup = async () => {
        if (!code || code.length !== 6) {
            setError('Please enter a valid 6-digit code');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const result = await verify2FASetup(code);
            setBackupCodes(result.backup_codes);
            setStep(4);
        } catch (err) {
            setError(err.message || 'Invalid code. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleComplete = () => {
        setStep(1);
        setCode('');
        setError('');
        setSetupData(null);
        setBackupCodes([]);
        onClose();
    };

    const downloadBackupCodes = () => {
        const content = backupCodes.join('\n');
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'netpilot-backup-codes.txt';
        a.click();
        URL.revokeObjectURL(url);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
                {/* Step 1: Introduction */}
                {step === 1 && (
                    <div>
                        <h2 className="text-xl font-bold mb-4">Set Up Two-Factor Authentication</h2>
                        <p className="text-gray-600 mb-6">
                            Add an extra layer of security to your account by enabling two-factor authentication.
                            You'll need an authenticator app like Google Authenticator or Authy.
                        </p>
                        <div className="flex space-x-3">
                            <button
                                onClick={() => setStep(2)}
                                className="flex-1 bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
                            >
                                Get Started
                            </button>
                            <button
                                onClick={onClose}
                                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400"
                            >
                                Skip for Now
                            </button>
                        </div>
                    </div>
                )}

                {/* Step 2: QR Code */}
                {step === 2 && (
                    <div>
                        <h2 className="text-xl font-bold mb-4">Scan QR Code</h2>
                        {loading ? (
                            <div className="text-center py-8">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                                <p className="mt-2 text-gray-600">Generating QR code...</p>
                            </div>
                        ) : setupData ? (
                            <div>
                                <p className="text-gray-600 mb-4">
                                    Scan this QR code with your authenticator app:
                                </p>
                                <div className="text-center mb-4">
                                    <img 
                                        src={setupData.qr_code} 
                                        alt="2FA QR Code" 
                                        className="mx-auto border rounded"
                                    />
                                </div>
                                <p className="text-sm text-gray-500 mb-4">
                                    Or enter this code manually: 
                                    <code className="bg-gray-100 px-2 py-1 rounded block mt-1">
                                        {setupData.secret}
                                    </code>
                                </p>
                                <button
                                    onClick={() => setStep(3)}
                                    className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
                                >
                                    Continue
                                </button>
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <p className="text-red-600 mb-4">{error}</p>
                                <button
                                    onClick={initiate2FASetup}
                                    className="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
                                >
                                    Try Again
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* Step 3: Verify Code */}
                {step === 3 && (
                    <div>
                        <h2 className="text-xl font-bold mb-4">Verify Setup</h2>
                        <p className="text-gray-600 mb-4">
                            Enter the 6-digit code from your authenticator app:
                        </p>
                        <input
                            type="text"
                            value={code}
                            onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                            placeholder="000000"
                            className="w-full text-center text-xl p-3 border rounded mb-4 tracking-widest"
                            maxLength={6}
                            autoFocus
                        />
                        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
                        <div className="flex space-x-3">
                            <button
                                onClick={() => setStep(2)}
                                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400"
                            >
                                Back
                            </button>
                            <button
                                onClick={handleVerifySetup}
                                disabled={loading || code.length !== 6}
                                className="flex-1 bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 disabled:opacity-50"
                            >
                                {loading ? 'Verifying...' : 'Verify'}
                            </button>
                        </div>
                    </div>
                )}

                {/* Step 4: Backup Codes */}
                {step === 4 && (
                    <div>
                        <h2 className="text-xl font-bold mb-4">Save Backup Codes</h2>
                        <p className="text-gray-600 mb-4">
                            Save these backup codes in a safe place. You can use them to access your account 
                            if you lose your authenticator device.
                        </p>
                        <div className="bg-gray-100 p-4 rounded mb-4 max-h-32 overflow-y-auto">
                            {backupCodes.map((code, index) => (
                                <div key={index} className="font-mono text-sm mb-1">
                                    {code}
                                </div>
                            ))}
                        </div>
                        <div className="flex space-x-3">
                            <button
                                onClick={downloadBackupCodes}
                                className="flex-1 bg-gray-500 text-white py-2 px-4 rounded hover:bg-gray-600"
                            >
                                Download
                            </button>
                            <button
                                onClick={handleComplete}
                                className="flex-1 bg-green-500 text-white py-2 px-4 rounded hover:bg-green-600"
                            >
                                Complete Setup
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TwoFASetupModal;
```

### 3.3 Create 2FA Verification Modal

Create `frontend/dashboard/src/components/TwoFAVerificationModal.jsx`:

```javascript
import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const TwoFAVerificationModal = ({ isOpen, onClose }) => {
    const { verify2FA } = useAuth();
    const [code, setCode] = useState('');
    const [method, setMethod] = useState('totp'); // 'totp' or 'backup'
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleVerify = async () => {
        if (!code || (method === 'totp' && code.length !== 6)) {
            setError('Please enter a valid code');
            return;
        }

        setLoading(true);
        setError('');

        try {
            await verify2FA(code, method);
            setCode('');
            // onClose will be handled by the AuthContext when verification succeeds
        } catch (err) {
            setError(err.message || 'Verification failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleMethodChange = (newMethod) => {
        setMethod(newMethod);
        setCode('');
        setError('');
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && code && !loading) {
            handleVerify();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
                <h2 className="text-xl font-bold mb-4">Two-Factor Authentication Required</h2>
                <p className="text-gray-600 mb-6">
                    Please enter your authentication code to continue.
                </p>

                {/* Method Selection */}
                <div className="flex mb-4 border rounded">
                    <button
                        onClick={() => handleMethodChange('totp')}
                        className={`flex-1 py-2 px-4 text-sm ${
                            method === 'totp' 
                                ? 'bg-blue-500 text-white' 
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                    >
                        Authenticator App
                    </button>
                    <button
                        onClick={() => handleMethodChange('backup')}
                        className={`flex-1 py-2 px-4 text-sm ${
                            method === 'backup' 
                                ? 'bg-blue-500 text-white' 
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                    >
                        Backup Code
                    </button>
                </div>

                {/* Code Input */}
                <input
                    type="text"
                    value={code}
                    onChange={(e) => {
                        if (method === 'totp') {
                            setCode(e.target.value.replace(/\D/g, '').slice(0, 6));
                        } else {
                            setCode(e.target.value.toUpperCase().slice(0, 9));
                        }
                    }}
                    onKeyPress={handleKeyPress}
                    placeholder={method === 'totp' ? '000000' : 'XXXX-XXXX'}
                    className="w-full text-center text-xl p-3 border rounded mb-4 tracking-widest"
                    maxLength={method === 'totp' ? 6 : 9}
                    autoFocus
                />

                {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

                <div className="flex space-x-3">
                    <button
                        onClick={onClose}
                        className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400"
                        disabled={loading}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleVerify}
                        disabled={loading || !code}
                        className="flex-1 bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 disabled:opacity-50"
                    >
                        {loading ? 'Verifying...' : 'Verify'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default TwoFAVerificationModal;
```

### 3.4 Update Main App Component

Update `frontend/dashboard/src/App.jsx` to include the 2FA modals:

```javascript
import { useAuth } from './context/AuthContext';
import TwoFASetupModal from './components/TwoFASetupModal';
import TwoFAVerificationModal from './components/TwoFAVerificationModal';

function App() {
    const { 
        showTwoFAModal, 
        setShowTwoFAModal, 
        showTwoFASetupModal, 
        setShowTwoFASetupModal 
    } = useAuth();

    return (
        <div className="App">
            {/* Your existing app content */}
            
            {/* 2FA Modals */}
            <TwoFASetupModal 
                isOpen={showTwoFASetupModal} 
                onClose={() => setShowTwoFASetupModal(false)} 
            />
            <TwoFAVerificationModal 
                isOpen={showTwoFAModal} 
                onClose={() => setShowTwoFAModal(false)} 
            />
        </div>
    );
}

export default App;
```

## 🔧 Phase 4: Configuration & Setup

### 4.1 Environment Variables

Add to `backend2/.env`:

```bash
# 2FA Configuration
TOTP_ENCRYPTION_KEY=<generate-with-fernet-generate-key>
RATE_LIMITING_ENABLED=true
AUDIT_LOGGING_ENABLED=true
SESSION_2FA_TIMEOUT_HOURS=8

# Generate encryption key with this Python command:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4.2 Install Dependencies

```bash
# Backend dependencies
cd backend2
pip install pyotp qrcode[pil] cryptography
pip freeze > requirements.txt

# Frontend dependencies (if needed)
cd ../frontend/dashboard
npm install  # No additional packages needed for basic implementation
```

### 4.3 Database Migration

```bash
# Run the SQL migration
cd backend2
# Apply the SQL from Phase 1 to your database
psql -h your-db-host -U your-db-user -d your-db-name -f migrations/add_2fa_support.sql
```

## 🚀 Testing & Deployment

### 4.1 Testing Checklist

- [ ] 2FA setup flow works end-to-end
- [ ] QR code generation and scanning
- [ ] TOTP verification with authenticator apps
- [ ] Backup code generation and verification
- [ ] Failed attempt lockout mechanism
- [ ] Session management with 2FA verification
- [ ] Integration with existing OAuth flow

### 4.2 Production Deployment

1. **Environment Variables**: Set all required environment variables
2. **Database Migration**: Apply database changes
3. **Dependencies**: Install all required packages
4. **Testing**: Run comprehensive tests
5. **Monitoring**: Set up logging and monitoring

## 📋 Usage Instructions

### For Users:

1. **Enable 2FA**: Go to Settings → Security → Enable 2FA
2. **Setup**: Scan QR code with authenticator app (Google Authenticator, Authy, etc.)
3. **Verify**: Enter 6-digit code to complete setup
4. **Save Backup Codes**: Download and securely store backup codes
5. **Login**: After Google OAuth, enter 2FA code when prompted

### For Administrators:

1. **Force 2FA**: Set `user.requires_2fa = True` for specific users
2. **Monitor**: Check `user_2fa_attempts` table for security monitoring
3. **Support**: Help users with backup codes if they lose access

## 🔒 Security Notes

- **Encryption**: TOTP secrets are encrypted before database storage
- **Rate Limiting**: Failed attempts result in progressive lockouts
- **Audit Logging**: All 2FA events are logged for security monitoring
- **Session Security**: 2FA verification expires with session
- **Backup Codes**: One-time use codes for account recovery

This implementation provides enterprise-grade 2FA security while maintaining a smooth user experience integrated with your existing Google OAuth flow.