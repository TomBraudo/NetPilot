from flask import Flask
from flask_cors import CORS
from utils.path_utils import get_data_folder
from db.schema_initializer import initialize_all_tables
from utils.ssh_client import ssh_manager
from db.tinydb_client import db_client
import os
import atexit
from dotenv import load_dotenv
import socket
from services.admin_protection import register_admin_device

# Import all blueprints
from endpoints.health import health_bp
from endpoints.config import config_bp
from endpoints.api import network_bp
from endpoints.db import db_bp
from endpoints.wifi import wifi_bp
from endpoints.device_protection import protection_bp
from endpoints.rule_mode import rule_mode_bp
from endpoints.admin_protection import admin_bp

# Load environment variables from .env file
env_path = os.path.join(get_data_folder(), '.env')
load_dotenv(dotenv_path=env_path)

# Get server port from environment variable
server_port = int(os.environ.get('SERVER_PORT', 5000))

# Check if database should be initialized (default to False for existing data persistence)
should_init_db = os.environ.get('INIT_DB', 'False').lower() == 'true'

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize database tables only if required
if should_init_db:
    initialize_all_tables()

# Register all blueprints
app.register_blueprint(health_bp)
app.register_blueprint(config_bp)
app.register_blueprint(network_bp)
app.register_blueprint(db_bp)
app.register_blueprint(wifi_bp)
app.register_blueprint(protection_bp)
app.register_blueprint(rule_mode_bp)
app.register_blueprint(admin_bp)

# Auto-register server device as admin
def register_server_as_admin():
    # Get local IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    
    # Register this device as admin
    if ip and ip != '127.0.0.1':
        print(f"Auto-registering server device (IP: {ip}) as admin device")
        register_admin_device(ip_address=ip)

# Function to clean up resources on exit
def cleanup_resources():
    ssh_manager.close_connection()
    db_client.close()

# Register cleanup function on application exit
atexit.register(cleanup_resources)

if __name__ == "__main__":
    try:
        # Auto-register the server as admin
        register_server_as_admin()
        
        app.run(host="0.0.0.0", port=server_port, debug=True)
    except KeyboardInterrupt:
        cleanup_resources()
    except Exception as e:
        print(f"Error: {str(e)}")
        cleanup_resources()

