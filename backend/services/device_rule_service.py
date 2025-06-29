from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
from services.router_state_manager import get_router_state

logger = get_logger('services.device_rule')
router_connection_manager = RouterConnectionManager()

def _execute_command(command: str):
    """
    Executes a command on the router with proper error handling.
    """
    _, err = router_connection_manager.execute(command, timeout=10)
    
    if err:
        error_lower = err.lower()
        # Check for idempotent operations that are safe to ignore
        if any(phrase in error_lower for phrase in [
            "file exists", "already exists", "cannot find", 
            "no such file", "chain already exists", "no chain/target/match"
        ]):
            logger.debug(f"Idempotent operation (safe to ignore): {command}")
            return True
            
        # Real errors that should fail the operation
        logger.error(f"Command failed: {command} - Error: {err}")
        return False
    
    logger.debug(f"Command successful: {command}")
    return True

def _convert_to_ip(device_identifier):
    """
    Converts MAC address to IP address or validates IP address.
    Returns the IP if successful, None if conversion fails.
    """
    # Check if it's already an IP address
    import re
    ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    
    if re.match(ip_pattern, device_identifier):
        return device_identifier
    
    # Check if it's a MAC address pattern
    mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    if re.match(mac_pattern, device_identifier):
        # For now, we'll use the MAC as-is since the existing API seems to use MAC addresses
        # In a real implementation, you might want to resolve MAC to IP via ARP table
        # For this phase, we'll treat it as MAC and use iptables MAC matching
        return None  # Indicates MAC address, needs different iptables syntax
    
    logger.error(f"Invalid device identifier format: {device_identifier}")
    return None

# === WHITELIST DEVICE MANAGEMENT ===

def add_device_to_whitelist_rules(device_identifier):
    """
    Add device rule to NETPILOT_WHITELIST chain using PROVEN WORKING logic.
    Uses mark 1 (unlimited) + RETURN to prevent hitting default limiting rule.
    """
    logger.info(f"Adding device {device_identifier} to whitelist rules (proven logic)")
    
    # Check if it's IP or MAC
    ip = _convert_to_ip(device_identifier)
    
    if ip:
        # IP-based rules for downloads (mark 1 + RETURN)
        mark_cmd = f"iptables -t mangle -I NETPILOT_WHITELIST 1 -d {ip} -j MARK --set-mark 1"
        return_cmd = f"iptables -t mangle -I NETPILOT_WHITELIST 2 -d {ip} -j RETURN"
    else:
        # MAC-based rules for uploads (mark 1 + RETURN)
        mac = device_identifier
        mark_cmd = f"iptables -t mangle -I NETPILOT_WHITELIST 1 -m mac --mac-source {mac} -j MARK --set-mark 1"
        return_cmd = f"iptables -t mangle -I NETPILOT_WHITELIST 2 -m mac --mac-source {mac} -j RETURN"
    
    # Execute both commands
    if not _execute_command(mark_cmd):
        logger.error(f"Failed to add mark rule for {device_identifier}")
        return False, f"Failed to add mark rule for {device_identifier}"
    
    if not _execute_command(return_cmd):
        logger.error(f"Failed to add return rule for {device_identifier}")
        # Try to clean up the mark rule
        _execute_command(mark_cmd.replace("-I", "-D").replace("1 ", ""))
        return False, f"Failed to add return rule for {device_identifier}"
    
    logger.info(f"Successfully added whitelist rules (mark+return) for {device_identifier}")
    return True, None

def remove_device_from_whitelist_rules(device_identifier):
    """
    Remove device rules from NETPILOT_WHITELIST chain (both mark and return rules).
    """
    logger.info(f"Removing device {device_identifier} from whitelist rules")
    
    # Check if it's IP or MAC
    ip = _convert_to_ip(device_identifier)
    
    if ip:
        # IP-based rule removal (both mark and return)
        mark_cmd = f"iptables -t mangle -D NETPILOT_WHITELIST -d {ip} -j MARK --set-mark 1"
        return_cmd = f"iptables -t mangle -D NETPILOT_WHITELIST -d {ip} -j RETURN"
    else:
        # MAC-based rule removal (both mark and return)
        mac = device_identifier
        mark_cmd = f"iptables -t mangle -D NETPILOT_WHITELIST -m mac --mac-source {mac} -j MARK --set-mark 1"
        return_cmd = f"iptables -t mangle -D NETPILOT_WHITELIST -m mac --mac-source {mac} -j RETURN"
    
    # Execute both removal commands (ignore errors since rules might not exist)
    _execute_command(mark_cmd)
    _execute_command(return_cmd)
    
    logger.info(f"Successfully removed whitelist rules for {device_identifier}")
    return True, None

