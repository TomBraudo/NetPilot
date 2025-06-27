from pathlib import Path
import os
from dotenv import load_dotenv
from flask import Flask, request, g, jsonify

# -----------------------------------------------------------------------------
# Load environment variables EARLY so that downstream imports (e.g. ssh_client)
# can read them.  When developing locally we keep secrets in `backend/.env.local`.
# On the VM that file will be absent, so the process simply relies on real
# environment variables set by the service manager.
# -----------------------------------------------------------------------------
_env_local_path = Path(__file__).resolve().parent / ".env.local"
if _env_local_path.exists():
    load_dotenv(_env_local_path)

# Rest of the imports can safely rely on env vars
from flask_cors import CORS
from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
import atexit
from utils.response_helpers import error

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
server_port = os.getenv("SERVER_PORT", 3000)
if isinstance(server_port, str):
    server_port = int(server_port)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --------------------------------------------------------------------------
# Create and attach the RouterConnectionManager to the app context
# --------------------------------------------------------------------------
app.router_connection_manager = RouterConnectionManager()

# List of blueprints that do not require session/router validation
EXEMPT_BLUEPRINTS = ['session', 'health']

# -----------------------------------------------------------------------------
# Attach sessionId & routerId from incoming requests into Flask `g` so that
# lower layers (ssh_client / RouterConnectionManager) can pick them up without
# each service needing to pass the values explicitly.
# -----------------------------------------------------------------------------
@app.before_request
def _capture_session_router():
    # If the request is for a blueprint that doesn't need this validation, skip.
    if request.blueprint in EXEMPT_BLUEPRINTS:
        return

    if request.method in ("POST", "PUT", "PATCH"):
        data = request.get_json(silent=True) or {}
    else:
        data = {}
    g.session_id = request.args.get("sessionId") or data.get("sessionId")
    g.router_id = request.args.get("routerId") or data.get("routerId")

    # For protected endpoints, validate that the required IDs were provided.
    if not g.session_id:
        # routerId is checked separately because some future endpoints might
        # operate on a session without a specific router.
        return jsonify(error("sessionId is required for this endpoint.", status_code=400)), 400
    
    if not g.router_id:
        return jsonify(error("routerId is required for this endpoint.", status_code=400)), 400

    # Check if the session is valid and active.
    if not app.router_connection_manager.get_session_status(g.session_id):
        return jsonify(error(f"Session not found or has expired: {g.session_id}", status_code=404)), 404

# Register all blueprints
logger.info("Registering API blueprints")
app.register_blueprint(health_bp)
app.register_blueprint(network_bp, url_prefix='/api')
app.register_blueprint(wifi_bp, url_prefix='/api')
app.register_blueprint(whitelist_bp, url_prefix='/api')
app.register_blueprint(blacklist_bp, url_prefix='/api')
app.register_blueprint(session_bp, url_prefix='/api')
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

