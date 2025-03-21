from flask import Flask, request, jsonify
from services.block_ip import block_mac_address, unblock_mac_address, get_blocked_devices
from services.limit_bandwidth import set_bandwidth_limit, remove_bandwidth_limit, get_bandwidth_limit
from utils.ssh_client import ssh_manager
from services.network_scanner import scan_network
from services.router_scanner import scan_network_via_router
from flask_cors import CORS
from services.subnets_manager import add_ip, remove_ip, clear_ips
from utils.path_utils import get_data_folder
import os
import json
from db.device_repository import init_db, get_all_devices, update_device_name
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

init_db()


@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint.
    """
    return jsonify({"status": "OK"})

@app.route("/config/add_ip", methods=["POST"])
def add_ip_route():
    data = request.get_json()
    ip = data.get("ip")
    response, status = add_ip(ip)
    return jsonify(response), status

@app.route("/config/remove_ip", methods=["POST"])
def remove_ip_route():
    data = request.get_json()
    ip = data.get("ip")
    response, status = remove_ip(ip)
    return jsonify(response), status

@app.route("/config/clear_ips", methods=["POST"])
def clear_ips_route():
    response, status = clear_ips()
    return jsonify(response), status
    
        

@app.route("/api/block", methods=["POST"])
def block_device():
    """
    API endpoint to block a device by IP.
    """
    data = request.get_json()
    target_ip = data.get("ip")

    if not target_ip:
        return jsonify({"error": "Missing IP address"}), 400

    result = block_mac_address(target_ip)
    return jsonify(result)

@app.route("/api/unblock", methods=["POST"])
def unblock_device():
    """
    API endpoint to unblock a device by IP.
    """
    data = request.get_json()
    target_ip = data.get("ip")

    if not target_ip:
        return jsonify({"error": "Missing IP address"}), 400

    result = unblock_mac_address(target_ip)  # Calls the unblock function

    return jsonify(result)

@app.route("/api/blocked_devices", methods=["GET"])
def get_blocked():
    """
    API endpoint to get all blocked devices.
    """
    result = get_blocked_devices()
    return jsonify(result)

@app.route("/api/limit_bandwidth", methods=["POST"])
def limit_bandwidth():
    """
    API endpoint to limit bandwidth for a device.
    """
    data = request.get_json()
    target_ip = data.get("ip")
    bandwidth = data.get("bandwidth")

    if not target_ip or not bandwidth:
        return jsonify({"error": "Missing parameters"}), 400

    result = set_bandwidth_limit(target_ip, bandwidth)
    return jsonify(result)


@app.route("/api/unlimit_bandwidth", methods=["POST"])
def unlimit_bandwidth():
    """
    API endpoint to remove bandwidth limits for a device by IP.
    """
    data = request.get_json()
    target_ip = data.get("ip")

    if not target_ip:
        return jsonify({"error": "Missing IP address"}), 400

    result = remove_bandwidth_limit(target_ip)  # Calls the function

    return jsonify(result)

@app.route("/api/get_bandwidth_limit", methods=["GET"])
def get_bandwidth():
    """
    API endpoint to get the bandwidth limit for a device by IP.
    """
    target_ip = request.args.get("ip")

    if not target_ip:
        return jsonify({"error": "Missing IP address"}), 400

    result = get_bandwidth_limit(target_ip)  # Calls the function

@app.route("/api/shutdown", methods=["POST"])
def shutdown():
    """
    API endpoint to gracefully shut down the server and SSH session.
    """
    ssh_manager.close_connection()
    return jsonify({"message": "Server and SSH session closed."})

@app.route("/api/network_scan", methods=["GET"])
def network_scan():
    """
    API endpoint to scan the network and return connected devices.
    """
    result = scan_network()
    return jsonify(result)

@app.route("/api/router_scan", methods=["GET"])
def router_scan():
    """
    API endpoint to scan the network using the OpenWrt router.
    """
    result = scan_network_via_router()
    return jsonify(result)

@app.route("/db/devices", methods=["GET"])
def get_devices():
    """
    API endpoint to retrieve all devices from the database.
    """
    devices = get_all_devices()
    return jsonify([{
        "mac": d[0],
        "ip": d[1],
        "hostname": d[2],
        "device_name": d[3],
        "first_seen": d[4],
        "last_seen": d[5]
    } for d in devices])
    
@app.route("/db/device_name", methods=["PATCH"])
def update_device_name_route():
    """
    API endpoint to update a device's name by MAC address.
    """
    data = request.get_json()
    mac = data.get("mac")
    device_name = data.get("device_name")

    if not mac or not device_name:
        return jsonify({"error": "Missing 'mac' or 'device_name' in request body"}), 400

    success = update_device_name(mac, device_name)
    if success:
        return jsonify({"message": "Device name updated successfully"})
    else:
        return jsonify({"error": "Device not found"}), 404

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=server_port, debug=True)
    except KeyboardInterrupt:
        ssh_manager.close_connection()
