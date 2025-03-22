from flask import Flask, request, jsonify
from services.block_ip import block_mac_address, unblock_mac_address, get_blocked_devices
from services.limit_bandwidth import set_bandwidth_limit, remove_bandwidth_limit, get_bandwidth_limit
from utils.ssh_client import ssh_manager
from services.network_scanner import scan_network
from services.router_scanner import scan_network_via_router
from flask_cors import CORS
from services.subnets_manager import add_ip, remove_ip, clear_ips
from utils.path_utils import get_data_folder
from utils.response_helpers import success, error
import os
import json
from db.device_repository import get_all_devices, update_device_name, clear_devices
from db.schema_initializer import initialize_all_tables
import sys

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

initialize_all_tables()

''' 
    API endpoint for health checking.
    Returns a simple success message to confirm the server is running.
'''
@app.route("/health", methods=["GET"])
def health():
    return success("Server is healthy")

''' 
    API endpoint to add a subnet IP to the scan list.
    Expects JSON: { "ip": "<subnet>" }
'''
@app.route("/config/add_ip", methods=["POST"])
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
@app.route("/config/remove_ip", methods=["POST"])
def remove_ip_route():
    data = request.get_json()
    ip = data.get("ip")
    if not ip:
        return error("Missing IP address")
    return jsonify(remove_ip(ip))

''' 
    API endpoint to clear all subnet IPs from the scan list.
'''
@app.route("/config/clear_ips", methods=["POST"])
def clear_ips_route():
    return jsonify(clear_ips())

''' 
    API endpoint to retrieve all currently blocked devices.
'''
@app.route("/api/blocked_devices", methods=["GET"])
def get_blocked():
    return jsonify(get_blocked_devices())

''' 
    API endpoint to gracefully shut down the server and SSH session.
'''
@app.route("/api/shutdown", methods=["POST"])
def shutdown():
    ssh_manager.close_connection()
    return success("Server and SSH session closed")

''' 
    API endpoint to perform a local network scan and return active devices.
'''
@app.route("/api/network_scan", methods=["GET"])
def network_scan():
    return jsonify(scan_network())

''' 
    API endpoint to perform a scan using the OpenWrt router's DHCP leases.
'''
@app.route("/api/router_scan", methods=["GET"])
def router_scan():
    return jsonify(scan_network_via_router())

''' 
    API endpoint to retrieve all devices from the database.
'''
@app.route("/db/devices", methods=["GET"])
def get_devices():
    devices = get_all_devices()
    return jsonify(success(data=[{
        "mac": d[0],
        "ip": d[1],
        "hostname": d[2],
        "device_name": d[3],
        "first_seen": d[4],
        "last_seen": d[5]
    } for d in devices]))

''' 
    API endpoint to update a user-defined name for a device.
    Expects JSON: { "mac": "<mac_address>", "device_name": "<name>" }
'''
@app.route("/db/device_name", methods=["PATCH"])
def update_device_name_route():
    data = request.get_json()
    mac = data.get("mac")
    device_name = data.get("device_name")
    if not mac or not device_name:
        return error("Missing 'mac' or 'device_name' in request body")
    success_status = update_device_name(mac, device_name)
    if success_status:
        return success("Device name updated successfully")
    else:
        return error("Device not found", status_code=404)

''' 
    API endpoint to clear all device records from the database.
'''
@app.route("/db/clear", methods=["DELETE"])
def clear_devices_route():
    clear_devices()
    return success("All devices cleared from the database")

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=server_port, debug=True)
    except KeyboardInterrupt:
        ssh_manager.close_connection()
