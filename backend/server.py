from flask import Flask
from flask_cors import CORS
from utils.ssh_client import ssh_manager
from utils.logging_config import get_logger
import os
import atexit
from dotenv import load_dotenv

# Get logger for this module
logger = get_logger(__name__)

# Import all blueprints
from endpoints.health import health_bp
from endpoints.api import network_bp
from endpoints.wifi import wifi_bp
from endpoints.whitelist import whitelist_bp
from endpoints.blacklist import blacklist_bp

# Load environment variables
load_dotenv()

server_port = os.getenv("SERVER_PORT", 3000)
if isinstance(server_port, str):
    server_port = int(server_port)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Register all blueprints
logger.info("Registering API blueprints")
app.register_blueprint(health_bp)
app.register_blueprint(network_bp)
app.register_blueprint(wifi_bp)
app.register_blueprint(whitelist_bp)
app.register_blueprint(blacklist_bp)
logger.info("API blueprints registered")

# Function to clean up resources on exit
def cleanup_resources():
    logger.info("Cleaning up resources")
    ssh_manager.close_connection()
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

