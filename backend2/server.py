from flask import Flask, g
from flask_cors import CORS
import os
import argparse
from decouple import config
from datetime import timedelta

# Import database
from database.connection import db
from database.session import get_db_session

# Import blueprints
from auth import auth_bp, init_oauth
from endpoints.health import health_bp
from endpoints.whitelist import whitelist_bp
from endpoints.network import network_bp
from endpoints.session import session_bp
from endpoints.settings import settings_bp

def create_app(dev_mode=False, dev_user_id=None):
    """Create and configure the Flask application
    
    Args:
        dev_mode (bool): Enable development mode with authentication bypass
        dev_user_id (str): User ID to use in development mode
    """
    app = Flask(__name__)
    
    # Development mode configuration
    app.config['DEV_MODE'] = dev_mode
    app.config['DEV_USER_ID'] = dev_user_id
    
    if dev_mode:
        print("=" * 50)
        print("🚨 WARNING: DEVELOPMENT MODE ACTIVE 🚨")
        print(f"Authentication bypassed with fake user_id: {dev_user_id}")
        print("DO NOT USE IN PRODUCTION!")
        print("=" * 50)
    
    # Load environment variables
    os.environ['DB_HOST'] = config('DB_HOST', default='127.0.0.1')
    os.environ['DB_PORT'] = config('DB_PORT', default='5432')
    os.environ['DB_USERNAME'] = config('DB_USERNAME', default='netpilot_user')
    os.environ['DB_PASSWORD'] = config('DB_PASSWORD', default='your_secure_password_here')
    os.environ['DB_NAME'] = config('DB_NAME', default='netpilot_db')
    os.environ['DATABASE_URL'] = config('DATABASE_URL', default='')

    # Command Server config
    app.config['COMMAND_SERVER_URL'] = config('COMMAND_SERVER_URL', default='http://34.38.207.87:5000')
    app.config['COMMAND_SERVER_TIMEOUT'] = config('COMMAND_SERVER_TIMEOUT', default=30, cast=int)
    
    # Configuration
    app.secret_key = config('SECRET_KEY', default='my-strong-secret-key')
    
    # CRITICAL: Enhanced session configuration for deterministic behavior
    app.config.update(
        SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
        SESSION_COOKIE_HTTPONLY=False,  # Allow JavaScript access for debugging
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_DOMAIN=None,  # Allow all domains
        SESSION_COOKIE_PATH='/',  # Set path to root
        PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
        SESSION_REFRESH_EACH_REQUEST=True,
        SESSION_COOKIE_NAME='session'
    )
    
    # Enable CORS with credentials support
    CORS(app, 
         origins=['http://localhost:3000', 'http://localhost:5173'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Initialize OAuth
    init_oauth(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)  # No prefix - routes will be /login, /authorize, etc.
    app.register_blueprint(health_bp)
    app.register_blueprint(whitelist_bp, url_prefix='/api/whitelist')
    app.register_blueprint(network_bp, url_prefix='/api/network')
    app.register_blueprint(session_bp, url_prefix='/api/session')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    
    # Root route
    @app.route('/')
    def root():
         return '<a href="/login">Log in with Google</a>'

    # Initialize database tables (optional, for dev)
    with app.app_context():
        try:
            db.create_tables()
            print("Database tables initialized")
        except Exception as e:
            print(f"Warning: Could not initialize database tables: {e}")

    # Attach db session to each request
    @app.before_request
    def before_request():
        g.db_session = db.get_session()
        
        # Check if we're in development mode first
        if app.config.get('DEV_MODE', False):
            dev_user_id = app.config.get('DEV_USER_ID')
            g.user_id = dev_user_id
            print(f"DEV MODE: Using fake user_id: {dev_user_id}")
            return  # Skip normal authentication flow
        
        # Normal authentication flow for production
        from flask import session as flask_session, request as flask_request
        user_id = flask_session.get('user_id')
        
        # Debug session state
        print(f"DEBUG: Session keys: {list(flask_session.keys())}")
        print(f"DEBUG: user_id from session: {user_id}")
        print(f"DEBUG: 'user' in session: {'user' in flask_session}")
        
        # Enhanced logging for whitelist add endpoint
        if '/api/whitelist/add' in flask_request.url:
            print(f"🔍 WHITELIST ADD REQUEST DEBUG:")
            print(f"  URL: {flask_request.url}")
            print(f"  Method: {flask_request.method}")
            print(f"  Cookies: {dict(flask_request.cookies)}")
            print(f"  Session data: {dict(flask_session)}")
            print(f"  user_id: {user_id}")
        
        if user_id:
            # Validate user_id format and set in g
            if user_id != 'None' and len(str(user_id)) > 0:
                g.user_id = user_id
                print(f"Request with valid user_id: {user_id}")
            else:
                # Clean up invalid user_id
                flask_session.pop('user_id', None)
                print(f"Cleaned up invalid user_id: {user_id}")
        else:
            print("Request without user_id in session")

    @app.teardown_request
    def teardown_request(exception):
        if hasattr(g, 'db_session'):
            if exception:
                g.db_session.rollback()
            g.db_session.close()

    return app

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='NetPilot Backend Server')
    parser.add_argument('-d', '--dev', type=str, metavar='USER_ID',
                       help='Run in development mode with fake user_id (e.g., -d test-user-123)')
    
    args = parser.parse_args()
    
    # Determine if we're in dev mode
    dev_mode = args.dev is not None
    dev_user_id = args.dev if dev_mode else None
    
    # Create app with appropriate mode
    app = create_app(dev_mode=dev_mode, dev_user_id=dev_user_id)
    
    # Show usage info
    if not dev_mode:
        print("🚀 Starting NetPilot server in PRODUCTION mode")
        print("💡 For development mode: python server.py -d <fake_user_id>")
    
    app.run(debug=True, host='0.0.0.0', port=5000)