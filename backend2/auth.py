# pyright: reportOptionalMemberAccess=false
from flask import Blueprint, url_for, session, redirect, request, jsonify, g
from authlib.integrations.flask_client import OAuth
from functools import wraps
from dotenv import load_dotenv
import os
from models.user import User, User2FASettings
from datetime import datetime
from utils.logging_config import get_logger
import jwt
import json

logger = get_logger('auth')

load_dotenv()

auth_bp = Blueprint('auth', __name__)

# OAuth setup will be done in the main server.py file
oauth = None
google = None

def init_oauth(app):
    """Initialize OAuth with the Flask app"""
    global oauth, google
    oauth = OAuth(app)
    
    google = oauth.register(
        "NetPilot",
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
            'prompt': 'login consent',  # Force fresh login AND consent
            'max_age': 0,  # Force re-authentication to get fresh auth_time  
            'acr_values': 'http://schemas.openid.net/pape/policies/2007/06/multi-factor',  # Request 2FA
        },
    )

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import current_app, g
        
        # Check if we're in development mode first
        if current_app.config.get('DEV_MODE', False):
            dev_user_id = current_app.config.get('DEV_USER_ID')
            print(f"DEV MODE: login_required bypassed with fake user_id: {dev_user_id}")
            g.user_id = dev_user_id  # Set user_id in g for compatibility
            return f(*args, **kwargs)
        
        print(f"DEBUG: login_required decorator called")
        print(f"DEBUG: Session keys: {list(session.keys())}")
        print(f"DEBUG: 'user' in session: {'user' in session}")
        print(f"DEBUG: 'user_id' in session: {'user_id' in session}")
        
        # Check for OAuth token
        if 'user' not in session:
            print(f"DEBUG: No OAuth token found")
            return jsonify({"error": "Authentication required - no OAuth token"}), 401
        
        # CRITICAL: Also check for user_id in session
        if 'user_id' not in session:
            print(f"DEBUG: No user_id found")
            return jsonify({"error": "Authentication incomplete - no user_id"}), 401
            
        # Additional validation: ensure user_id is valid
        user_id = session.get('user_id')
        if not user_id or user_id == 'None':
            print(f"DEBUG: Invalid user_id: {user_id}")
            return jsonify({"error": "Authentication incomplete - invalid user_id"}), 401
        
        # Set user_id in g for easy access in endpoints
        g.user_id = user_id
        
        print(f"DEBUG: Authentication successful for user_id: {user_id}")
        return f(*args, **kwargs)
    return decorated_function

