# pyright: reportOptionalMemberAccess=false
from flask import Blueprint, url_for, session, redirect, request, jsonify, g
from authlib.integrations.flask_client import OAuth
from functools import wraps
from dotenv import load_dotenv
import os
from models.user import User
from datetime import datetime

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
            return f(*args, **kwargs)
        
        print(f"DEBUG: login_required decorator called")
        print(f"DEBUG: Session keys: {list(session.keys())}")
        print(f"DEBUG: 'user' in session: {'user' in session}")
        print(f"DEBUG: 'user_id' in session: {'user_id' in session}")
        
        # Temporarily allow access if user_id exists in session
        if 'user_id' in session:
            user_id = session.get('user_id')
            if user_id and user_id != 'None':
                print(f"DEBUG: Allowing access with user_id: {user_id}")
                return f(*args, **kwargs)
        
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
        
        print(f"DEBUG: Authentication successful")
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/')
def homepage():
    """Homepage with login link"""
    return '<a href="/login">Log in with Google</a>'

@auth_bp.route('/login')
def login():
    """Initiate Google OAuth login"""
    redirect_uri = "http://localhost:5000/authorize"
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
        
        # CRITICAL: Store user_id in session IMMEDIATELY after successful commit
        session['user_id'] = str(user.id)
        session.permanent = True  # Ensure session persistence
        
        print(f"User authenticated successfully: {user.email} (ID: {user.id})")
        print(f"Session updated with user_id: {session.get('user_id')}")
        
        # Redirect back to frontend with success
        frontend_url = "http://localhost:5173"
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
    """Get current user info"""
    print(f"DEBUG: /me endpoint called")
    print(f"DEBUG: Session keys: {list(session.keys())}")
    print(f"DEBUG: 'user' in session: {'user' in session}")
    print(f"DEBUG: 'user_id' in session: {'user_id' in session}")
    
    userToken = session.get('user')
    if not userToken:
        print(f"DEBUG: No user token found in session")
        return jsonify({"error": "No user session found"}), 400
    
    print(f"DEBUG: User token found: {type(userToken)}")
    userInfo = userToken['userinfo']
    return jsonify({
        "name": userInfo.get("given_name"),
        "email": userInfo.get("email"),
        "picture": userInfo.get("picture")
    }) 