from flask import Blueprint, request, jsonify
from services.block_ip import block_mac_address, unblock_mac_address, get_blocked_devices, verify_block_status, debug_blocking
from services.limit_bandwidth import set_bandwidth_limit, remove_bandwidth_limit, get_bandwidth_limit
from services.reset_rules import reset_all_rules
from services.network_scanner import scan_network
from services.router_scanner import scan_network_via_router
from utils.ssh_client import ssh_manager
from utils.response_helpers import error, success
from db.device_repository import get_mac_from_ip
from db.device_groups_repository import set_rule_for_device, remove_rule_from_device
from services.apply_rules import apply_rule_with_blacklist_logic

network_bp = Blueprint('network', __name__)

''' 
    API endpoint to retrieve all currently blocked devices.
'''
@network_bp.route("/api/blocked_devices", methods=["GET"])
def get_blocked():
    return jsonify(get_blocked_devices())

''' 
    API endpoint to gracefully shut down the server and SSH session.
'''
@network_bp.route("/api/shutdown", methods=["POST"])
def shutdown():
    response = reset_all_rules()
    ssh_manager.close_connection()
    return jsonify(response)

''' 
    API endpoint to perform a local network scan and return active devices.
'''
@network_bp.route("/api/network_scan", methods=["GET"])
def network_scan():
    return jsonify(scan_network())

''' 
    API endpoint to perform a scan using the OpenWrt router's DHCP leases.
'''
@network_bp.route("/api/router_scan", methods=["GET"])
def router_scan():
    return jsonify(scan_network_via_router())

'''
    API endpoint to block a device by IP address.
    Expects JSON: { "ip": "<ip_address>" }
'''
@network_bp.route("/api/block", methods=["POST"])
def block():
    """Block a device from the network."""
    data = request.get_json()
    if not data:
        return jsonify(error("No data provided"))
        
    ip = data.get("ip")
    if not ip:
        return jsonify(error("No IP address provided"))
    
    # Prevent self-blocking
    client_ip = request.remote_addr
    if ip == client_ip:
        return jsonify(error("Cannot block your own device"))
        
    return jsonify(block_mac_address(ip))

'''
    API endpoint to unblock a device by IP address.
    Expects JSON: { "ip": "<ip_address>" }
'''
@network_bp.route("/api/unblock", methods=["POST"])
def unblock():
    data = request.get_json()
    ip = data.get("ip")
    if not ip:
        return error("Missing 'ip' in request body")
    mac = get_mac_from_ip(ip)
    if mac:
        # Pass both mac and ip to remove_rule_from_device
        remove_rule_from_device(mac, ip, "block")
    else:
        return error("Device not found")
    return jsonify(unblock_mac_address(ip))

'''
    API endpoint to set a bandwidth limit for a device in mbps.
    Expects JSON: { "ip": "<ip_address>", "bandwidth": "<bandwidth_limit_mbps>" }
'''
@network_bp.route("/api/limit_bandwidth", methods=["POST"])
def limit_bandwidth():
    data = request.get_json()
    ip = data.get("ip")
    limit = data.get("bandwidth")
    if not ip or not limit:
        return error("Missing 'ip' or 'bandwidth' in request body")
    
    mac = get_mac_from_ip(ip)
    if mac:
        # Pass both mac and ip to set_rule_for_device
        set_rule_for_device(mac, ip, "limit_bandwidth", limit)
    else:
        return error("Device not found")
    
    return jsonify(set_bandwidth_limit(ip, limit))
    
'''
    API endpoint to remove a bandwidth limit for a device.
    Expects JSON: { "ip": "<ip_address>" }
'''
@network_bp.route("/api/unlimit_bandwidth", methods=["POST"])
def unlimit_bandwidth():
    data = request.get_json()
    ip = data.get("ip")
    if not ip:
        return error("Missing 'ip' in request body")
    
    mac = get_mac_from_ip(ip)
    if mac:
        # Pass both mac and ip to remove_rule_from_device
        remove_rule_from_device(mac, ip, "limit_bandwidth")
    else:
        return error("Device not found")
    return jsonify(remove_bandwidth_limit(ip))

'''
    API endpoint to retrieve the bandwidth limit for a device.
    Expects JSON: { "ip": "<ip_address>" }
'''
@network_bp.route("/api/get_bandwidth_limit", methods=["GET"])
def get_limit():
    ip = request.args.get("ip")
    if not ip:
        return error("Missing 'ip' in query parameters")
    return jsonify(get_bandwidth_limit(ip))

'''
    API endpoint to reset all network rules
'''
@network_bp.route("/api/reset_all_rules", methods=["POST"])
def reset_rules_route():
    """Reset all network rules including bandwidth limits and blocks."""
    return jsonify(reset_all_rules())

'''
    API endpoint to apply a rule with blacklist/whitelist mode consideration.
    Expects JSON: { "rule_name": "<rule_name>", "rule_value": "<rule_value>", "group_name": "<group_name>" }
'''
@network_bp.route("/api/apply_rule_with_mode", methods=["POST"])
def apply_rule_with_mode():
    """Apply a rule with blacklist/whitelist mode consideration."""
    data = request.get_json()
    
    if not data:
        return jsonify(error("Missing request body"))
        
    rule_name = data.get("rule_name")
    rule_value = data.get("rule_value")
    group_name = data.get("group_name")
    
    if not rule_name:
        return jsonify(error("Missing 'rule_name' in request body"))
        
    # Call the new function with blacklist logic
    result = apply_rule_with_blacklist_logic(rule_name, rule_value, group_name)
    
    if result:
        return jsonify(success(f"Successfully applied {rule_name} rule with blacklist/whitelist logic"))
    else:
        return jsonify(error(f"Failed to apply {rule_name} rule"))

@network_bp.route("/api/block_device", methods=["POST"])
def block_device_route():
    """Block a device, with protection checks."""
    data = request.get_json()
    
    if not data:
        return jsonify(error("Missing request body"))
        
    target_ip = data.get("ip")
    
    if not target_ip:
        return jsonify(error("Missing 'ip' in request body"))
    
    # Get client IP address
    client_ip = request.remote_addr
    
    # Prevent self-blocking
    if target_ip == client_ip:
        return jsonify(error("Cannot block your own device"))
        
    # Continue with existing implementation...

@network_bp.route("/api/block_status", methods=["GET"])
def check_block_status():
    """Check if a device is effectively blocked."""
    mac = request.args.get("mac")
    
    if not mac:
        return jsonify(error("MAC address is required"))
    
    status = verify_block_status(mac)
    
    if status.get("is_connected") and (status.get("wifi_filters") or status.get("firewall_rules")):
        # Device is still connected despite blocking measures
        return jsonify(error("Warning: Device is still connected despite blocking measures"))
    
    if status.get("wifi_filters") or status.get("firewall_rules"):
        return jsonify(success("Device is blocked", data=status))
    else:
        return jsonify(error("Device is not blocked", data=status))

@network_bp.route("/api/debug_block", methods=["GET"])
def debug_block_endpoint():
    """Diagnose blocking issues for a device."""
    mac = request.args.get("mac")
    
    if not mac:
        return jsonify(error("MAC address is required"))
    
    diagnostics = debug_blocking(mac)
    return jsonify(success(data=diagnostics))