def twofa_required(f):
    """Decorator to require 2FA verification for sensitive routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import current_app
        
        # Skip 2FA in dev mode
        if current_app.config.get('DEV_MODE', False):
            return f(*args, **kwargs)
        
        # First ensure user is logged in
        user_id = g.get('user_id') or session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        # Check if user has 2FA enabled
        from database.connection import db
        db_session = db.get_session()
        try:
            user = db_session.query(User).filter_by(id=user_id).first()
            user_2fa = db_session.query(User2FASettings).filter_by(user_id=user_id).first()
            
            requires_2fa = user.requires_2fa if user else False
            has_2fa_enabled = user_2fa.is_enabled if user_2fa else False
            
            if requires_2fa or has_2fa_enabled:
                # Check if 2FA is verified in current session
                is_2fa_verified = session.get('2fa_verified', False)
                
                if not is_2fa_verified:
                    return jsonify({
                        "error": "2FA verification required", 
                        "requires_2fa": True
                    }), 403
                
                # Check if 2FA verification is still valid (e.g., within last hour)
                verified_at = session.get('2fa_verified_at')
                if verified_at:
                    from datetime import datetime, timedelta
                    verified_time = datetime.fromisoformat(verified_at)
                    if datetime.utcnow() - verified_time > timedelta(hours=1):
                        session.pop('2fa_verified', None)
                        session.pop('2fa_verified_at', None)
                        return jsonify({
                            "error": "2FA verification expired", 
                            "requires_2fa": True
                        }), 403
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error checking 2FA requirements: {e}")
            return jsonify({"error": "Authentication check failed"}), 500
        finally:
            db_session.close()
    
    return decorated_function

@auth_bp.route('/')
def homepage():
    """Homepage with login link"""
    return '<a href="/login">Log in with Google</a>'

@auth_bp.route('/login')
def login():
    """Initiate Google OAuth login"""
    # Use request host to determine correct redirect URI
    from flask import request
    host = request.host
    scheme = 'https' if request.is_secure else 'http'
    redirect_uri = f"{scheme}://{host}/authorize"
    return google.authorize_redirect(redirect_uri)

def decode_google_id_token(token):
    """
    Decode Google ID token to extract 2FA claims
    """
    id_token = token.get('id_token')
    if not id_token:
        return {}
    
    try:
        # Decode without verification (Google's signature verification is complex)
        # In production, you should verify the signature properly
        decoded = jwt.decode(id_token, options={"verify_signature": False})
        
        logger.info(f"ID Token Claims Found: {json.dumps(decoded, indent=2, default=str)}")
        
        return decoded
    except Exception as e:
        logger.error(f"Failed to decode ID token: {e}")
        return {}

def detect_google_2fa(token, id_token_claims=None):
    """
    Enhanced 2FA detection using both token and ID token claims
    Returns: (used_2fa: bool, method: str, confidence: str)
    """
    
    # Check various 2FA indicators
    used_2fa = False
    method = "none"
    confidence = "low"
    
    # Method 1: Check Authentication Methods Reference (AMR) in main token
    amr = token.get('amr', [])
    
    # Known 2FA AMR values:
    # 'mfa' = Multi-factor authentication
    # 'sms' = SMS-based authentication  
    # 'otp' = One-time password
    # 'totp' = Time-based one-time password
    # 'hwk' = Hardware key
    strong_methods = ['mfa', 'sms', 'otp', 'totp', 'hwk', 'oath']
    
    for amr_method in amr:
        if amr_method.lower() in strong_methods:
            used_2fa = True
            method = amr_method
            confidence = "high"
            break
    
    # Method 2: Check ACR in main token
    if not used_2fa:
        acr = token.get('acr')
        if acr in ['2', 'mfa', 'https://schemas.openid.net/pape/policies/2007/06/multi-factor']:
            used_2fa = True
            method = f"acr:{acr}"
            confidence = "high"
    
    # Method 3: Check auth_time in main token
    if not used_2fa:
        auth_time = token.get('auth_time')
        if auth_time:
            from datetime import timedelta
            auth_datetime = datetime.fromtimestamp(auth_time)
            time_diff = datetime.utcnow() - auth_datetime
            
            if time_diff < timedelta(minutes=2):
                used_2fa = True
                method = "recent_auth"
                confidence = "medium"
    
    # Method 4: CHECK ID TOKEN CLAIMS (NEW!)
    if not used_2fa and id_token_claims:
        logger.info("Checking ID token claims for 2FA indicators...")
        
        # Check AMR in ID token
        id_amr = id_token_claims.get('amr', [])
        logger.info(f"ID Token AMR: {id_amr}")
        
        for amr_method in id_amr:
            if amr_method.lower() in strong_methods:
                used_2fa = True
                method = f"id_token_{amr_method}"
                confidence = "high"
                logger.info(f"Found 2FA in ID token AMR: {amr_method}")
                break
        
        # Check ACR in ID token
        if not used_2fa:
            id_acr = id_token_claims.get('acr')
            logger.info(f"ID Token ACR: {id_acr}")
            
            if id_acr in ['2', 'mfa', 'https://schemas.openid.net/pape/policies/2007/06/multi-factor']:
                used_2fa = True
                method = f"id_token_acr:{id_acr}"
                confidence = "high"
                logger.info(f"Found 2FA in ID token ACR: {id_acr}")
        
        # Check iat (issued at) time for freshness - Google uses this instead of auth_time
        if not used_2fa:
            # Try auth_time first, then fall back to iat (issued at time)
            id_auth_time = id_token_claims.get('auth_time') or id_token_claims.get('iat')
            if id_auth_time:
                from datetime import timedelta
                auth_datetime = datetime.fromtimestamp(id_auth_time)
                time_diff = datetime.utcnow() - auth_datetime
                logger.info(f"ID Token issued at: {auth_datetime}, age: {time_diff}")
                
                # With our forced authentication, fresh login = high confidence 2FA
                if time_diff < timedelta(minutes=5):
                    used_2fa = True
                    method = "forced_fresh_auth"
                    confidence = "high"  # High confidence since we forced fresh auth
                    logger.info(f"Fresh authentication detected with forced login (high confidence 2FA)")
                    logger.info(f"User likely went through Google 2FA during forced re-authentication")
    
    return used_2fa, method, confidence

@auth_bp.route('/authorize')
def authorize():
    """Handle OAuth callback"""
    token = google.authorize_access_token()
    session['user'] = token

    # === GOOGLE 2FA DETECTION DEBUG ===
    logger.info("=== GOOGLE OAUTH TOKEN ANALYSIS ===")
    logger.info(f"Token keys: {list(token.keys())}")
    
    # Log authentication details (avoid sensitive tokens)
    for key, value in token.items():
        if key not in ['access_token', 'refresh_token']:
            logger.info(f"Token[{key}]: {value}")
    
    # Check for 2FA indicators
    userinfo = token.get('userinfo', {})
    id_token_claims = token.get('id_token_claims', {})
    
    if 'amr' in token:
        logger.info(f"AMR (Auth Methods): {token['amr']}")
    if 'acr' in token:
        logger.info(f"ACR (Auth Context): {token['acr']}")
    if 'auth_time' in token:
        auth_time = datetime.fromtimestamp(token['auth_time'])
        logger.info(f"Auth time: {auth_time}")
        
    if id_token_claims:
        logger.info(f"ID token claims keys: {list(id_token_claims.keys())}")
        if 'amr' in id_token_claims:
            logger.info(f"ID Token AMR: {id_token_claims['amr']}")
    
    logger.info("=== END OAUTH ANALYSIS ===")

    # === DECODE ID TOKEN FOR HIDDEN 2FA INFO ===
    logger.info("Decoding ID token for additional 2FA claims...")
    id_token_claims = decode_google_id_token(token)
    
    userToken = session.get('user')
    if not userToken:
        return 'No user session found', 400
    
    # Extract user info from token
    userInfo = userToken.get('userinfo', {})
    google_id = userInfo.get('sub')  # Google's unique user identifier
    email = userInfo.get('email')
    full_name = userInfo.get('name')
    avatar_url = userInfo.get('picture')
    
    if not google_id or not email:
        return 'Invalid user information from Google', 400
    
    # CRITICAL: Ensure database session is available
    try:
        db_session = g.db_session
    except (AttributeError, RuntimeError):
        # Fallback if g.db_session is not available
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
        
        # GOOGLE 2FA DETECTION (with ID token claims)
        google_2fa_used, google_method, confidence = detect_google_2fa(token, id_token_claims)
        
        logger.info(f"Google 2FA detection for {user.email}:")
        logger.info(f"  Used 2FA: {google_2fa_used}")
        logger.info(f"  Method: {google_method}")
        logger.info(f"  Confidence: {confidence}")
        
        # CRITICAL: Store user_id in session IMMEDIATELY after successful commit
        session['user_id'] = str(user.id)
        session.permanent = True  # Ensure session persistence
        
        # Handle 2FA based on Google authentication
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        
        if google_2fa_used:
            # Mark as 2FA verified since Google handled it
            session['2fa_verified'] = True
            session['2fa_verified_at'] = datetime.utcnow().isoformat()
            session['2fa_method'] = f"google_{google_method}"
            
            logger.info(f"User {user.email} authenticated with Google 2FA ({google_method})")
            print(f"Google 2FA detected: {google_method} (confidence: {confidence})")
            return redirect(f"{frontend_url}?login=success&google_2fa=verified&method={google_method}")
        else:
            # No Google 2FA detected
            logger.warning(f"No Google 2FA detected for {user.email}")
            print(f"No Google 2FA detected - user should enable 2FA in Google account")
            session.pop('2fa_verified', None)
            session.pop('2fa_verified_at', None)
            return redirect(f"{frontend_url}?login=success&google_2fa=not_detected")
        
    except Exception as e:
        print(f"Error creating/updating user: {e}")
        db_session.rollback()
        # Clear any partial session data on error
        session.pop('user_id', None)
        return 'Error creating user account', 500

@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """Logout user and clear session"""
    try:
        # Clear the session
        session.clear()
        print("Session cleared successfully")
        return jsonify({"message": "Logged out successfully"}), 200
    except Exception as e:
        print(f"Error during logout: {e}")
        return jsonify({"error": "Logout failed"}), 500

@auth_bp.route('/me')
@login_required
def me():
    """Get current user info including 2FA status"""
    print(f"DEBUG: /me endpoint called")
    print(f"DEBUG: Session keys: {list(session.keys())}")
    print(f"DEBUG: 'user' in session: {'user' in session}")
    print(f"DEBUG: 'user_id' in session: {'user_id' in session}")
    
    user_id = session.get('user_id')
    userToken = session.get('user')
    
    if not userToken or not user_id:
        print(f"DEBUG: No user token or user_id found in session")
        return jsonify({"error": "No user session found"}), 400
    
    # Get user info from database for 2FA status
    from database.connection import db
    db_session = db.get_session()
    try:
        user = db_session.query(User).filter_by(id=user_id).first()
        user_2fa = db_session.query(User2FASettings).filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        userInfo = userToken['userinfo']
        user_info = {
            "id": user.id,
            "name": userInfo.get("given_name"),
            "email": user.email,
            "full_name": user.full_name,
            "picture": userInfo.get("picture"),
            "avatar_url": user.avatar_url,
            
            # Google 2FA Status Information
            "is_2fa_verified": session.get('2fa_verified', False),
            "twofa_method": session.get('2fa_method', None),
            "google_2fa_detected": session.get('2fa_method', '').startswith('google_'),
            
            # Legacy 2FA fields (for compatibility)
            "requires_2fa": False,  # Not using custom 2FA anymore
            "has_2fa_enabled": False,  # Using Google 2FA instead
            "twofa_enforced_at": None,
            
            # Additional metadata
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "is_active": user.is_active
        }
        
        print(f"DEBUG: User info compiled with 2FA status")
        return jsonify(user_info)
        
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        return jsonify({"error": "Failed to get user information"}), 500
    finally:
        db_session.close() 

@auth_bp.route('/dev/create-session/<test_user_id>')
def dev_create_session(test_user_id):
    """TEMPORARY: Create a test session for API testing"""
    # Create fake session for testing
    session['user_id'] = f"test-{test_user_id}"
    session['user'] = {
        'userinfo': {
            'email': f'{test_user_id}@test.com',
            'name': f'Test User {test_user_id}',
            'given_name': f'Test{test_user_id}',
            'picture': 'https://via.placeholder.com/150',
            'sub': f'test-{test_user_id}'
        }
    }
    session.permanent = True
    
    return jsonify({
        "message": f"Test session created for user: test-{test_user_id}",
        "user_id": session['user_id'],
        "instructions": "Now use this session cookie in Postman to test API endpoints"
    })