from flask import Flask
from flask_cors import CORS
from utils.path_utils import get_data_folder
from db.schema_initializer import initialize_all_tables
from utils.ssh_client import ssh_manager
from db.tinydb_client import db_client
import os
import json
import atexit
from dotenv import load_dotenv

# Import all blueprints
from endpoints.health import health_bp
from endpoints.config import config_bp
from endpoints.api import network_bp
from endpoints.db import db_bp
from endpoints.wifi import wifi_bp


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
initialize_all_tables()

# Register all blueprints
app.register_blueprint(health_bp)
app.register_blueprint(config_bp)
app.register_blueprint(network_bp)
app.register_blueprint(db_bp)
app.register_blueprint(wifi_bp)

# Function to clean up resources on exit
def cleanup_resources():
    ssh_manager.close_connection()
    db_client.close()

# Register cleanup function on application exit
atexit.register(cleanup_resources)

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=server_port, debug=True)
    except KeyboardInterrupt:
        cleanup_resources()
    except Exception as e:
        print(f"Error: {str(e)}")
        cleanup_resources()

