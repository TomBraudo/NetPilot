from flask import Blueprint, request, jsonify
from services.admin_protection import register_admin_device, get_admin_device_mac, ensure_admin_device_protected
from utils.response_helpers import success, error
from utils.ssh_client import ssh_manager

admin_bp = Blueprint('admin', __name__)

'''
    API endpoint to register the current device as admin device
'''
@admin_bp.route("/api/admin/register", methods=["POST"])
def register_admin_endpoint():
    # Get client IP from request
    client_ip = request.remote_addr
    
    # Register this device as admin
    result = register_admin_device(ip_address=client_ip)
    return jsonify(result)

'''
    API endpoint to get admin device info
'''
@admin_bp.route("/api/admin/status", methods=["GET"])
def admin_status_endpoint():
    admin_mac = get_admin_device_mac()
    
    if not admin_mac:
        return jsonify({"status": "no_admin", "message": "No admin device registered"})
        
    # Ensure admin device is protected
    ensure_admin_device_protected(admin_mac)
    
    return jsonify(success(data={"admin_mac": admin_mac}))

@admin_bp.route("/api/admin/emergency_reset", methods=["POST"])
def emergency_reset_endpoint():
    """
    Emergency endpoint to reset all filtering.
    """
    try:
        # Reset wireless filtering
        reset_cmds = [
            # Reset wireless
            "for iface in $(uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1); do "
            "uci set wireless.$iface.macfilter='disable'; "
            "uci delete wireless.$iface.maclist; done",
            
            # Commit wireless changes
            "uci commit wireless",
            
            # Reset firewall
            "iptables -F FORWARD",
            "iptables -P FORWARD ACCEPT",
            
            # Apply changes
            "wifi reload"
        ]
        
        for cmd in reset_cmds:
            ssh_manager.execute_command(cmd)
            
        # Reset rule mode to blacklist
        from services.rule_mode import set_rule_mode, BLACKLIST_MODE
        set_rule_mode(BLACKLIST_MODE)
        
        return jsonify(success("All filtering reset. System in blacklist mode with no rules."))
    except Exception as e:
        return jsonify(error(f"Emergency reset failed: {str(e)}")) 