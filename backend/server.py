from pathlib import Path
import os
from dotenv import load_dotenv
from flask import Flask, request, g, jsonify

# -----------------------------------------------------------------------------
# Load environment variables EARLY so that downstream imports (e.g. ssh_client)
# can read them.  When developing locally we keep secrets in `backend/.env.local`.
# On the VM that file will be absent, so the process simply relies on the
# .env file and real environment variables set by the service manager.
# -----------------------------------------------------------------------------
_env_local_path = Path(__file__).resolve().parent / ".env.local"
_env_path = Path(__file__).resolve().parent / ".env"

if _env_local_path.exists():
    load_dotenv(_env_local_path)
elif _env_path.exists():
    load_dotenv(_env_path)

# Rest of the imports can safely rely on env vars
from flask_cors import CORS
from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
import atexit
from utils.middleware import verify_session_and_router

# Get logger for this module
logger = get_logger(__name__)

# Import all blueprints
from endpoints.health import health_bp
from endpoints.api import network_bp
from endpoints.wifi import wifi_bp
from endpoints.whitelist import whitelist_bp
from endpoints.blacklist import blacklist_bp
from endpoints.session import session_bp

# Load environment variables
# Support both COMMANDS-SERVER_PORT and SERVER_PORT for backward compatibility
# Also support SERVER_PORT_TEST for deployment testing
server_port = os.getenv("COMMANDS-SERVER_PORT", os.getenv("SERVER_PORT", 5000))
server_port_test = os.getenv("SERVER_PORT_TEST", 5001)

# Use test port if we're in test mode (indicated by SERVER_PORT_TEST being set)
if os.getenv("SERVER_PORT_TEST") is not None:
    server_port = server_port_test

if isinstance(server_port, str):
    server_port = int(server_port)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Register the session verification middleware to run before all requests
@app.before_request
def before_request_hook():
    # The verify_session_and_router function will check for session/router context
    # and return a response if checks fail, effectively protecting the endpoints.
    # It will internally skip checks for exempt endpoints like /health.
    response = verify_session_and_router()
    if response is not None:
        return response

# --------------------------------------------------------------------------
# Create and attach the RouterConnectionManager to the app context
# --------------------------------------------------------------------------
app.router_connection_manager = RouterConnectionManager()

# Register all blueprints
logger.info("Registering API blueprints")
app.register_blueprint(health_bp)
app.register_blueprint(network_bp, url_prefix='/api/network')
app.register_blueprint(wifi_bp, url_prefix='/api/wifi')
app.register_blueprint(whitelist_bp, url_prefix='/api/whitelist')
app.register_blueprint(blacklist_bp, url_prefix='/api/blacklist')
app.register_blueprint(session_bp, url_prefix='/api/session')
logger.info("API blueprints registered")

# Function to clean up resources on exit
def cleanup_resources():
    logger.info("Cleaning up resources")
    # ssh_manager.close_connection() - This is legacy, RCM handles it.
    if hasattr(app, 'router_connection_manager'):
        app.router_connection_manager.shutdown()
    logger.info("Resources cleaned up")

# Register cleanup function on application exit
atexit.register(cleanup_resources)

if __name__ == "__main__":
    try:
        logger.info(f"Starting Commands Server on port {server_port}")
        app.run(host="0.0.0.0", port=server_port, debug=True)
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
        cleanup_resources()
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}", exc_info=True)
        cleanup_resources()

