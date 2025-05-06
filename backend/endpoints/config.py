from flask import Blueprint, request, jsonify
from services.subnets_manager import add_ip, remove_ip, clear_ips
from utils.response_helpers import error, success
import os
from dotenv import load_dotenv
from utils.path_utils import get_data_folder

config_bp = Blueprint('config', __name__)

def get_env_path():
    data_folder = get_data_folder()
    return os.path.join(data_folder, ".env")

env_path = get_env_path()
if not os.path.exists(env_path):
    raise FileNotFoundError(f".env file not found at {env_path}")

load_dotenv(env_path)

server_port = os.getenv("SERVER_PORT")
if server_port is None:
    raise ValueError("SERVER_PORT is not set in the .env file")
server_port = int(server_port)

'''
    API endpoint to set the admin username and password for the web interface.
    Expects JSON: { "username": "<username>", "password": "<password>" }
    This will update the .env file in the data folder.
'''
@config_bp.route("/config/set_admin", methods=["POST"])
def set_admin():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return error("Missing 'username' or 'password' in request body")
    
    set_env_value(env_path, "USERNAME", username)
    set_env_value(env_path, "PASSWORD", password)
        
    return success("Admin credentials updated successfully")

def set_env_value(env_path, key, value):
    lines = []
    found = False
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith(f"{key}="):
                lines.append(f"{key}={value}\n")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"{key}={value}\n")
    with open(env_path, "w") as f:
        f.writelines(lines)