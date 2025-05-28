from utils.logging_config import get_logger
from utils.ssh_client import ssh_manager
from utils.response_helpers import success
from services.block_ip import get_blocked_devices, unblock_device_by_ip
from db.device_repository import get_all_devices

logger = get_logger('services.reset_rules')

def reset_all_tc_rules():
    """
    Remove all traffic control (bandwidth limit) rules from the router.
    This is used when resetting blacklist/whitelist modes.
    """
    try:
        # Flush iptables mangle table first to remove any packet marks
        logger.info("Flushing iptables mangle table.")
        iptables_flush_output, iptables_flush_error = ssh_manager.execute_command("iptables -t mangle -F")
        if iptables_flush_error:
            # Log an error but proceed with trying to remove tc rules
            logger.error(f"Error flushing iptables mangle table: {iptables_flush_error}. Output: {iptables_flush_output}")
            # Depending on policy, you might choose to raise an exception here
            # raise Exception(f"Failed to flush iptables mangle table: {iptables_flush_error}")
        else:
            logger.info("Successfully flushed iptables mangle table.")

        # Get all interfaces first
        iface_cmd = "ip link show | grep -v '@' | grep -v 'lo:' | awk -F': ' '{print $2}' | cut -d'@' -f1"
        interfaces_output, iface_error = ssh_manager.execute_command(iface_cmd)
        
        if iface_error:
            raise Exception(f"Failed to fetch network interfaces: {iface_error}")
        
        # For each interface, remove all tc rules
        for interface in interfaces_output.strip().split('\n'):
            if not interface.strip():
                continue
            
            # Remove all qdisc rules. Capture stderr.
            cmd = f"tc qdisc del dev {interface} root"
            output, error = ssh_manager.execute_command(cmd) # error will now contain tc's stderr

            # Log the outcome, even if 'successful' due to no qdisc existing
            if error:
                # Log common 'Cannot find device' or 'RTNETLINK answers: No such file or directory' as info, others as error
                if "Cannot find device" in error or "No such file or directory" in error:
                    logger.info(f"Interface {interface} or qdisc not found (normal for reset): {error}")
                else:
                    logger.error(f"Error deleting qdisc on {interface}: {error}. Output: {output}")
                    # Optionally, re-raise an exception if a critical error occurs during reset
                    # raise Exception(f"Failed to delete qdisc on {interface}: {error}") 
            else:
                logger.info(f"Successfully deleted qdisc on {interface} or no qdisc was present. Output: {output}")
        
        return success(message="All traffic control rules removed (or attempted)")
    except Exception as e:
        logger.error(f"Error resetting traffic control rules: {str(e)}", exc_info=True)
        raise

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
            unblock_device_by_ip(device["ip"])
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
    try:
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
    except Exception as e:
        logger.error(f"Error resetting network rules: {str(e)}", exc_info=True)
        raise