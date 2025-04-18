from flask import Blueprint, request, jsonify
from services.subnets_manager import add_ip, remove_ip, clear_ips
from utils.response_helpers import error, success
import json
import os

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
    from server import config_path
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return error("Missing 'username' or 'password' in request body")
    
    # Save the new credentials to config.json
    with open(config_path, "r") as f:
        config = json.load(f)
        
    config["username"] = username
    config["password"] = password
    
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
        
    return success("Admin credentials updated successfully")