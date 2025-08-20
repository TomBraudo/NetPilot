from flask import Flask, g, request
from flask_cors import CORS
import os
import argparse
from decouple import config
from datetime import timedelta

# Import database
from database.connection import db
from database.session import get_db_session
from managers.transaction_manager import TransactionManager
from managers.db_session_context import SessionContext

# Import blueprints
from auth import auth_bp, init_oauth
from endpoints.health import health_bp
from endpoints.network import network_bp
from endpoints.session import session_bp
from endpoints.settings import settings_bp
from endpoints.twofa import twofa_bp
from endpoints.monitor import monitor_bp
from endpoints.agh import agh_bp
from endpoints.bandwidth import bandwidth_bp
from endpoints.device_groups import device_groups_bp
from endpoints.devices import devices_bp
from endpoints.scheduled_tasks import scheduled_tasks_bp
from services.scheduler_bootstrap import init_scheduler

def create_app(dev_mode=False, dev_user_id=None):
    """Create and configure the Flask application
    
    Args:
        dev_mode (bool): Enable development mode with authentication bypass
        dev_user_id (str): User ID to use in development mode
    """
    print("🚀 Creating NetPilot Flask application...")
    
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
    
    # HTTPS Configuration
    use_https = config('USE_HTTPS', default=False, cast=bool)
    secure_cookies = config('SECURE_COOKIES', default=False, cast=bool)
    
    # CRITICAL: Enhanced session configuration for deterministic behavior
    app.config.update(
        SESSION_COOKIE_SECURE=secure_cookies,  # True in production with HTTPS
        SESSION_COOKIE_HTTPONLY=True,  # Prevent JavaScript access for security
        SESSION_COOKIE_SAMESITE='Lax' if not use_https else 'None',  # 'None' required for HTTPS cross-origin
        SESSION_COOKIE_DOMAIN=None,  # Allow all domains
        SESSION_COOKIE_PATH='/',  # Set path to root
        PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
        SESSION_REFRESH_EACH_REQUEST=True,
        SESSION_COOKIE_NAME='session'
    )
    
    # Enable CORS with credentials support
    cors_origins = config('CORS_ORIGINS', default='http://localhost:3000,http://localhost:5173').split(',')
    CORS(app, 
         origins=cors_origins,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Initialize OAuth
    init_oauth(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)  # No prefix - routes will be /login, /authorize, etc.
    app.register_blueprint(health_bp)
    # Removed whitelist/blacklist blueprints
    app.register_blueprint(network_bp, url_prefix='/api/network')
    app.register_blueprint(session_bp, url_prefix='/api/session')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')

    app.register_blueprint(twofa_bp, url_prefix='/api/2fa')

    app.register_blueprint(monitor_bp)  # monitor_bp already has url_prefix='/api/monitor'
    app.register_blueprint(agh_bp, url_prefix='/api/agh')
    app.register_blueprint(bandwidth_bp, url_prefix='/api/bandwidth')
    app.register_blueprint(device_groups_bp, url_prefix='/api/device-groups')
    app.register_blueprint(devices_bp, url_prefix='/api/devices')
    app.register_blueprint(scheduled_tasks_bp, url_prefix='/api')
    
    # Root route
    @app.route('/')
    def root():
         return '<a href="/login">Log in with Google</a>'
    
    # Simple health check for Cloud Run
    @app.route('/_ah/health')
    def app_engine_health():
        return {'status': 'ok', 'service': 'backend2'}, 200

    # Initialize database tables (optional, for dev)
    try:
        with app.app_context():
            print("🔧 Initializing database tables...")
            db.create_tables()
            print("✅ Database tables initialized successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize database tables: {e}")
        print("🔄 Continuing without database initialization...")

    # Initialize scheduler (Phase 3)
    try:
        print("🔧 Initializing scheduler...")
        init_scheduler(app)
        print("✅ Scheduler initialized successfully")
    except Exception as e:
        print(f"⚠️  Warning: Scheduler failed to start: {e}")
        print("🔄 Continuing without scheduler...")

    # Attach db session to each request
    @app.before_request
    def before_request():
        from flask import request as flask_request
        
        # Skip authentication for OPTIONS requests (CORS preflight)
        if flask_request.method == 'OPTIONS':
            return
        
        # Initialize centralized transaction/session handling
        TransactionManager.begin_request()
        # Temporary bridge: keep g.db_session for legacy code until Phase 3 completes
        g.db_session = SessionContext.get()
        
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
        
        # Removed whitelist debug logging
        
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

    @app.after_request
    def after_request(response):
        # Delegate commit/rollback decision to TransactionManager
        return TransactionManager.finalize_response(response)

    @app.teardown_request
    def teardown_request(exception):
        # Close session and clear context
        TransactionManager.teardown()

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
    
    # Test that the app was created successfully
    print("✅ Flask application created successfully")
    
    # Show usage info
    if not dev_mode:
        print("🚀 Starting NetPilot server in PRODUCTION mode")
        print("💡 For development mode: python server.py -d <fake_user_id>")
    else:
        print("🔧 Starting NetPilot server in DEVELOPMENT mode")
    
    # Get server configuration from environment
    server_host = config('SERVER_HOST', default='0.0.0.0')
    # Use PORT environment variable for Cloud Run, fallback to 5000 for local dev
    server_port = int(os.environ.get('PORT', config('SERVER_PORT', default=5000)))
    
    # Only enable debug mode in development
    debug_mode = dev_mode and config('FLASK_DEBUG', default=False, cast=bool)
    
    print(f"🚀 Starting server on {server_host}:{server_port}")
    print(f"🌍 Environment PORT: {os.environ.get('PORT', 'not set')}")
    print(f"⚙️  Config SERVER_PORT: {config('SERVER_PORT', default=5000)}")
    
    app.run(debug=debug_mode, host=server_host, port=server_port)