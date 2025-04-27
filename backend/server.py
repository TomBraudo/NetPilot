from flask import Flask
from flask_cors import CORS
from utils.path_utils import get_data_folder
from db.schema_initializer import initialize_all_tables
from utils.ssh_client import ssh_manager
from db.tinydb_client import db_client
import os
import json
import atexit

# Import all blueprints
from endpoints.health import health_bp
from endpoints.config import config_bp
from endpoints.api import network_bp
from endpoints.db import db_bp
from endpoints.wifi import wifi_bp

# Function to get the external config.json path
def get_config_path():
    data_folder = get_data_folder()
    return os.path.join(data_folder, "config.json")

# Load config.json externally
config_path = get_config_path()
if not os.path.exists(config_path):
    raise FileNotFoundError(f"config.json not found at {config_path}")

with open(config_path, "r") as f:
    config = json.load(f)

server_port = config["server_port"]

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

