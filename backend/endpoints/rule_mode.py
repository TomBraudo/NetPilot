from flask import Blueprint, request, jsonify
from services.rule_mode import set_rule_mode, get_rule_mode, BLACKLIST_MODE, WHITELIST_MODE
from utils.response_helpers import success, error
from utils.ssh_client import ssh_manager

rule_mode_bp = Blueprint('rule_mode', __name__)

'''
    API endpoint to get the current rule mode (blacklist or whitelist)
'''
@rule_mode_bp.route("/api/rule_mode", methods=["GET"])
def get_rule_mode_endpoint():
    mode = get_rule_mode()
    return jsonify(success(data={"mode": mode}))

'''
    API endpoint to set the rule mode
    Expects JSON: {
        "mode": "blacklist" or "whitelist"
    }
'''
@rule_mode_bp.route("/api/rule_mode", methods=["POST"])
def set_rule_mode_endpoint():
    """Set the rule mode to blacklist or whitelist."""
    data = request.get_json()
    
    if not data:
        return jsonify(error("Missing request body"))
        
    mode = data.get("mode")
    
    if not mode:
        return jsonify(error("Missing 'mode' in request body"))
        
    # Get client IP for protection
    client_ip = request.remote_addr
    
    # Special handling for localhost - get real network interface IP instead
    if client_ip == "127.0.0.1":
        # Try to get a real LAN IP
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't need to be reachable
            s.connect(('10.255.255.255', 1))
            real_ip = s.getsockname()[0]
            client_ip = real_ip if real_ip != "127.0.0.1" else None
        except:
            client_ip = None
        finally:
            s.close()
    
    # Set the rule mode with client protection
    result = set_rule_mode(mode, client_ip=client_ip)
    return jsonify(result)

@rule_mode_bp.route("/api/test_rule_mode", methods=["GET"])
def test_rule_mode_endpoint():
    """Test the current rule mode behavior."""
    mode = get_rule_mode()
    
    # Get current firewall rules
    fw_cmd = "iptables -L FORWARD -n"
    fw_output, _ = ssh_manager.execute_command(fw_cmd)
    
    # Get WiFi configuration
    wifi_cmd = "uci show wireless | grep macfilter"
    wifi_output, _ = ssh_manager.execute_command(wifi_cmd)
    
    # Get allowed/blocked MAC addresses
    mac_cmd = "uci show wireless | grep maclist"
    mac_output, _ = ssh_manager.execute_command(mac_cmd)
    
    return jsonify(success(data={
        "current_mode": mode,
        "firewall_rules": fw_output,
        "wifi_configuration": wifi_output,
        "mac_lists": mac_output,
        "expected_behavior": {
            "new_devices": "Allowed" if mode == BLACKLIST_MODE else "Blocked",
            "blocked_devices": "Denied access",
            "allowed_devices": "Granted access"
        }
    })) 