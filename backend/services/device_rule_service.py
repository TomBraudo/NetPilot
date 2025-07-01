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

def _validate_ip_address(ip_address):
    """
    Validates that the input is a valid IP address.
    Returns the IP if valid, None if invalid.
    """
    import re
    ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    
    if re.match(ip_pattern, ip_address):
        return ip_address
    
    logger.error(f"Invalid IP address format: {ip_address}")
    return None

# === WHITELIST DEVICE MANAGEMENT ===

def add_device_to_whitelist_rules(ip_address):
    """
    Add device rule to NETPILOT_WHITELIST chain using IP-only logic.
    Uses mark 1 (unlimited) + RETURN to prevent hitting default limiting rule.
    """
    logger.info(f"Adding IP {ip_address} to whitelist rules")
    
    # Validate IP address
    if not _validate_ip_address(ip_address):
        return False, f"Invalid IP address: {ip_address}"
    
    # IP-based rules for traffic control (mark 1 + RETURN)
    mark_cmd = f"iptables -t mangle -I NETPILOT_WHITELIST 1 -s {ip_address} -j MARK --set-mark 1"
    return_cmd = f"iptables -t mangle -I NETPILOT_WHITELIST 2 -s {ip_address} -j RETURN"
    
    # Also add destination rules for bidirectional traffic
    mark_cmd_dest = f"iptables -t mangle -I NETPILOT_WHITELIST 3 -d {ip_address} -j MARK --set-mark 1"
    return_cmd_dest = f"iptables -t mangle -I NETPILOT_WHITELIST 4 -d {ip_address} -j RETURN"
    
    # Execute all commands
    commands = [mark_cmd, return_cmd, mark_cmd_dest, return_cmd_dest]
    for cmd in commands:
        if not _execute_command(cmd):
            logger.error(f"Failed to add whitelist rule: {cmd}")
            # Try to clean up any successfully added rules
            _execute_command(f"iptables -t mangle -D NETPILOT_WHITELIST -s {ip_address} -j MARK --set-mark 1")
            _execute_command(f"iptables -t mangle -D NETPILOT_WHITELIST -s {ip_address} -j RETURN")
            _execute_command(f"iptables -t mangle -D NETPILOT_WHITELIST -d {ip_address} -j MARK --set-mark 1")
            _execute_command(f"iptables -t mangle -D NETPILOT_WHITELIST -d {ip_address} -j RETURN")
            return False, f"Failed to add whitelist rules for {ip_address}"
    
    logger.info(f"Successfully added whitelist rules for IP {ip_address}")
    return True, None

def remove_device_from_whitelist_rules(ip_address):
    """
    Remove device rules from NETPILOT_WHITELIST chain (both source and destination rules).
    """
    logger.info(f"Removing IP {ip_address} from whitelist rules")
    
    # Validate IP address
    if not _validate_ip_address(ip_address):
        return False, f"Invalid IP address: {ip_address}"
    
    # Remove all rules for this IP (both source and destination)
    commands = [
        f"iptables -t mangle -D NETPILOT_WHITELIST -s {ip_address} -j MARK --set-mark 1",
        f"iptables -t mangle -D NETPILOT_WHITELIST -s {ip_address} -j RETURN",
        f"iptables -t mangle -D NETPILOT_WHITELIST -d {ip_address} -j MARK --set-mark 1",
        f"iptables -t mangle -D NETPILOT_WHITELIST -d {ip_address} -j RETURN"
    ]
    
    # Execute all removal commands (ignore errors since rules might not exist)
    for cmd in commands:
        _execute_command(cmd)
    
    logger.info(f"Successfully removed whitelist rules for IP {ip_address}")
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

