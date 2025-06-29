from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
from services.router_state_manager import get_router_state, write_router_state
from services.device_rule_service import (
    add_device_to_blacklist_rules,
    remove_device_from_blacklist_rules,
    rebuild_blacklist_chain
)
from services.mode_activation_service import (
    activate_blacklist_mode_rules,
    deactivate_blacklist_mode_rules
)

logger = get_logger('services.blacklist')
router_connection_manager = RouterConnectionManager()

def get_blacklist():
    """Gets the list of blacklisted devices."""
    state = get_router_state()
    return state['devices']['blacklist'], None

def add_device_to_blacklist(mac):
    """Adds a device to the blacklist and updates iptables rules."""
    if not mac: 
        return None, "MAC address is required."

    state = get_router_state()
    if mac in state['devices']['blacklist']:
        return f"Device {mac} already in blacklist.", None
        
    # First update the state file
    state['devices']['blacklist'].append(mac)
    if write_router_state(state):
        # Then add the iptables rule
        rule_success, rule_error = add_device_to_blacklist_rules(mac)
        if not rule_success:
            logger.error(f"Failed to add iptables rule for {mac}: {rule_error}")
            # Note: State is already updated, but rule failed. This is logged but not rolled back.
        
        logger.info(f"Device {mac} added to blacklist with iptables rule")
        return f"Device {mac} added to blacklist.", None
    return None, "Failed to update state file on router."

def remove_device_from_blacklist(mac):
    """Removes a device from the blacklist and updates iptables rules."""
    if not mac: 
        return None, "MAC address is required."

    state = get_router_state()
    if mac not in state['devices']['blacklist']:
        return f"Device {mac} not in blacklist.", None

    # First remove from state  
    state['devices']['blacklist'].remove(mac)
    if write_router_state(state):
        # Then remove the iptables rule
        rule_success, rule_error = remove_device_from_blacklist_rules(mac)
        if not rule_success:
            logger.error(f"Failed to remove iptables rule for {mac}: {rule_error}")
            # Note: State is already updated. Rule removal failure is logged but not considered fatal.
        
        logger.info(f"Device {mac} removed from blacklist with iptables rule cleanup")
        return f"Device {mac} removed from blacklist.", None
    return None, "Failed to update state file on router."

def activate_blacklist_mode():
    """Activates blacklist mode using fast iptables chain toggling."""
    state = get_router_state()
    if state['active_mode'] == 'blacklist':
        return "Blacklist mode is already active.", None

    state['active_mode'] = 'blacklist'
    if write_router_state(state):
        # Activate blacklist mode with iptables jump commands
        rule_success, rule_error = activate_blacklist_mode_rules()
        if not rule_success:
            logger.error(f"Failed to activate blacklist mode rules: {rule_error}")
            # Rollback state change
            state['active_mode'] = 'none'
            write_router_state(state)
            return None, f"Failed to activate blacklist mode: {rule_error}"
        
        logger.info("Blacklist mode activated successfully with fast iptables toggling")
        return "Blacklist mode activated.", None
    return None, "Failed to update state file on router."

def deactivate_blacklist_mode():
    """Deactivates blacklist mode using fast iptables chain toggling."""
    state = get_router_state()
    if state['active_mode'] == 'none':
        return "Modes are already inactive.", None
        
    state['active_mode'] = 'none'
    if write_router_state(state):
        # Deactivate blacklist mode by removing iptables jump commands
        rule_success, rule_error = deactivate_blacklist_mode_rules()
        if not rule_success:
            logger.error(f"Failed to deactivate blacklist mode rules: {rule_error}")
            # Note: State is already updated to 'none', which is the desired end state
            # We log the error but don't consider it fatal since the intent is to disable
        
        logger.info("Blacklist mode deactivated successfully")
        return "Blacklist mode deactivated.", None
    return None, "Failed to update state file on router."

def set_blacklist_limit_rate(rate):
    """Sets the blacklist limited rate in Mbps."""
    state = get_router_state()
    try:
        # Validate rate is a positive number
        mbps = float(rate)
        if mbps <= 0:
            raise ValueError("Rate must be positive")
        formatted_rate = f"{mbps}mbit"
    except (ValueError, TypeError):
        return None, "Rate must be a positive number (Mbps)"

    state['rates']['blacklist_limited'] = formatted_rate

    if write_router_state(state):
        # Update infrastructure rates dynamically
        from services.router_setup_service import update_infrastructure_rates
        rate_success, rate_error = update_infrastructure_rates(limited_rate=formatted_rate)
        if not rate_success:
            logger.warning(f"Failed to update infrastructure rates: {rate_error}")
            # Rate is saved in state but infrastructure update failed - not fatal
        
        logger.info(f"Blacklist limited rate set to {formatted_rate} and infrastructure updated")
        return {"rate_mbps": rate}, None
    return None, "Failed to update state file on router." 