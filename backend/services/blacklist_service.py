from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
from services.router_state_manager import get_router_state, write_router_state

logger = get_logger('services.blacklist')
router_connection_manager = RouterConnectionManager()

# Constants for iptables and tc
BLACKLIST_CHAIN = "NETPILOT_BLACKLIST"
BLACKLIST_MARK = "10" # Mark for traffic to be limited
LIMITED_CLASSID = "1:12"

def _rebuild_blacklist_rules(conn, state):
    """Flushes and rebuilds blacklist iptables rules based on the provided state."""
    conn.exec_command("iptables -t mangle -F NETPILOT_BLACKLIST")

    if state['active_mode'] == 'blacklist':
        for mac in state['devices']['blacklist']:
            conn.exec_command(f"iptables -t mangle -A NETPILOT_BLACKLIST -m mac --mac-source {mac} -j MARK --set-mark 10")
    logger.info("Blacklist rules rebuilt on router.")

def add_device_to_blacklist(mac):
    """Adds a device to the blacklist if it's not already there."""
    if not mac: return None, "MAC address is required."

    conn = router_connection_manager._get_current_connection()
    if not conn: return None, "No active router connection."

    state = get_router_state(conn)
    if mac in state['devices']['blacklist']:
        return f"Device {mac} already in blacklist.", None
        
    state['devices']['blacklist'].append(mac)
    if write_router_state(conn, state):
        _rebuild_blacklist_rules(conn, state)
        return f"Device {mac} added to blacklist.", None
    return None, "Failed to update state file on router."

def remove_device_from_blacklist(mac):
    """Removes a device from the blacklist if it exists."""
    if not mac: return None, "MAC address is required."

    conn = router_connection_manager._get_current_connection()
    if not conn: return None, "No active router connection."

    state = get_router_state(conn)
    if mac not in state['devices']['blacklist']:
        return f"Device {mac} not in blacklist.", None

    state['devices']['blacklist'].remove(mac)
    if write_router_state(conn, state):
        _rebuild_blacklist_rules(conn, state)
        return f"Device {mac} removed from blacklist.", None
    return None, "Failed to update state file on router."

def activate_blacklist_mode():
    """Activates blacklist mode if not already active."""
    conn = router_connection_manager._get_current_connection()
    if not conn: return None, "No active router connection."

    state = get_router_state(conn)
    if state['active_mode'] == 'blacklist':
        return "Blacklist mode is already active.", None

    state['active_mode'] = 'blacklist'
    if write_router_state(conn, state):
        # When activating, set TC rules to the specific rate for this mode
        rate = state['rates']['blacklist']['limited_rate']
        
        # Set the limited class to the blacklist rate
        conn.exec_command(f"tc class change dev br-lan parent 1: classid 1:12 htb rate {rate}")
        # Set the full rate class to a high default, as it's not used by blacklist
        conn.exec_command(f"tc class change dev br-lan parent 1: classid 1:11 htb rate 1000mbit")
        
        # Also clear the other list's rules for a clean state
        conn.exec_command("iptables -t mangle -F NETPILOT_WHITELIST")
        _rebuild_blacklist_rules(conn, state)
        return "Blacklist mode activated.", None
    return None, "Failed to update state file on router."

def deactivate_blacklist_mode():
    """Deactivates any active mode."""
    conn = router_connection_manager._get_current_connection()
    if not conn: return None, "No active router connection."

    state = get_router_state(conn)
    if state['active_mode'] == 'none':
        return "Modes are already inactive.", None
        
    state['active_mode'] = 'none'
    if write_router_state(conn, state):
        _rebuild_blacklist_rules(conn, state) # This will just flush the rules
        return "Blacklist mode deactivated.", None
    return None, "Failed to update state file on router."

def set_blacklist_limit_rate(rate):
    """Sets the blacklist limited rate."""
    conn = router_connection_manager._get_current_connection()
    if not conn: return None, "No active router connection."

    state = get_router_state(conn)
    formatted_rate = f"{rate}kbit"
    state['rates']['blacklist']['limited_rate'] = formatted_rate
    
    if write_router_state(conn, state):
        # If blacklist mode is active, apply the change immediately
        if state['active_mode'] == 'blacklist':
            conn.exec_command(f"tc class change dev br-lan parent 1: classid 1:12 htb rate {formatted_rate}")
        return {"rate": formatted_rate}, None
    return None, "Failed to update state file on router." 