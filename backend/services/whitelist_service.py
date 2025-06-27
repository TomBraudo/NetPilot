from utils.logging_config import get_logger
from services.bandwidth_mode import get_current_mode_value, set_current_mode_value
from services.reset_rules import reset_all_tc_rules
from managers.router_connection_manager import RouterConnectionManager

logger = get_logger('services.whitelist')
router_connection_manager = RouterConnectionManager()

# Constants for iptables and tc
WHITELIST_CHAIN = "NETPILOT_WHITELIST"
WHITELIST_MARK = "20"
FULL_RATE_CLASSID = "1:11"
LIMITED_RATE_CLASSID = "1:12"

def _execute_command(command):
    """Executes a command on the router and logs specific, non-critical errors."""
    _, err = router_connection_manager.execute(command)
    if err and "File exists" not in err and "No such file or directory" not in err and "does not exist" not in err:
        logger.error(f"Command '{command}' failed with error: {err}")
    return err is None or "File exists" in err

def _get_lan_interface():
    """Dynamically finds the LAN bridge interface, defaulting to 'br-lan'."""
    iface_cmd = "ip -o link show | grep 'br-lan' | awk '{print $2}' | cut -d: -f1"
    interface, iface_err = router_connection_manager.execute(iface_cmd)
    if iface_err or not interface:
        logger.warning("Could not dynamically find LAN bridge, falling back to br-lan.")
        return "br-lan"
    return interface.strip()

def _ensure_whitelist_infrastructure():
    """
    Ensures that all necessary iptables chains and tc rules for the whitelist are present.
    This function is idempotent.
    """
    logger.info("Ensuring whitelist infrastructure is in place.")
    interface = _get_lan_interface()
    limit_rate, _ = get_whitelist_limit_rate()
    full_rate, _ = get_whitelist_full_rate()

    _execute_command(f"iptables -t mangle -N {WHITELIST_CHAIN}")
    _execute_command(f"tc qdisc add dev {interface} root handle 1: htb default {LIMITED_RATE_CLASSID.split(':')[1]}")
    _execute_command(f"tc class add dev {interface} parent 1: classid {FULL_RATE_CLASSID} htb rate {full_rate}")
    _execute_command(f"tc class add dev {interface} parent 1: classid {LIMITED_RATE_CLASSID} htb rate {limit_rate}")
    
    check_filter_cmd = f"tc filter show dev {interface} | grep 'handle {WHITELIST_MARK}'"
    filter_exists, _ = router_connection_manager.execute(check_filter_cmd)
    if not filter_exists:
        _execute_command(f"tc filter add dev {interface} parent 1: protocol ip prio 1 handle {WHITELIST_MARK} fw flowid {FULL_RATE_CLASSID}")

    logger.info("Whitelist infrastructure verified.")
    return True

def add_device_to_whitelist(mac):
    """Adds a device's MAC to the persistent whitelist iptables chain."""
    if not mac:
        return None, "MAC address is required."
    
    logger.info(f"Adding MAC {mac} to the {WHITELIST_CHAIN} chain.")
    check_cmd = f"iptables -t mangle -C {WHITELIST_CHAIN} -m mac --mac-source {mac} -j MARK --set-mark {WHITELIST_MARK}"
    exists, _ = router_connection_manager.execute(check_cmd)
    
    if not exists:
        command = f"iptables -t mangle -A {WHITELIST_CHAIN} -m mac --mac-source {mac} -j MARK --set-mark {WHITELIST_MARK}"
        if not _execute_command(command):
            return None, f"Failed to add MAC {mac} to whitelist chain."

    return f"Device {mac} added to whitelist ruleset.", None

def remove_device_from_whitelist(mac):
    """Removes a device's MAC from the persistent whitelist iptables chain."""
    if not mac:
        return None, "MAC address is required."
        
    logger.info(f"Removing MAC {mac} from the {WHITELIST_CHAIN} chain.")
    command = f"iptables -t mangle -D {WHITELIST_CHAIN} -m mac --mac-source {mac} -j MARK --set-mark {WHITELIST_MARK}"
    _execute_command(command)
    
    return f"Device {mac} removed from whitelist ruleset.", None

