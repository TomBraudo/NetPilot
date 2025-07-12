from flask import Flask, g
from flask_cors import CORS
import os
from decouple import config

# Import database
from database.connection import db
from database.session import get_db_session

# Import blueprints
from auth import auth_bp, init_oauth
from endpoints.health import health_bp
from endpoints.whitelist import whitelist_bp
from endpoints.blacklist import blacklist_bp
from endpoints.wifi import wifi_bp
from endpoints.api import network_bp
from endpoints.devices import devices_bp
from endpoints.whitelist_new import whitelist_new_bp
from endpoints.blacklist_new import blacklist_bp as blacklist_new_bp

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load environment variables
    os.environ['DB_HOST'] = config('DB_HOST', default='127.0.0.1')
    os.environ['DB_PORT'] = config('DB_PORT', default='5432')
    os.environ['DB_USERNAME'] = config('DB_USERNAME', default='netpilot_user')
    os.environ['DB_PASSWORD'] = config('DB_PASSWORD', default='your_secure_password_here')
    os.environ['DB_NAME'] = config('DB_NAME', default='netpilot_db')
    os.environ['DATABASE_URL'] = config('DATABASE_URL', default='')

    # Configuration
    app.secret_key = config('SECRET_KEY', default='my-strong-secret-key')
    
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
    app.register_blueprint(blacklist_bp, url_prefix='/api/blacklist')
    app.register_blueprint(wifi_bp, url_prefix='/api/wifi')
    app.register_blueprint(network_bp, url_prefix='/api/network')
    app.register_blueprint(devices_bp, url_prefix='/api/devices')
    app.register_blueprint(whitelist_new_bp, url_prefix='/api/whitelist-new')
    app.register_blueprint(blacklist_new_bp, url_prefix='/api/blacklist-new')
    
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

    @app.teardown_request
    def teardown_request(exception):
        if hasattr(g, 'db_session'):
            if exception:
                g.db_session.rollback()
            g.db_session.close()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)