def rebuild_whitelist_chain():
    """
    Rebuild whitelist chain from database state.
    This flushes the chain and recreates all rules from the stored whitelist.
    """
    logger.info("Rebuilding whitelist chain from database state")
    
    try:
        # Get current whitelist from state
        state = get_router_state()
        whitelist_devices = state.get('devices', {}).get('whitelist', [])
        
        # Flush the chain
        if not _execute_command("iptables -t mangle -F NETPILOT_WHITELIST"):
            logger.error("Failed to flush whitelist chain")
            return False, "Failed to flush whitelist chain"
        
        # Re-add default "mark all as limited" rule
        if not _execute_command("iptables -t mangle -A NETPILOT_WHITELIST -j MARK --set-mark 98"):
            logger.error("Failed to add default limiting rule to whitelist chain")
            return False, "Failed to add default limiting rule"
        
        # Add all whitelisted devices (these rules go BEFORE the default rule)
        for device in whitelist_devices:
            success, error = add_device_to_whitelist_rules(device)
            if not success:
                logger.warning(f"Failed to re-add whitelist rule for {device}: {error}")
        
        logger.info(f"Whitelist chain rebuilt with {len(whitelist_devices)} devices")
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to rebuild whitelist chain: {str(e)}")
        return False, f"Failed to rebuild whitelist chain: {str(e)}"

# === BLACKLIST DEVICE MANAGEMENT ===

def add_device_to_blacklist_rules(device_identifier):
    """
    Add device rule to NETPILOT_BLACKLIST chain (doesn't activate mode).
    According to the plan: iptables -t mangle -A NETPILOT_BLACKLIST -s {ip} -j MARK --set-mark 97
    """
    logger.info(f"Adding device {device_identifier} to blacklist rules")
    
    # Check if it's IP or MAC
    ip = _convert_to_ip(device_identifier)
    
    if ip:
        # IP-based rule
        command = f"iptables -t mangle -A NETPILOT_BLACKLIST -s {ip} -j MARK --set-mark 97"
    else:
        # MAC-based rule
        mac = device_identifier
        command = f"iptables -t mangle -A NETPILOT_BLACKLIST -m mac --mac-source {mac} -j MARK --set-mark 97"
    
    if not _execute_command(command):
        logger.error(f"Failed to add blacklist rule for {device_identifier}")
        return False, f"Failed to add blacklist rule for {device_identifier}"
    
    logger.info(f"Successfully added blacklist rule for {device_identifier}")
    return True, None

def remove_device_from_blacklist_rules(device_identifier):
    """
    Remove device rule from NETPILOT_BLACKLIST chain.
    """
    logger.info(f"Removing device {device_identifier} from blacklist rules")
    
    # Check if it's IP or MAC
    ip = _convert_to_ip(device_identifier)
    
    if ip:
        # IP-based rule removal
        command = f"iptables -t mangle -D NETPILOT_BLACKLIST -s {ip} -j MARK --set-mark 97"
    else:
        # MAC-based rule removal
        mac = device_identifier
        command = f"iptables -t mangle -D NETPILOT_BLACKLIST -m mac --mac-source {mac} -j MARK --set-mark 97"
    
    if not _execute_command(command):
        logger.warning(f"Could not remove blacklist rule for {device_identifier} (may not exist)")
        return True, None  # Not finding the rule to remove is not an error
    
    logger.info(f"Successfully removed blacklist rule for {device_identifier}")
    return True, None

def rebuild_blacklist_chain():
    """
    Rebuild blacklist chain from database state.
    This flushes the chain and recreates all rules from the stored blacklist.
    """
    logger.info("Rebuilding blacklist chain from database state")
    
    try:
        # Get current blacklist from state
        state = get_router_state()
        blacklist_devices = state.get('devices', {}).get('blacklist', [])
        
        # Flush the chain (blacklist starts empty, no default rule)
        if not _execute_command("iptables -t mangle -F NETPILOT_BLACKLIST"):
            logger.error("Failed to flush blacklist chain")
            return False, "Failed to flush blacklist chain"
        
        # Add all blacklisted devices
        for device in blacklist_devices:
            success, error = add_device_to_blacklist_rules(device)
            if not success:
                logger.warning(f"Failed to re-add blacklist rule for {device}: {error}")
        
        logger.info(f"Blacklist chain rebuilt with {len(blacklist_devices)} devices")
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to rebuild blacklist chain: {str(e)}")
        return False, f"Failed to rebuild blacklist chain: {str(e)}"

# === CHAIN VALIDATION ===

def validate_device_chains():
    """
    Validates that the device chains are properly configured.
    Returns status of both whitelist and blacklist chains.
    """
    logger.info("Validating device chains")
    
    try:
        validation_results = {
            'whitelist_chain': {},
            'blacklist_chain': {}
        }
        
        # Check whitelist chain
        output, _ = router_connection_manager.execute("iptables -t mangle -L NETPILOT_WHITELIST -n --line-numbers")
        validation_results['whitelist_chain'] = {
            'exists': 'NETPILOT_WHITELIST' in output if output else False,
            'rules_output': output.strip() if output else 'No output',
            'has_default_rule': '--set-mark 0x62' in output if output else False  # 0x62 = 98
        }
        
        # Check blacklist chain  
        output, _ = router_connection_manager.execute("iptables -t mangle -L NETPILOT_BLACKLIST -n --line-numbers")
        validation_results['blacklist_chain'] = {
            'exists': 'NETPILOT_BLACKLIST' in output if output else False,
            'rules_output': output.strip() if output else 'No output'
        }
        
        logger.info(f"Chain validation completed: {validation_results}")
        return True, validation_results
        
    except Exception as e:
        logger.error(f"Failed to validate device chains: {str(e)}")
        return False, f"Chain validation failed: {str(e)}"
