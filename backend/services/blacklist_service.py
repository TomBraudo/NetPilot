from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
from services.router_state_manager import get_router_state, write_router_state
from services.device_rule_service import (
    add_device_to_blacklist_rules,
    remove_device_from_blacklist_rules,
    rebuild_blacklist_chain,
    _validate_ip_address
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

def add_device_to_blacklist(ip):
    """Adds a device to the blacklist and updates iptables rules."""
    if not ip: 
        return None, "IP address is required."

    # Validate IP format
    if not _validate_ip_address(ip):
        return None, "Invalid IP address format."

    state = get_router_state()
    if ip in state['devices']['blacklist']:
        return f"Device {ip} already in blacklist.", None
        
    # First update the state file
    state['devices']['blacklist'].append(ip)
    if write_router_state(state):
        # Then add the iptables rule
        rule_success, rule_error = add_device_to_blacklist_rules(ip)
        if not rule_success:
            logger.error(f"Failed to add iptables rule for {ip}: {rule_error}")
            # Note: State is already updated, but rule failed. This is logged but not rolled back.
        
        logger.info(f"Device {ip} added to blacklist with iptables rule")
        return f"Device {ip} added to blacklist.", None
    return None, "Failed to update state file on router."

def remove_device_from_blacklist(ip):
    """Removes a device from the blacklist and updates iptables rules."""
    if not ip: 
        return None, "IP address is required."

    # Validate IP format
    if not _validate_ip_address(ip):
        return None, "Invalid IP address format."

    state = get_router_state()
    if ip not in state['devices']['blacklist']:
        return f"Device {ip} not in blacklist.", None

    # First remove the iptables rules
    # We do this first because if it fails, we want to know before changing state
    rule_success, rule_error = remove_device_from_blacklist_rules(ip)
    
    if not rule_success:
        logger.error(f"Failed to remove iptables rules for {ip}: {rule_error}")
        # Don't proceed with state update if critical rule removal failed
        return None, f"Failed to remove blacklist rules: {rule_error}"
    
    # If rules were removed successfully, update state
    state['devices']['blacklist'].remove(ip)
    if write_router_state(state):
        logger.info(f"Device {ip} removed from blacklist with iptables rule cleanup")
        return f"Device {ip} removed from blacklist.", None
    else:
        # Rules removed but state update failed - inconsistent state
        logger.error(f"Rules removed but failed to update state file for {ip}")
        return None, "Failed to update state file on router."

def activate_blacklist_mode():
    """Activates blacklist mode using naive approach - complete teardown and rebuild."""
    state = get_router_state()
    if state['active_mode'] == 'blacklist':
        return "Blacklist mode is already active.", None

    state['active_mode'] = 'blacklist'
    if write_router_state(state):
        # Use naive approach: complete teardown and rebuild
        rule_success, rule_error = activate_blacklist_mode_rules()
        if not rule_success:
            logger.error(f"Failed to activate blacklist mode rules: {rule_error}")
            # Rollback state change
            state['active_mode'] = 'none'
            write_router_state(state)
            return None, f"Failed to activate blacklist mode: {rule_error}"
        
        logger.info("Blacklist mode activated successfully using naive approach")
        return "Blacklist mode activated.", None
    return None, "Failed to update state file on router."

def deactivate_blacklist_mode():
    """Deactivates blacklist mode using naive approach - complete teardown and rebuild."""
    state = get_router_state()
    if state['active_mode'] == 'none':
        return "Modes are already inactive.", None
        
    state['active_mode'] = 'none'
    if write_router_state(state):
        # Use naive approach: complete teardown and rebuild
        rule_success, rule_error = deactivate_blacklist_mode_rules()
        if not rule_success:
            logger.error(f"Failed to deactivate blacklist mode rules: {rule_error}")
            # Note: State is already updated to 'none', which is the desired end state
            # We log the error but don't consider it fatal since the intent is to disable
        
        logger.info("Blacklist mode deactivated successfully using naive approach")
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
        logger.info(f"Blacklist limited rate set to {formatted_rate} (will apply on next mode activation)")
        return {"rate_mbps": rate}, None
    return None, "Failed to update state file on router." 