def activate_whitelist_mode():
    """
    Activates whitelist mode. If the blacklist is active, it will be deactivated first.
    """
    from services.blacklist_service import deactivate_blacklist_mode
    
    current_mode, _ = get_current_mode_value()
    if current_mode == 'blacklist':
        logger.info("Blacklist mode is active. Deactivating it before enabling whitelist mode.")
        deactivate_blacklist_mode()
        
    _ensure_whitelist_infrastructure()
    
    logger.info("Activating whitelist mode.")
    check_cmd = f"iptables -t mangle -C PREROUTING -j {WHITELIST_CHAIN}"
    exists, _ = router_connection_manager.execute(check_cmd)

    if not exists:
        command = f"iptables -t mangle -I PREROUTING 1 -j {WHITELIST_CHAIN}"
        if not _execute_command(command):
            return None, "Failed to activate whitelist mode by adding jump rule."
    
    set_current_mode_value('whitelist')
    return "Whitelist mode activated.", None

def deactivate_whitelist_mode():
    """
    Deactivates whitelist mode by removing the jump rule and resetting all tc rules.
    """
    logger.info("Deactivating whitelist mode.")
    detach_cmd = f"iptables -t mangle -D PREROUTING -j {WHITELIST_CHAIN}"
    _execute_command(detach_cmd)
    
    reset_all_tc_rules()
    
    set_current_mode_value('none')
    return "Whitelist mode deactivated and all TC rules cleared.", None

# --- Configuration Management ---

def _format_rate(rate, default_unit="mbit"):
    """Formats a rate value to include units if not present."""
    if isinstance(rate, (int, float)) and not isinstance(rate, bool):
        return f"{rate}{default_unit}"
    if isinstance(rate, str) and rate.isnumeric():
        return f"{rate}{default_unit}"
    return str(rate)

def get_whitelist_limit_rate():
    """Get the bandwidth rate for non-whitelisted devices."""
    try:
        config = config_manager.load_config('whitelist')
        return config.get('Limit_Rate', "1kbit"), None
    except Exception as e:
        return None, f"Could not load whitelist config: {e}"

def set_whitelist_limit_rate(rate):
    """Sets the rate for non-whitelisted devices and dynamically updates the tc rule."""
    formatted_r = _format_rate(rate, default_unit="kbit")
    try:
        config = config_manager.load_config('whitelist')
        config['Limit_Rate'] = formatted_r
        config_manager.save_config('whitelist', config)
        logger.info(f"Updated whitelist limit rate to {formatted_r}")

        interface = _get_lan_interface()
        command = f"tc class change dev {interface} parent 1: classid {LIMITED_RATE_CLASSID} htb rate {formatted_r}"
        _execute_command(command)
        
        return {"rate": formatted_r}, None
    except Exception as e:
        logger.error(f"Error setting whitelist limit rate: {e}", exc_info=True)
        return None, "Failed to set whitelist limit rate."

def get_whitelist_full_rate():
    """Get the bandwidth rate for whitelisted devices."""
    try:
        config = config_manager.load_config('whitelist')
        return config.get('Full_Rate', "1000mbit"), None
    except Exception as e:
        return None, f"Could not load whitelist config: {e}"

def set_whitelist_full_rate(rate):
    """Sets the rate for whitelisted devices and dynamically updates the tc rule."""
    formatted_r = _format_rate(rate, default_unit="mbit")
    try:
        config = config_manager.load_config('whitelist')
        config['Full_Rate'] = formatted_r
        config_manager.save_config('whitelist', config)
        logger.info(f"Updated whitelist full rate to {formatted_r}")

        interface = _get_lan_interface()
        command = f"tc class change dev {interface} parent 1: classid {FULL_RATE_CLASSID} htb rate {formatted_r}"
        _execute_command(command)
        
        return {"rate": formatted_r}, None
    except Exception as e:
        logger.error(f"Error setting whitelist full rate: {e}", exc_info=True)
        return None, "Failed to set whitelist full rate." 