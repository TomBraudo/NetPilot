from utils.logging_config import get_logger
from utils.ssh_client import ssh_manager
from utils.response_helpers import success

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

def reset_all_wireless_blocking():
    """
    Reset all wireless device blocking (MAC filtering).
    """
    try:
        # Reset the OpenWrt blocklist settings
        ssh_manager.execute_command("uci set wireless.@wifi-iface[1].macfilter='disable'")
        ssh_manager.execute_command("uci delete wireless.@wifi-iface[1].maclist")
        ssh_manager.execute_command("uci commit wireless")
        ssh_manager.execute_command("wifi")
        
        return success(message="All wireless blocking rules reset")
    except Exception as e:
        logger.error(f"Error resetting wireless blocking: {str(e)}", exc_info=True)
        raise

def reset_all_rules():
    """
    Reset all network rules including bandwidth limits and wireless blocks.
    """
    try:
        # Reset bandwidth limits
        tc_result = reset_all_tc_rules()
        
        # Reset wireless blocking
        wireless_result = reset_all_wireless_blocking()
        
        return success(
            message="All network rules have been reset successfully",
            data={
                "bandwidth_reset": tc_result.get("message", "Failed"),
                "wireless_reset": wireless_result.get("message", "Failed")
            }
        )
    except Exception as e:
        logger.error(f"Error resetting network rules: {str(e)}", exc_info=True)
        raise