from flask import Flask
from flask_cors import CORS
import os

# Import blueprints
from auth import auth_bp, init_oauth
from endpoints.health import health_bp
from endpoints.whitelist import whitelist_bp
from endpoints.blacklist import blacklist_bp
from endpoints.wifi import wifi_bp
from endpoints.api import network_bp

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = 'my-strong-secret-key'
    
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
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(whitelist_bp, url_prefix='/api/whitelist')
    app.register_blueprint(blacklist_bp, url_prefix='/api/blacklist')
    app.register_blueprint(wifi_bp, url_prefix='/api/wifi')
    app.register_blueprint(network_bp, url_prefix='/api/network')
    
    # Root route
    @app.route('/')
    def root():
         return '<a href="/login">Log in with Google</a>'
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)