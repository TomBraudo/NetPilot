from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager

logger = get_logger('services.reset_rules')
router_connection_manager = RouterConnectionManager()

def reset_all_rules():
    """
    Resets all firewall rules to a default state by removing all but the essential
    forwarding and system rules. Also clears any MAC-based blocklists.
    """
    try:
        get_rules_cmd = "uci show firewall | grep 'firewall.@rule' | sed 's/\\[\\([0-9]*\\)\\].*/\\1/' | sort -rn"
        rule_indices_str, err = router_connection_manager.execute(get_rules_cmd)

        if err:
            return None, f"Failed to retrieve firewall rules: {err}"

        delete_commands = []
        if rule_indices_str:
            indices = rule_indices_str.strip().split('\n')
            for index in indices:
                if int(index) > 5:
                    delete_commands.append(f"uci delete firewall.@rule[{index}]")

        clear_maclist_cmd = (
            "uci show wireless.@wifi-iface[0].maclist > /dev/null 2>&1 && "
            "uci set wireless.@wifi-iface[0].maclist='' && "
            "uci set wireless.@wifi-iface[0].macfilter='none'"
        )
        delete_commands.append(clear_maclist_cmd)

        delete_commands.append("uci commit firewall")
        delete_commands.append("uci commit wireless")
        delete_commands.append("/etc/init.d/firewall restart")
        delete_commands.append("wifi")

        full_command = " && ".join(delete_commands)
        _, final_err = router_connection_manager.execute(full_command)
        
        if final_err:
            if "uci: Entry not found" not in final_err:
                return None, f"An error occurred during reset: {final_err}"

        return "All firewall rules and MAC blocks have been reset.", None

    except RuntimeError as e:
        logger.error(f"Connection error resetting rules: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"An unexpected error occurred during rule reset: {str(e)}", exc_info=True)
        return None, "An unexpected error occurred during rule reset."

def reset_all_tc_rules():
    """
    Removes all traffic control (tc) qdiscs from the LAN interface, effectively
    resetting any bandwidth shaping rules.
    """
    try:
        # Find the LAN bridge interface
        iface_cmd = "ip -o link show | grep 'br-lan' | awk '{print $2}' | cut -d: -f1"
        interface, iface_err = router_connection_manager.execute(iface_cmd)
        if iface_err or not interface:
            interface = "br-lan"
            logger.warning("Could not dynamically find LAN bridge, falling back to br-lan.")
        
        interface = interface.strip()

        # Command to delete the root qdisc, which removes all child classes and filters
        cmd = f"tc qdisc del dev {interface} root"
        _, err = router_connection_manager.execute(cmd)

        # It's not an error if the qdisc doesn't exist (it may have been already cleared)
        if err and "Cannot find device" not in err and "No such file or directory" not in err:
            logger.error(f"Failed to delete tc qdisc on {interface}: {err}")
            return None, f"Failed to delete tc qdisc on {interface}: {err}"
        
        logger.info(f"Successfully cleared all TC rules on interface {interface}.")
        return f"Successfully cleared all TC rules on interface {interface}.", None

    except RuntimeError as e:
        logger.error(f"Connection error resetting TC rules: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"An unexpected error occurred during TC rule reset: {str(e)}", exc_info=True)
        return None, "An unexpected error occurred during TC rule reset."