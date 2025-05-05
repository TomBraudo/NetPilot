from flask import Blueprint, request, jsonify
from services.subnets_manager import add_ip, remove_ip, clear_ips
from utils.response_helpers import error, success
import os
from utils.path_utils import get_data_folder
from dotenv import load_dotenv, set_key
import logging

# Configure logging
logger = logging.getLogger(__name__)

config_bp = Blueprint('config', __name__)

''' 
    API endpoint to add a subnet IP to the scan list.
    Expects JSON: { "ip": "<subnet>" }
'''
@config_bp.route("/config/add_ip", methods=["POST"])
def add_ip_route():
    data = request.get_json()
    ip = data.get("ip")
    if not ip:
        return error("Missing IP address")
    return jsonify(add_ip(ip))

''' 
    API endpoint to remove a subnet IP from the scan list.
    Expects JSON: { "ip": "<subnet>" }
'''
@config_bp.route("/config/remove_ip", methods=["POST"])
def remove_ip_route():
    data = request.get_json()
    ip = data.get("ip")
    if not ip:
        return error("Missing IP address")
    return jsonify(remove_ip(ip))

''' 
    API endpoint to clear all subnet IPs from the scan list.
'''
@config_bp.route("/config/clear_ips", methods=["POST"])
def clear_ips_route():
    return jsonify(clear_ips())

'''
    API endpoint to set the admin username and password for the web interface.
    Expects JSON: { "username": "<username>", "password": "<password>" }
'''
@config_bp.route("/config/set_admin", methods=["POST"])
def set_admin():
    env_path = os.path.join(get_data_folder(), '.env')
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return error("Missing 'username' or 'password' in request body")
    
    try:
        # Update the environment variables in the .env file
        set_key(env_path, 'ROUTER_USERNAME', username)
        set_key(env_path, 'ROUTER_PASSWORD', password)
        
        # Also update in current process
        os.environ['ROUTER_USERNAME'] = username
        os.environ['ROUTER_PASSWORD'] = password
        
        # Update the SSH manager with new credentials
        from utils.ssh_client import ssh_manager
        ssh_manager.username = username
        ssh_manager.password = password
        
        return success("Admin credentials updated successfully")
    except Exception as e:
        logger.error(f"Error updating admin credentials: {str(e)}")
        return error(f"Failed to update credentials: {str(e)}")

'''
    API endpoint to set the router connection details.
    Expects JSON: { "router_ip": "<ip>", "username": "<username>", "password": "<password>" }
'''
@config_bp.route("/config/set_router", methods=["POST"])
def set_router():
    env_path = os.path.join(get_data_folder(), '.env')
    data = request.get_json()
    router_ip = data.get("router_ip")
    username = data.get("username")
    password = data.get("password")
    
    # Validate required fields
    missing_fields = []
    if not router_ip:
        missing_fields.append("router_ip")
    if not username:
        missing_fields.append("username")
    if not password:
        missing_fields.append("password")
        
    if missing_fields:
        return error(f"Missing required fields: {', '.join(missing_fields)}")
    
    try:
        # Update the environment variables in the .env file
        set_key(env_path, 'ROUTER_IP', router_ip)
        set_key(env_path, 'ROUTER_USERNAME', username)
        set_key(env_path, 'ROUTER_PASSWORD', password)
        
        # Also update in current process
        os.environ['ROUTER_IP'] = router_ip
        os.environ['ROUTER_USERNAME'] = username
        os.environ['ROUTER_PASSWORD'] = password
        
        # Update the SSH manager with new credentials
        from utils.ssh_client import ssh_manager
        ssh_manager.router_ip = router_ip
        ssh_manager.username = username
        ssh_manager.password = password
        
        # Test the connection
        ssh_manager.close_connection()  # Close existing connection if any
        success_connection = ssh_manager.connect()
        
        if success_connection:
            return success("Router connection details updated successfully")
        else:
            return error("Router credentials saved, but connection test failed")
    except Exception as e:
        logger.error(f"Error updating router credentials: {str(e)}")
        return error(f"Failed to update router credentials: {str(e)}")