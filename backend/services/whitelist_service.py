from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
from services.router_state_manager import get_router_state, write_router_state

logger = get_logger('services.whitelist')
router_connection_manager = RouterConnectionManager()

# Constants for iptables and tc
WHITELIST_CHAIN = "NETPILOT_WHITELIST"
WHITELIST_LIMITED_MARK = "30"
LIMITED_RATE_CLASSID = "1:12"
FULL_RATE_CLASSID = "1:11"

def _rebuild_whitelist_rules(conn, state):
    """Flushes and rebuilds whitelist iptables rules based on the provided state."""
    conn.exec_command("iptables -t mangle -F NETPILOT_WHITELIST")
    
    if state['active_mode'] == 'whitelist':
        conn.exec_command("iptables -t mangle -A NETPILOT_WHITELIST -j MARK --set-mark 30")
        for mac in state['devices']['whitelist']:
            conn.exec_command(f"iptables -t mangle -I NETPILOT_WHITELIST 1 -m mac --mac-source {mac} -j RETURN")
    logger.info("Whitelist rules rebuilt on router.")

def add_device_to_whitelist(mac):
    """Adds a device to the whitelist if it's not already there."""
    if not mac: return None, "MAC address is required."
    
    conn = router_connection_manager._get_current_connection()
    if not conn: return None, "No active router connection."

    state = get_router_state(conn)
    if mac in state['devices']['whitelist']:
        return f"Device {mac} already in whitelist.", None
        
    state['devices']['whitelist'].append(mac)
    if write_router_state(conn, state):
        _rebuild_whitelist_rules(conn, state)
        return f"Device {mac} added to whitelist.", None
    return None, "Failed to update state file on router."

def remove_device_from_whitelist(mac):
    """Removes a device from the whitelist if it exists."""
    if not mac: return None, "MAC address is required."
        
    conn = router_connection_manager._get_current_connection()
    if not conn: return None, "No active router connection."

    state = get_router_state(conn)
    if mac not in state['devices']['whitelist']:
        return f"Device {mac} not in whitelist.", None

    state['devices']['whitelist'].remove(mac)
    if write_router_state(conn, state):
        _rebuild_whitelist_rules(conn, state)
        return f"Device {mac} removed from whitelist.", None
    return None, "Failed to update state file on router."

def activate_whitelist_mode():
    """Activates whitelist mode if not already active."""
    conn = router_connection_manager._get_current_connection()
    if not conn: return None, "No active router connection."

    state = get_router_state(conn)
    if state['active_mode'] == 'whitelist':
        return "Whitelist mode is already active.", None

    state['active_mode'] = 'whitelist'
    if write_router_state(conn, state):
        # When activating, set TC rules to the specific rates for this mode
        rates = state['rates']['whitelist']
        conn.exec_command(f"tc class change dev br-lan parent 1: classid 1:11 htb rate {rates['full_rate']}")
        conn.exec_command(f"tc class change dev br-lan parent 1: classid 1:12 htb rate {rates['limited_rate']}")
        
        # Also clear the other list's rules for a clean state
        conn.exec_command("iptables -t mangle -F NETPILOT_BLACKLIST")
        _rebuild_whitelist_rules(conn, state)
        return "Whitelist mode activated.", None
    return None, "Failed to update state file on router."

def deactivate_whitelist_mode():
    """Deactivates any active mode."""
    conn = router_connection_manager._get_current_connection()
    if not conn: return None, "No active router connection."
    
    state = get_router_state(conn)
    if state['active_mode'] == 'none':
        return "Modes are already inactive.", None
        
    state['active_mode'] = 'none'
    if write_router_state(conn, state):
        _rebuild_whitelist_rules(conn, state) # This will just flush the rules
        return "Whitelist mode deactivated.", None
    return None, "Failed to update state file on router."

def set_whitelist_limit_rate(rate):
    """Sets the whitelist limited rate."""
    conn = router_connection_manager._get_current_connection()
    if not conn: return None, "No active router connection."

    state = get_router_state(conn)
    formatted_rate = f"{rate}kbit"
    state['rates']['whitelist']['limited_rate'] = formatted_rate
    
    if write_router_state(conn, state):
        # If whitelist mode is active, apply the change immediately
        if state['active_mode'] == 'whitelist':
            conn.exec_command(f"tc class change dev br-lan parent 1: classid 1:12 htb rate {formatted_rate}")
        return {"rate": formatted_rate}, None
    return None, "Failed to update state file on router."

def set_whitelist_full_rate(rate):
    """Sets the whitelist full rate."""
    conn = router_connection_manager._get_current_connection()
    if not conn: return None, "No active router connection."

    state = get_router_state(conn)
    formatted_rate = f"{rate}mbit"
    state['rates']['whitelist']['full_rate'] = formatted_rate
    
    if write_router_state(conn, state):
        # If whitelist mode is active, apply the change immediately
        if state['active_mode'] == 'whitelist':
            conn.exec_command(f"tc class change dev br-lan parent 1: classid 1:11 htb rate {formatted_rate}")
        return {"rate": formatted_rate}, None
    return None, "Failed to update state file on router."

def get_whitelist():
    """Gets the current whitelist state."""
    conn = router_connection_manager._get_current_connection()
    if not conn: return None, "No active router connection."

    state = get_router_state(conn)
    return {
        "devices": state['devices']['whitelist'],
        "active_mode": state['active_mode'],
        "rates": state['rates']['whitelist']
    }, None 