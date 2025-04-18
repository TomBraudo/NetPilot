from utils.ssh_client import ssh_manager
from utils.response_helpers import success, error
from services.block_ip import get_blocked_devices, unblock_mac_address
from services.limit_bandwidth import remove_bandwidth_limit
from db.device_repository import get_all_devices
from db.device_groups_repository import get_rules_for_device

def reset_all_tc_rules():
    """
    Remove all traffic control (bandwidth limit) rules from the router.
    """
    # Get all interfaces first
    iface_cmd = "ip link show | grep -v '@' | grep -v 'lo:' | awk -F': ' '{print $2}' | cut -d'@' -f1"
    interfaces_output, iface_error = ssh_manager.execute_command(iface_cmd)
    
    if iface_error:
        return error(f"Failed to fetch network interfaces: {iface_error}")
        
    # For each interface, remove all tc rules
    for interface in interfaces_output.strip().split('\n'):
        if not interface.strip():
            continue
            
        # Remove all qdisc rules
        ssh_manager.execute_command(f"tc qdisc del dev {interface} root 2>/dev/null")
        
    return success("All bandwidth limits removed")

def unblock_all_devices():
    """
    Unblock all currently blocked devices.
    """
    blocked_response = get_blocked_devices()
    
    if "error" in blocked_response:
        return blocked_response
        
    blocked_devices = blocked_response.get("data", [])
    unblocked_count = 0
    
    for device in blocked_devices:
        if device["ip"] != "Unknown":
            unblock_mac_address(device["ip"])
            unblocked_count += 1
            
    # Also reset the OpenWrt blocklist settings
    ssh_manager.execute_command("uci set wireless.@wifi-iface[1].macfilter='disable'")
    ssh_manager.execute_command("uci delete wireless.@wifi-iface[1].maclist")
    ssh_manager.execute_command("uci commit wireless")
    ssh_manager.execute_command("wifi")
    
    return success(f"Unblocked {unblocked_count} devices")

def reset_all_rules():
    """
    Reset all network rules including bandwidth limits and blocks.
    """
    # Reset bandwidth limits
    tc_result = reset_all_tc_rules()
    
    # Unblock devices
    unblock_result = unblock_all_devices()
    
    # Get all rules from database to report what was cleared
    all_devices = get_all_devices()
    
    return success(
        message="All network rules have been reset successfully",
        data={
            "bandwidth_reset": tc_result.get("message", "Failed"),
            "unblock_reset": unblock_result.get("message", "Failed"),
            "affected_devices": len(all_devices)
        }
    )