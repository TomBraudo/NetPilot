from utils.logging_config import get_logger
from utils.config_manager import config_manager
from services.bandwidth_mode import get_current_mode_value, set_current_mode_value
from managers.router_connection_manager import RouterConnectionManager

logger = get_logger('services.blacklist')
router_connection_manager = RouterConnectionManager()

# Constants for iptables and tc
BLACKLIST_CHAIN = "NETPILOT_BLACKLIST"
BLACKLIST_MARK = "10"

def _execute_command(command):
    """Executes a command on the router and logs errors."""
    _, err = router_connection_manager.execute(command)
    if err and "File exists" not in err and "No such file or directory" not in err and "does not exist" not in err:
        logger.error(f"Command '{command}' failed with error: {err}")
    return err is None or "File exists" in err

def _get_lan_interface():
    """Dynamically find the LAN bridge interface, defaulting to 'br-lan'."""
    iface_cmd = "ip -o link show | grep 'br-lan' | awk '{print $2}' | cut -d: -f1"
    interface, iface_err = router_connection_manager.execute(iface_cmd)
    if iface_err or not interface:
        logger.warning("Could not dynamically find LAN bridge, falling back to br-lan.")
        return "br-lan"
    return interface.strip()

def _ensure_blacklist_infrastructure():
    """
    Ensures that all necessary iptables chains and tc rules for the blacklist are present.
    This function is idempotent and can be safely called multiple times.
    """
    logger.info("Ensuring blacklist infrastructure is in place.")
    interface = _get_lan_interface()
    limit_rate, error = get_blacklist_limit_rate()
    if error:
        # This is an internal call, so we'll log the error and proceed with a default.
        # A more robust implementation might raise an exception.
        logger.error(f"Could not get limit rate, falling back to default. Error: {error}")
        limit_rate = "1kbit"
    
    # 1. Create a custom iptables chain for blacklist rules
    _execute_command(f"iptables -t mangle -N {BLACKLIST_CHAIN}")

    # 2. Setup tc qdisc, class, and filter
    _execute_command(f"tc qdisc add dev {interface} root handle 1: htb default 12")
    _execute_command(f"tc class add dev {interface} parent 1: classid 1:11 htb rate {limit_rate}")
    
    check_filter_cmd = f"tc filter show dev {interface} | grep 'handle {BLACKLIST_MARK}'"
    filter_exists, _ = router_connection_manager.execute(check_filter_cmd)
    if not filter_exists:
        _execute_command(f"tc filter add dev {interface} parent 1: protocol ip prio 1 handle {BLACKLIST_MARK} fw flowid 1:11")

    logger.info("Blacklist infrastructure verified.")
    return True

def add_device_to_blacklist(mac):
    """
    Adds a device's MAC address to the persistent blacklist iptables chain.
    """
    if not mac:
        return None, "MAC address is required."
    
    logger.info(f"Adding MAC {mac} to the {BLACKLIST_CHAIN} chain.")
    check_cmd = f"iptables -t mangle -C {BLACKLIST_CHAIN} -m mac --mac-source {mac} -j MARK --set-mark {BLACKLIST_MARK}"
    exists, _ = router_connection_manager.execute(check_cmd)
    
    if not exists:
        command = f"iptables -t mangle -A {BLACKLIST_CHAIN} -m mac --mac-source {mac} -j MARK --set-mark {BLACKLIST_MARK}"
        if not _execute_command(command):
            return None, f"Failed to add MAC {mac} to blacklist chain."

    return f"Device {mac} added to blacklist ruleset.", None

def remove_device_from_blacklist(mac):
    """
    Removes a device's MAC address from the persistent blacklist iptables chain.
    """
    if not mac:
        return None, "MAC address is required."
        
    logger.info(f"Removing MAC {mac} from the {BLACKLIST_CHAIN} chain.")
    command = f"iptables -t mangle -D {BLACKLIST_CHAIN} -m mac --mac-source {mac} -j MARK --set-mark {BLACKLIST_MARK}"
    _execute_command(command)
    
    return f"Device {mac} removed from blacklist ruleset.", None

def activate_blacklist_mode():
    """
    Activates the blacklist mode. If the whitelist is active, it will be
    deactivated first.
    """
    from services.whitelist_service import deactivate_whitelist_mode
    
    current_mode, _ = get_current_mode_value()
    if current_mode == 'whitelist':
        logger.info("Whitelist mode is active. Deactivating it before enabling blacklist mode.")
        deactivate_whitelist_mode()

    _ensure_blacklist_infrastructure()
    
    logger.info("Activating blacklist mode.")
    check_cmd = f"iptables -t mangle -C PREROUTING -j {BLACKLIST_CHAIN}"
    exists, _ = router_connection_manager.execute(check_cmd)

    if not exists:
        command = f"iptables -t mangle -I PREROUTING 1 -j {BLACKLIST_CHAIN}"
        if not _execute_command(command):
            return None, "Failed to activate blacklist mode by adding jump rule."
    
    set_current_mode_value('blacklist')
    return "Blacklist mode activated.", None

def deactivate_blacklist_mode():
    """
    Deactivates the blacklist mode by removing the jump rule from the PREROUTING chain.
    """
    logger.info("Deactivating blacklist mode.")
    command = f"iptables -t mangle -D PREROUTING -j {BLACKLIST_CHAIN}"
    _execute_command(command)
    
    set_current_mode_value('none')
    return "Blacklist mode deactivated.", None

# --- Configuration Management ---

def get_blacklist_limit_rate():
    """Get the current blacklist bandwidth limit rate from config."""
    try:
        config = config_manager.load_config('blacklist')
        return config.get('Limit_Rate', "1kbit"), None
    except Exception as e:
        return None, f"Could not load blacklist config: {e}"

def format_rate(rate):
    """Format rate value to include units if not present."""
    if isinstance(rate, (int, float)) and not isinstance(rate, bool):
        return f"{rate}kbit"
    if isinstance(rate, str) and rate.isnumeric():
        return f"{rate}kbit"
    return str(rate)

def set_blacklist_limit_rate(rate):
    """
    Set the blacklist bandwidth limit rate in config and updates the tc rule if it exists.
    """
    formatted_r = format_rate(rate)
    try:
        config = config_manager.load_config('blacklist')
        config['Limit_Rate'] = formatted_r
        config_manager.save_config('blacklist', config)
        logger.info(f"Updated blacklist limit rate to {formatted_r}")

        interface = _get_lan_interface()
        command = f"tc class change dev {interface} parent 1: classid 1:11 htb rate {formatted_r}"
        _execute_command(command)

        return {"rate": formatted_r}, None
    except Exception as e:
        logger.error(f"Error setting blacklist limit rate: {e}", exc_info=True)
        return None, "Failed to set blacklist limit rate." 