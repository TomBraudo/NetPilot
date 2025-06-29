from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
from services.router_state_manager import get_router_state, write_router_state
from services.device_rule_service import (
    add_device_to_whitelist_rules, 
    remove_device_from_whitelist_rules,
    rebuild_whitelist_chain
)
from services.mode_activation_service import (
    activate_whitelist_mode_rules,
    deactivate_whitelist_mode_rules
)

logger = get_logger('services.whitelist')
router_connection_manager = RouterConnectionManager()

def get_whitelist():
    """Gets the list of whitelisted devices."""
    state = get_router_state()
    return state['devices']['whitelist'], None

def add_device_to_whitelist(mac):
    """Adds a device to the whitelist and updates iptables rules."""
    if not mac: 
        return None, "MAC address is required."

    state = get_router_state()
    if mac in state['devices']['whitelist']:
        return f"Device {mac} already in whitelist.", None
        
    # First update the state file
    state['devices']['whitelist'].append(mac)
    if write_router_state(state):
        # Then add the iptables rule
        rule_success, rule_error = add_device_to_whitelist_rules(mac)
        if not rule_success:
            logger.error(f"Failed to add iptables rule for {mac}: {rule_error}")
            # Note: State is already updated, but rule failed. This is logged but not rolled back.
            # The rule will be applied when the chain is rebuilt or mode is activated.
        
        logger.info(f"Device {mac} added to whitelist with iptables rule")
        return f"Device {mac} added to whitelist.", None
    return None, "Failed to update state file on router."

def remove_device_from_whitelist(mac):
    """Removes a device from the whitelist and updates iptables rules."""
    if not mac: 
        return None, "MAC address is required."

    state = get_router_state()
    if mac not in state['devices']['whitelist']:
        return f"Device {mac} not in whitelist.", None

    # First remove from state
    state['devices']['whitelist'].remove(mac)
    if write_router_state(state):
        # Then remove the iptables rule
        rule_success, rule_error = remove_device_from_whitelist_rules(mac)
        if not rule_success:
            logger.error(f"Failed to remove iptables rule for {mac}: {rule_error}")
            # Note: State is already updated. Rule removal failure is logged but not considered fatal.
        
        logger.info(f"Device {mac} removed from whitelist with iptables rule cleanup")
        return f"Device {mac} removed from whitelist.", None
    return None, "Failed to update state file on router."

def activate_whitelist_mode():
    """Activates whitelist mode using fast iptables chain toggling."""
    state = get_router_state()
    if state['active_mode'] == 'whitelist':
        return "Whitelist mode is already active.", None

    state['active_mode'] = 'whitelist'
    if write_router_state(state):
        # Activate whitelist mode with iptables jump commands
        rule_success, rule_error = activate_whitelist_mode_rules()
        if not rule_success:
            logger.error(f"Failed to activate whitelist mode rules: {rule_error}")
            # Rollback state change
            state['active_mode'] = 'none'
            write_router_state(state)
            return None, f"Failed to activate whitelist mode: {rule_error}"
        
        logger.info("Whitelist mode activated successfully with fast iptables toggling")
        return "Whitelist mode activated.", None
    return None, "Failed to update state file on router."

def deactivate_whitelist_mode():
    """Deactivates whitelist mode using fast iptables chain toggling."""
    state = get_router_state()
    if state['active_mode'] == 'none':
        return "Modes are already inactive.", None
        
    state['active_mode'] = 'none'
    if write_router_state(state):
        # Deactivate whitelist mode by removing iptables jump commands
        rule_success, rule_error = deactivate_whitelist_mode_rules()
        if not rule_success:
            logger.error(f"Failed to deactivate whitelist mode rules: {rule_error}")
            # Note: State is already updated to 'none', which is the desired end state
            # We log the error but don't consider it fatal since the intent is to disable
        
        logger.info("Whitelist mode deactivated successfully")
        return "Whitelist mode deactivated.", None
    return None, "Failed to update state file on router."

def set_whitelist_limit_rate(rate):
    """Sets the whitelist limited rate in Mbps."""
    state = get_router_state()
    try:
        mbps = float(rate)
        if mbps <= 0:
            raise ValueError("Rate must be positive")
        formatted_rate = f"{int(mbps) if mbps.is_integer() else mbps}mbit"
    except (ValueError, TypeError):
        return None, "Rate must be a positive number (Mbps)"

    state['rates']['whitelist_limited'] = formatted_rate

    if write_router_state(state):
        # Update infrastructure rates dynamically
        from services.router_setup_service import update_infrastructure_rates
        rate_success, rate_error = update_infrastructure_rates(limited_rate=formatted_rate)
        if not rate_success:
            logger.warning(f"Failed to update infrastructure rates: {rate_error}")
            # Rate is saved in state but infrastructure update failed - not fatal
        
        logger.info(f"Whitelist limited rate set to {formatted_rate} and infrastructure updated")
        return {"rate_mbps": rate}, None
    return None, "Failed to update state file on router."

def set_whitelist_full_rate(rate):
    """Sets the whitelist full rate in Mbps."""
    state = get_router_state()
    try:
        mbps = float(rate)
        if mbps <= 0:
            raise ValueError("Rate must be positive")
        formatted_rate = f"{int(mbps) if mbps.is_integer() else mbps}mbit"
    except (ValueError, TypeError):
        return None, "Rate must be a positive number (Mbps)"

    state['rates']['whitelist_full'] = formatted_rate

    if write_router_state(state):
        # Update infrastructure rates dynamically
        from services.router_setup_service import update_infrastructure_rates
        rate_success, rate_error = update_infrastructure_rates(unlimited_rate=formatted_rate)
        if not rate_success:
            logger.warning(f"Failed to update infrastructure rates: {rate_error}")
            # Rate is saved in state but infrastructure update failed - not fatal
        
        logger.info(f"Whitelist full rate set to {formatted_rate} and infrastructure updated")
        return {"rate_mbps": rate}, None
    return None, "Failed to update state file on router." 