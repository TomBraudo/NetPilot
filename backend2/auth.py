# pyright: reportOptionalMemberAccess=false
from flask import Blueprint, url_for, session, redirect, request, jsonify
from authlib.integrations.flask_client import OAuth
from functools import wraps

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
        client_id='1053980213438-p4jvv47k3gmcuce206m5iv8cht0gpqhu.apps.googleusercontent.com',
        client_secret='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',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "Authentication required"}), 401
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
    
    # Redirect back to frontend with success
    frontend_url = "http://localhost:5173"
    return redirect(f"{frontend_url}?login=success")

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
    userToken = session.get('user')
    if not userToken:
        return jsonify({"error": "No user session found"}), 400
    
    userInfo = userToken['userinfo']
    return jsonify({
        "name": userInfo.get("given_name"),
        "email": userInfo.get("email"),
        "picture": userInfo.get("picture")
    }) 