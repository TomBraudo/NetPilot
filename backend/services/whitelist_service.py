from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
from services.router_state_manager import get_router_state, write_router_state
from .router_setup_service import NFT_TABLE_NAME, WHITELIST_DEVICES_CHAIN, WHITELIST_LIMIT_CHAIN, GATE_CHAIN, LAN_INTERFACE

logger = get_logger('services.whitelist')
router_connection_manager = RouterConnectionManager()

def _execute_nft_command(command: str):
    """Helper to execute nft commands."""
    _, err = router_connection_manager.execute(f"nft {command}")
    if err and "Error:" in err:
        logger.error(f"nft command failed: {err}")
        # Even if it fails, we don't block the state change.
        # The state file is the source of truth.

def get_whitelist():
    """Gets the list of whitelisted devices."""
    state = get_router_state()
    return state['devices']['whitelist'], None

def add_device_to_whitelist(mac):
    """Adds a device to the nftables whitelist devices chain."""
    if not mac: return None, "MAC address is required."

    state = get_router_state()
    if mac in state['devices']['whitelist']:
        return f"Device {mac} already in whitelist.", None
        
    state['devices']['whitelist'].append(mac)
    if write_router_state(state):
        # Ensure any residual fwmark is cleared **before** accepting the packet
        # so the TC filters don't treat whitelisted traffic as limited.
        # Using meta mark set 0 makes the packet unmarked, then accept.
        _execute_nft_command(
            f"add rule inet {NFT_TABLE_NAME} {WHITELIST_DEVICES_CHAIN} ether saddr {mac} meta mark set 0 accept"
        )
        return f"Device {mac} added to whitelist.", None
    return None, "Failed to update state file on router."

def remove_device_from_whitelist(mac):
    """
    Removes a device from the nftables whitelist. It finds the handle for the
    rule and deletes it.
    """
    if not mac: return None, "MAC address is required."

    state = get_router_state()
    if mac not in state['devices']['whitelist']:
        return f"Device {mac} not in whitelist.", None

    state['devices']['whitelist'].remove(mac)
    if write_router_state(state):
        # To delete a rule, we need its handle. We can get this by parsing the output.
        # This is more complex, a simpler approach for now is to just flush and re-add.
        # For a truly robust solution, parsing the handle is best.
        # Let's try a simpler, idempotent flush and rebuild approach first.
        _rebuild_whitelist_rules(state['devices']['whitelist'])
        return f"Device {mac} removed from whitelist.", None
    return None, "Failed to update state file on router."

def _rebuild_whitelist_rules(mac_list):
    """Flushes the whitelist chain and re-adds all devices from the list."""
    logger.debug("Rebuilding whitelist nft rules...")
    _execute_nft_command(f"flush chain inet {NFT_TABLE_NAME} {WHITELIST_DEVICES_CHAIN}")
    for mac in mac_list:
        _execute_nft_command(
            f"add rule inet {NFT_TABLE_NAME} {WHITELIST_DEVICES_CHAIN} ether saddr {mac} meta mark set 0 accept"
        )

def activate_whitelist_mode():
    """Activates whitelist mode by adding jumps from the main gate to the service chains."""
    state = get_router_state()
    if state['active_mode'] == 'whitelist':
        return "Whitelist mode is already active.", None

    state['active_mode'] = 'whitelist'
    if write_router_state(state):
        _execute_nft_command(f"flush chain inet {NFT_TABLE_NAME} {GATE_CHAIN}")
        _execute_nft_command(f"add rule inet {NFT_TABLE_NAME} {GATE_CHAIN} jump {WHITELIST_DEVICES_CHAIN}")
        _execute_nft_command(f"add rule inet {NFT_TABLE_NAME} {GATE_CHAIN} jump {WHITELIST_LIMIT_CHAIN}")
        return "Whitelist mode activated.", None
    return None, "Failed to update state file on router."

def deactivate_whitelist_mode():
    """Deactivates any active mode by clearing the central gate."""
    state = get_router_state()
    if state['active_mode'] == 'none':
        return "Modes are already inactive.", None
        
    state['active_mode'] = 'none'
    if write_router_state(state):
        _execute_nft_command(f"flush chain inet {NFT_TABLE_NAME} {GATE_CHAIN}")
        return "Whitelist mode deactivated.", None
    return None, "Failed to update state file on router."

def _format_mbit(value):
    """Return a tc-compatible mbit string from numeric input."""
    try:
        # Allow float or int
        mbps = float(value)
        if mbps <= 0:
            raise ValueError
        # Remove trailing .0 for ints
        if mbps.is_integer():
            mbps = int(mbps)
        return f"{mbps}mbit"
    except (ValueError, TypeError):
        raise ValueError("Rate must be a positive number (Mbps)")

def set_whitelist_limit_rate(rate):
    """Sets the whitelist limited rate in Mbps (numeric)."""
    state = get_router_state()
    try:
        formatted_rate = _format_mbit(rate)
    except ValueError as e:
        return None, str(e)

    state['rates']['whitelist_limited'] = formatted_rate

    if write_router_state(state):
        # Always update the TC class regardless of whether mode is active
        # This ensures the rate is properly set for when the mode gets activated
        router_connection_manager.execute(f"tc class change dev {LAN_INTERFACE} parent 1: classid 1:12 htb rate {formatted_rate}")
        return {"rate_mbps": rate}, None
    return None, "Failed to update state file on router."

def set_whitelist_full_rate(rate):
    """Sets the whitelist full rate in Mbps (numeric)."""
    state = get_router_state()
    try:
        formatted_rate = _format_mbit(rate)
    except ValueError as e:
        return None, str(e)

    state['rates']['whitelist_full'] = formatted_rate

    if write_router_state(state):
        # Always update the TC class regardless of whether mode is active
        router_connection_manager.execute(f"tc class change dev {LAN_INTERFACE} parent 1: classid 1:11 htb rate {formatted_rate}")
        return {"rate_mbps": rate}, None
    return None, "Failed to update state file on router." 