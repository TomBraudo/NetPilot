from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

# Import blueprints (without database dependencies)
from auth import auth_bp, init_oauth
from endpoints.health import health_bp
from endpoints.whitelist import whitelist_bp
from endpoints.blacklist import blacklist_bp
from endpoints.wifi import wifi_bp
from endpoints.api import network_bp

def create_test_app():
    """Create a minimal Flask app without database integration"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.getenv('SECRET_KEY', 'my-strong-secret-key')
    
    # Enable CORS with credentials support
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    CORS(app, 
         origins=cors_origins,
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
    app = create_test_app()
    print("Starting test server without database integration...")
    
    # Get server configuration from environment
    server_host = os.getenv('SERVER_HOST', '127.0.0.1')
    server_port = int(os.getenv('SERVER_PORT', '5000'))
    
    app.run(debug=True, host=server_host, port=server_port) 