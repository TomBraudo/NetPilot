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
    data = request.get_json()
    
    if not data:
        return jsonify(error("Missing request body"))
        
    mode = data.get("mode")
    
    if not mode:
        return jsonify(error("Missing 'mode' in request body"))
        
    if mode not in [BLACKLIST_MODE, WHITELIST_MODE]:
        return jsonify(error(f"Invalid mode: {mode}. Must be '{BLACKLIST_MODE}' or '{WHITELIST_MODE}'"))
        
    return jsonify(set_rule_mode(mode))

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