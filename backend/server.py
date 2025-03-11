from flask import Flask, request, jsonify
from services.block_ip import block_mac_address, unblock_mac_address
from services.limit_bandwidth import set_bandwidth_limit, remove_bandwidth_limit
from utils.ssh_client import ssh_manager
from services.network_scanner import scan_network
from services.router_scanner import scan_network_via_router
import json

# Load router configurationn
with open("config.json") as config_file:
    config = json.load(config_file)

server_port = config["server_port"]

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint.
    """
    return jsonify({"status": "OK"})

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

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=server_port, debug=True, ssl_context="adhoc")
    except KeyboardInterrupt:
        ssh_manager.close_connection()