def add_device_to_blacklist_rules(ip_address):
    """
    Add device rule to NETPILOT_BLACKLIST chain using IP-only logic.
    Uses mark 97 for blacklist traffic.
    """
    logger.info(f"Adding IP {ip_address} to blacklist rules")
    
    # Validate IP address
    if not _validate_ip_address(ip_address):
        logger.error(f"Invalid IP address: {ip_address}")
        return False, f"Invalid IP address: {ip_address}"
    
    # Add source IP rule - Mark with 98 to match the TC filter handle
    command_src = f"iptables -t mangle -A NETPILOT_BLACKLIST -s {ip_address} -j MARK --set-mark 98"
    if not _execute_command(command_src):
        logger.error(f"Failed to add blacklist source rule for {ip_address}")
        return False, f"Failed to add blacklist source rule for {ip_address}"
    
    # Add destination IP rule - Mark with 98 to match the TC filter handle
    command_dst = f"iptables -t mangle -A NETPILOT_BLACKLIST -d {ip_address} -j MARK --set-mark 98"
    if not _execute_command(command_dst):
        logger.error(f"Failed to add blacklist destination rule for {ip_address}")
        # Try to clean up the source rule we just added
        _execute_command(f"iptables -t mangle -D NETPILOT_BLACKLIST -s {ip_address} -j MARK --set-mark 97")
        return False, f"Failed to add blacklist destination rule for {ip_address}"
    
    logger.info(f"Successfully added blacklist rules for IP {ip_address}")
    return True, None

def remove_device_from_blacklist_rules(ip_address):
    """
    Remove device rule from NETPILOT_BLACKLIST chain using IP-only logic.
    First checks if the rules exist, then removes them.
    """
    logger.info(f"Removing IP {ip_address} from blacklist rules")
    
    # Validate IP address
    if not _validate_ip_address(ip_address):
        logger.error(f"Invalid IP address: {ip_address}")
        return False, f"Invalid IP address: {ip_address}"
    
    # First, check if the rules exist using a safer grep approach - check for both mark values
    # (in case there are old rules with mark 97 or new ones with mark 98)
    check_cmd = f"iptables-save -t mangle | grep -F '{ip_address} -j MARK --set-mark'"
    output, _ = router_connection_manager.execute(check_cmd)
    
    if not output.strip():
        logger.warning(f"No blacklist rules found for {ip_address} in iptables")
        # If no rules found, we consider it a success since the end state is correct
        return True, None
    
    # Rules exist, proceed with removal
    success = True
    error_messages = []
    
    # Try to remove with mark 98 (new correct value)
    command_src = f"iptables -t mangle -D NETPILOT_BLACKLIST -s {ip_address} -j MARK --set-mark 98"
    output_src, err_src = router_connection_manager.execute(command_src)
    if err_src and "Bad rule" in err_src:
        # If it failed with mark 98, try with mark 97 (old value)
        old_command_src = f"iptables -t mangle -D NETPILOT_BLACKLIST -s {ip_address} -j MARK --set-mark 97"
        output_src_old, err_src_old = router_connection_manager.execute(old_command_src)
        if err_src_old:
            logger.error(f"Failed to remove blacklist source rule for {ip_address}: {err_src_old}")
            success = False
            error_messages.append(f"Source rule: {err_src_old}")
    elif err_src:
        logger.error(f"Failed to remove blacklist source rule for {ip_address}: {err_src}")
        success = False
        error_messages.append(f"Source rule: {err_src}")
    
    # Try to remove with mark 98 (new correct value)
    command_dst = f"iptables -t mangle -D NETPILOT_BLACKLIST -d {ip_address} -j MARK --set-mark 98"
    output_dst, err_dst = router_connection_manager.execute(command_dst)
    if err_dst and "Bad rule" in err_dst:
        # If it failed with mark 98, try with mark 97 (old value)
        old_command_dst = f"iptables -t mangle -D NETPILOT_BLACKLIST -d {ip_address} -j MARK --set-mark 97"
        output_dst_old, err_dst_old = router_connection_manager.execute(old_command_dst)
        if err_dst_old:
            logger.error(f"Failed to remove blacklist destination rule for {ip_address}: {err_dst_old}")
            success = False
            error_messages.append(f"Destination rule: {err_dst_old}")
    elif err_dst:
        logger.error(f"Failed to remove blacklist destination rule for {ip_address}: {err_dst}")
        success = False
        error_messages.append(f"Destination rule: {err_dst}")
    
    if success:
        logger.info(f"Successfully removed blacklist rules for IP {ip_address}")
        return True, None
    else:
        error_msg = "; ".join(error_messages)
        return False, f"Failed to remove blacklist rules: {error_msg}"

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
