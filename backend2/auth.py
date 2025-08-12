# pyright: reportOptionalMemberAccess=false
from flask import Blueprint, url_for, session, redirect, request, jsonify, g
from authlib.integrations.flask_client import OAuth
from functools import wraps
from dotenv import load_dotenv
import os
from models.user import User, User2FASettings
from datetime import datetime
from utils.logging_config import get_logger

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
        client_kwargs={'scope': 'openid email profile'},
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
        
        # Check if user requires 2FA
        user_2fa = db_session.query(User2FASettings).filter_by(user_id=str(user.id)).first()
        requires_2fa = user.requires_2fa or (user_2fa and user_2fa.is_enabled)
        
        # CRITICAL: Store user_id in session IMMEDIATELY after successful commit
        session['user_id'] = str(user.id)
        session.permanent = True  # Ensure session persistence
        
        # Clear any previous 2FA verification for new login
        session.pop('2fa_verified', None)
        session.pop('2fa_verified_at', None)
        
        print(f"User authenticated successfully: {user.email} (ID: {user.id})")
        print(f"Session updated with user_id: {session.get('user_id')}")
        print(f"2FA required: {requires_2fa}")
        
        # Redirect back to frontend with 2FA indicator
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        
        if requires_2fa:
            if user_2fa and user_2fa.is_enabled:
                # User has 2FA enabled - redirect to verification
                return redirect(f"{frontend_url}?login=success&requires_2fa=true&action=verify")
            else:
                # User needs to set up 2FA
                return redirect(f"{frontend_url}?login=success&requires_2fa=true&action=setup")
        else:
            # No 2FA required
            return redirect(f"{frontend_url}?login=success")
        
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
            
            # 2FA Status Information
            "requires_2fa": user.requires_2fa or (user_2fa and user_2fa.is_enabled),
            "has_2fa_enabled": user_2fa.is_enabled if user_2fa else False,
            "is_2fa_verified": session.get('2fa_verified', False),
            "twofa_enforced_at": user.twofa_enforced_at.isoformat() if user.twofa_enforced_at else None,
            
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