from flask import Flask
from flask_cors import CORS
from utils.path_utils import get_data_folder
from db.schema_initializer import initialize_all_tables
from utils.ssh_client import ssh_manager
from db.tinydb_client import db_client
from utils.logging_config import get_logger
import os
import json
import atexit
from dotenv import load_dotenv

# Get logger for this module
logger = get_logger(__name__)

# Import all blueprints
from endpoints.health import health_bp
from endpoints.config import config_bp
from endpoints.api import network_bp
from endpoints.db import db_bp
from endpoints.wifi import wifi_bp
from endpoints.whitelist import whitelist_bp

# Function to get the external .env path
def get_env_path():
    data_folder = get_data_folder()
    return os.path.join(data_folder, ".env")

# Load .env externally
env_path = get_env_path()
if not os.path.exists(env_path):
    raise FileNotFoundError(f".env file not found at {env_path}")

load_dotenv(env_path)

server_port = os.getenv("SERVER_PORT")
if server_port is None:
    raise ValueError("SERVER_PORT is not set in the .env file")
server_port = int(server_port)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize database tables
logger.info("Initializing database tables")
initialize_all_tables()
logger.info("Database tables initialized")

# Register all blueprints
logger.info("Registering API blueprints")
app.register_blueprint(health_bp)
app.register_blueprint(config_bp)
app.register_blueprint(network_bp)
app.register_blueprint(db_bp)
app.register_blueprint(wifi_bp)
app.register_blueprint(whitelist_bp)
logger.info("API blueprints registered")

# Function to clean up resources on exit
def cleanup_resources():
    logger.info("Cleaning up resources")
    ssh_manager.close_connection()
    db_client.close()
    logger.info("Resources cleaned up")

# Register cleanup function on application exit
atexit.register(cleanup_resources)

if __name__ == "__main__":
    try:
        logger.info(f"Starting server on port {server_port}")
        app.run(host="0.0.0.0", port=server_port, debug=True)
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
        cleanup_resources()
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}", exc_info=True)
        cleanup_resources()

