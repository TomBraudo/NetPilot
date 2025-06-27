from utils.logging_config import get_logger
from services.bandwidth_mode import get_current_mode_value, set_current_mode_value
from services.reset_rules import reset_all_tc_rules
from managers.router_connection_manager import RouterConnectionManager

logger = get_logger('services.whitelist')
router_connection_manager = RouterConnectionManager()

# Constants for iptables and tc
WHITELIST_CHAIN = "NETPILOT_WHITELIST"
WHITELIST_LIMITED_MARK = "30" # Mark for traffic to be limited
FULL_RATE_CLASSID = "1:11"
LIMITED_RATE_CLASSID = "1:12"

def _execute_command(command, timeout=15):
    """Executes a command on the router and logs specific, non-critical errors."""
    # Using a shorter timeout for these critical commands to prevent long hangs.
    _, err = router_connection_manager.execute(command, timeout=timeout)
    if err and "File exists" not in err and "No such file or directory" not in err and "does not exist" not in err:
        logger.error(f"Command '{command}' failed with error: {err}")
        return False # Indicate failure
    return True

def _get_lan_interface():
    """Dynamically finds the LAN bridge interface, defaulting to 'br-lan'."""
    # The 'br-lan' interface is typically the master bridge for all LAN and WLAN traffic.
    # Applying TC rules here is the correct way to manage all connected device bandwidth.
    iface_cmd = "ip -o link show | grep -o 'br-lan' | head -n 1"
    interface, err = router_connection_manager.execute(iface_cmd)
    if err or not interface.strip():
        logger.warning("Could not dynamically find 'br-lan' interface, falling back to default 'br-lan'.")
        return "br-lan"
    found_iface = interface.strip()
    logger.info(f"Found LAN interface: {found_iface}")
    return found_iface

def _ensure_whitelist_infrastructure():
    """
    Builds the necessary infrastructure for whitelist mode in a fail-safe way.
    Default traffic is at full speed.
    """
    logger.info("Ensuring whitelist infrastructure is in place.")
    interface = _get_lan_interface()
    
    limit_rate, err1 = get_whitelist_limit_rate()
    if err1 or not limit_rate:
        logger.warning(f"Could not get whitelist limit rate, falling back to 50mbit. Error: {err1}")
        limit_rate = "50mbit"

    full_rate, err2 = get_whitelist_full_rate()
    if err2 or not full_rate:
        logger.warning(f"Could not get whitelist full rate, falling back to 1000mbit. Error: {err2}")
        full_rate = "1000mbit"

    # Fail-safe: Default class is FULL_RATE_CLASSID (11)
    if not _execute_command(f"tc qdisc add dev {interface} root handle 1: htb default {FULL_RATE_CLASSID.split(':')[1]}"): return False
    if not _execute_command(f"tc class add dev {interface} parent 1: classid {FULL_RATE_CLASSID} htb rate {full_rate}"): return False
    if not _execute_command(f"tc class add dev {interface} parent 1: classid {LIMITED_RATE_CLASSID} htb rate {limit_rate}"): return False
    
    # Filter to slow down traffic marked for limitation
    if not _execute_command(f"tc filter add dev {interface} parent 1: protocol ip prio 2 handle {WHITELIST_LIMITED_MARK} fw flowid {LIMITED_RATE_CLASSID}"): return False
    
    # Create the chain for our rules
    if not _execute_command(f"iptables -t mangle -N {WHITELIST_CHAIN}"): return False
    
    # Rule 1: Mark all traffic for limitation.
    if not _execute_command(f"iptables -t mangle -A {WHITELIST_CHAIN} -j MARK --set-mark {WHITELIST_LIMITED_MARK}"): return False
    
    logger.info("Whitelist infrastructure built successfully.")
    return True

def add_device_to_whitelist(mac):
    """Adds a device's MAC to the whitelist, exempting it from limitation."""
    if not mac:
        return None, "MAC address is required."
    
    logger.info(f"Adding MAC {mac} to the {WHITELIST_CHAIN} chain to exempt it from speed limits.")
    # This rule is inserted at the top of the chain. If the MAC matches, it returns to the calling chain,
    # skipping the general MARK rule that would have slowed it down.
    command = f"iptables -t mangle -I {WHITELIST_CHAIN} 1 -m mac --mac-source {mac} -j RETURN"
    if not _execute_command(command):
        return None, f"Failed to add MAC {mac} to whitelist chain."

    return f"Device {mac} added to whitelist ruleset and exempted from limits.", None

def remove_device_from_whitelist(mac):
    """Removes a device's MAC from the whitelist exemption list."""
    if not mac:
        return None, "MAC address is required."
        
    logger.info(f"Removing MAC {mac} exemption from the {WHITELIST_CHAIN} chain.")
    command = f"iptables -t mangle -D {WHITELIST_CHAIN} -m mac --mac-source {mac} -j RETURN"
    _execute_command(command) # Try to remove, don't worry if it fails (e.g., already gone)
    
    return f"Device {mac} exemption removed from whitelist ruleset.", None

def activate_whitelist_mode():
    """
    Activates whitelist mode. This is now an atomic operation.
    """
    logger.info("Attempting to activate whitelist mode...")
    # 1. Always start from a clean state to prevent rule conflicts.
    deactivate_whitelist_mode()
    
    # 2. Build the new infrastructure.
    if not _ensure_whitelist_infrastructure():
        logger.error("Failed to build whitelist infrastructure. Aborting activation and cleaning up.")
        deactivate_whitelist_mode()
        return None, "Failed to build whitelist infrastructure. All rules have been cleared."

    # 3. Atomically activate the new rules by adding the jump to the chain.
    logger.info("Activating whitelist mode by adding jump rule.")
    command = f"iptables -t mangle -I PREROUTING 1 -j {WHITELIST_CHAIN}"
    if not _execute_command(command):
        logger.error("Failed to add jump rule to activate whitelist. Cleaning up.")
        deactivate_whitelist_mode()
        return None, "Failed to activate whitelist mode. All rules have been cleared."

    set_current_mode_value('whitelist')
    logger.info("Whitelist mode activated successfully.")
    return "Whitelist mode activated.", None

def deactivate_whitelist_mode():
    """
    Deactivates whitelist mode by removing the jump rule and all associated tc and iptables rules.
    """
    logger.info("Deactivating whitelist mode and cleaning up all related rules.")
    
    # Detach the main rule from the PREROUTING chain
    detach_cmd = f"iptables -t mangle -D PREROUTING -j {WHITELIST_CHAIN}"
    _execute_command(detach_cmd)

    # Flush the custom chain to remove all rules (e.g., exemptions, marks)
    flush_cmd = f"iptables -t mangle -F {WHITELIST_CHAIN}"
    _execute_command(flush_cmd)
    
    # Delete the custom chain itself
    delete_chain_cmd = f"iptables -t mangle -X {WHITELIST_CHAIN}"
    _execute_command(delete_chain_cmd)

    # Reset all traffic control rules completely to ensure a clean state
    reset_all_tc_rules()
    
    set_current_mode_value('none')
    logger.info("Whitelist mode deactivated and all TC/iptables rules cleared.")
    return "Whitelist mode deactivated. All active firewall and traffic control rules have been cleared.", None

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