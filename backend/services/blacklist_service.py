from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
from services.router_state_manager import get_router_state, write_router_state
from .router_setup_service import NFT_TABLE_NAME, BLACKLIST_CHAIN, GATE_CHAIN, LAN_INTERFACE

logger = get_logger('services.blacklist')
router_connection_manager = RouterConnectionManager()

# Constants for iptables and tc
BLACKLIST_MARK = "0xa" # Mark for traffic to be limited
LIMITED_CLASSID = "1:12"

def _execute_nft_command(command: str):
    """Helper to execute nft commands."""
    _, err = router_connection_manager.execute(f"nft {command}")
    if err and "Error:" in err:
        logger.error(f"nft command failed: {err}")

def get_blacklist():
    """Gets the list of blacklisted devices."""
    state = get_router_state()
    return state['devices']['blacklist'], None

def add_device_to_blacklist(mac):
    """Adds a device to the nftables blacklist chain."""
    if not mac: return None, "MAC address is required."

    state = get_router_state()
    if mac in state['devices']['blacklist']:
        return f"Device {mac} already in blacklist.", None
        
    state['devices']['blacklist'].append(mac)
    if write_router_state(state):
        _execute_nft_command(f"add rule inet {NFT_TABLE_NAME} {BLACKLIST_CHAIN} ether saddr {mac} meta mark set {BLACKLIST_MARK}")
        return f"Device {mac} added to blacklist.", None
    return None, "Failed to update state file on router."

def remove_device_from_blacklist(mac):
    """Removes a device from the nftables blacklist."""
    if not mac: return None, "MAC address is required."

    state = get_router_state()
    if mac not in state['devices']['blacklist']:
        return f"Device {mac} not in blacklist.", None

    state['devices']['blacklist'].remove(mac)
    if write_router_state(state):
        _rebuild_blacklist_rules(state['devices']['blacklist'])
        return f"Device {mac} removed from blacklist.", None
    return None, "Failed to update state file on router."

def _rebuild_blacklist_rules(mac_list):
    """Flushes the blacklist chain and re-adds all devices from the list."""
    logger.debug("Rebuilding blacklist nft rules...")
    _execute_nft_command(f"flush chain inet {NFT_TABLE_NAME} {BLACKLIST_CHAIN}")
    for mac in mac_list:
        _execute_nft_command(f"add rule inet {NFT_TABLE_NAME} {BLACKLIST_CHAIN} ether saddr {mac} meta mark set {BLACKLIST_MARK}")

def activate_blacklist_mode():
    """Activates blacklist mode by adding a jump from the main gate to the blacklist chain."""
    state = get_router_state()
    if state['active_mode'] == 'blacklist':
        return "Blacklist mode is already active.", None

    state['active_mode'] = 'blacklist'
    if write_router_state(state):
        _execute_nft_command(f"flush chain inet {NFT_TABLE_NAME} {GATE_CHAIN}")
        _execute_nft_command(f"add rule inet {NFT_TABLE_NAME} {GATE_CHAIN} jump {BLACKLIST_CHAIN}")
        return "Blacklist mode activated.", None
    return None, "Failed to update state file on router."

def deactivate_blacklist_mode():
    """Deactivates any active mode by clearing the central gate."""
    state = get_router_state()
    if state['active_mode'] == 'none':
        return "Modes are already inactive.", None
        
    state['active_mode'] = 'none'
    if write_router_state(state):
        _execute_nft_command(f"flush chain inet {NFT_TABLE_NAME} {GATE_CHAIN}")
        return "Blacklist mode deactivated.", None
    return None, "Failed to update state file on router."

def _format_mbit(value):
    try:
        mbps = float(value)
        if mbps <= 0:
            raise ValueError
        if mbps.is_integer():
            mbps = int(mbps)
        return f"{mbps}mbit"
    except (ValueError, TypeError):
        raise ValueError("Rate must be a positive number (Mbps)")

def set_blacklist_limit_rate(rate):
    """Sets the blacklist limited rate in Mbps (numeric)."""
    state = get_router_state()
    try:
        formatted_rate = _format_mbit(rate)
    except ValueError as e:
        return None, str(e)

    state['rates']['blacklist_limited'] = formatted_rate

    if write_router_state(state):
        # Always update the TC class regardless of whether mode is active
        router_connection_manager.execute(
            f"tc class change dev {LAN_INTERFACE} parent 1: classid 1:12 htb rate {formatted_rate}"
        )
        return {"rate_mbps": rate}, None
    return None, "Failed to update state file on router." 