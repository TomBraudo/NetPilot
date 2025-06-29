from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
from services.router_state_manager import get_router_state

logger = get_logger('services.mode_activation')
router_connection_manager = RouterConnectionManager()

def _execute_command(command: str):
    """
    Executes a command on the router with proper error handling.
    """
    output, err = router_connection_manager.execute(command, timeout=10)
    
    if err:
        error_lower = err.lower()
        # Check for idempotent operations that are safe to ignore
        if any(phrase in error_lower for phrase in [
            "file exists", "already exists", "cannot find", 
            "no such file", "chain already exists", "no chain/target/match",
            "bad rule", "does not exist"
        ]):
            logger.debug(f"Idempotent operation (safe to ignore): {command}")
            return True
            
        # Real errors that should fail the operation
        logger.error(f"Command failed: {command} - Error: {err}")
        return False
    
    logger.debug(f"Command successful: {command}")
    return True

def _execute_command_with_fallback(command: str, fallback_command: str = None):
    """
    Executes a command with an optional fallback if the first command fails.
    Used for POSTROUTING commands that might have execution issues.
    """
    output, err = router_connection_manager.execute(command, timeout=10)
    
    if err:
        error_lower = err.lower()
        
        # Check for idempotent operations that are safe to ignore
        if any(phrase in error_lower for phrase in [
            "file exists", "already exists", "cannot find", 
            "no such file", "chain already exists", "no chain/target/match",
            "bad rule", "does not exist"
        ]):
            logger.debug(f"Idempotent operation (safe to ignore): {command}")
            return True
        
        # If we have a fallback command, try it
        if fallback_command:
            logger.warning(f"Primary command failed, trying fallback: {command} -> {fallback_command}")
            return _execute_command(fallback_command)
        
        # Real errors that should fail the operation
        logger.error(f"Command failed: {command} - Error: {err}")
        return False
    
    logger.debug(f"Command successful: {command}")
    return True

def _complete_teardown():
    """
    NAIVE APPROACH: Complete teardown of ALL NetPilot rules and TC infrastructure.
    
    This function removes everything NetPilot-related from the router:
    - All iptables jump rules from all chains
    - All NetPilot chains (flush and delete)
    - All TC qdiscs on all interfaces
    
    Since we're using the naive approach, we don't check if rules exist -
    we just try to remove everything and ignore errors with || true.
    
    This ensures a completely clean slate for rebuilding, even if persistent
    infrastructure was previously created by setup_router_infrastructure().
    """
    logger.info("Performing complete teardown of ALL NetPilot infrastructure")
    
    # Remove ALL possible NetPilot iptables jump rules from ALL chains
    _execute_command("iptables -t mangle -D FORWARD -j NETPILOT_WHITELIST 2>/dev/null || true")
    _execute_command("iptables -t mangle -D INPUT -j NETPILOT_WHITELIST 2>/dev/null || true")
    _execute_command("iptables -t mangle -D OUTPUT -j NETPILOT_WHITELIST 2>/dev/null || true")
    _execute_command("iptables -t mangle -D PREROUTING -j NETPILOT_WHITELIST 2>/dev/null || true")
    _execute_command("iptables -t mangle -D POSTROUTING -j NETPILOT_WHITELIST 2>/dev/null || true")
    
    _execute_command("iptables -t mangle -D FORWARD -j NETPILOT_BLACKLIST 2>/dev/null || true")
    _execute_command("iptables -t mangle -D INPUT -j NETPILOT_BLACKLIST 2>/dev/null || true")
    _execute_command("iptables -t mangle -D OUTPUT -j NETPILOT_BLACKLIST 2>/dev/null || true")
    _execute_command("iptables -t mangle -D PREROUTING -j NETPILOT_BLACKLIST 2>/dev/null || true")
    _execute_command("iptables -t mangle -D POSTROUTING -j NETPILOT_BLACKLIST 2>/dev/null || true")
    
    # Flush and remove ALL NetPilot chains (handles persistent infrastructure)
    _execute_command("iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true")
    _execute_command("iptables -t mangle -F NETPILOT_BLACKLIST 2>/dev/null || true")
    _execute_command("iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true")
    _execute_command("iptables -t mangle -X NETPILOT_BLACKLIST 2>/dev/null || true")
    
    # Remove ALL TC rules from ALL interfaces (handles persistent TC infrastructure)
    output, _ = router_connection_manager.execute("ls /sys/class/net/ | grep -v lo")
    if output:
        interfaces = [iface.strip() for iface in output.split() if iface.strip()]
        logger.info(f"Removing TC from {len(interfaces)} interfaces: {interfaces}")
        for iface in interfaces:
            _execute_command(f"tc qdisc del dev {iface} root 2>/dev/null || true")
            _execute_command(f"tc qdisc del dev {iface} ingress 2>/dev/null || true")
    
    logger.info("Complete teardown finished - router is now in clean state")

def _rebuild_tc_infrastructure():
    """
    Rebuild TC infrastructure on all interfaces with proven working setup.
    OPTIMIZED: Reduced interface calls and batch operations.
    """
    logger.info("Rebuilding TC infrastructure on all interfaces (optimized)")
    
    # Get state for rates (single call)
    state = get_router_state()
    unlimited_rate = state['rates'].get('whitelist_full', '1000mbit')
    limited_rate = state['rates'].get('whitelist_limited', '50mbit')
    
    # Get all interfaces (single call, cached)
    output, err = router_connection_manager.execute("ls /sys/class/net/ | grep -v lo")
    if err or not output:
        logger.error("Failed to get network interfaces")
        return False
    
    interfaces = [iface.strip() for iface in output.split() if iface.strip()]
    logger.info(f"Setting up TC on {len(interfaces)} interfaces: {interfaces}")
    
    # Batch TC setup per interface for speed
    failed_interfaces = []
    for interface in interfaces:
        # Batch all TC commands for this interface into one call
        tc_commands = f"""
tc qdisc add dev {interface} root handle 1: htb default 1 2>/dev/null;
tc class add dev {interface} parent 1: classid 1:1 htb rate {unlimited_rate} 2>/dev/null;
tc class add dev {interface} parent 1: classid 1:10 htb rate {limited_rate} 2>/dev/null;
tc filter add dev {interface} parent 1: protocol ip prio 1 handle 1 fw flowid 1:1 2>/dev/null;
tc filter add dev {interface} parent 1: protocol ip prio 2 handle 98 fw flowid 1:10 2>/dev/null;
echo "TC setup completed on {interface}"
"""
        
        output, err = router_connection_manager.execute(tc_commands.strip())
        if err and "completed" not in output:
            logger.warning(f"Some TC commands failed on {interface}: {err}")
            failed_interfaces.append(interface)
        else:
            logger.debug(f"TC setup completed on {interface}")
    
    if failed_interfaces:
        logger.warning(f"TC setup failed on {len(failed_interfaces)} interfaces: {failed_interfaces}")
    
    success_count = len(interfaces) - len(failed_interfaces)
    logger.info(f"TC infrastructure setup completed on {success_count}/{len(interfaces)} interfaces")
    return success_count > 0  # Success if at least one interface works

def _rebuild_whitelist_chain_proven():
    """
    Rebuild whitelist chain with the exact proven working logic.
    OPTIMIZED: Batch iptables commands for better performance.
    """
    logger.info("Rebuilding whitelist chain with proven working logic (optimized)")
    
    # Create the whitelist chain
    if not _execute_command("iptables -t mangle -N NETPILOT_WHITELIST"):
        logger.warning("NETPILOT_WHITELIST chain might already exist")
    
    # Get whitelisted devices from router state
    whitelisted_devices = _get_whitelisted_devices()
    logger.info(f"Adding {len(whitelisted_devices)} whitelisted devices to chain")
    
    # Build all iptables commands in batch for performance
    iptables_commands = []
    
    # Add rules for each whitelisted device (MAC + RETURN logic)
    for device_data in whitelisted_devices:
        # Handle both simple MAC strings and device objects
        if isinstance(device_data, dict):
            mac = device_data.get('mac')
            ip = device_data.get('ip')
        else:
            # Simple MAC string (current format)
            mac = device_data
            ip = None
        
        if mac:
            # MAC-based rules for uploads (mark 1 + RETURN)
            iptables_commands.append(f"iptables -t mangle -A NETPILOT_WHITELIST -m mac --mac-source {mac} -j MARK --set-mark 1")
            iptables_commands.append(f"iptables -t mangle -A NETPILOT_WHITELIST -m mac --mac-source {mac} -j RETURN")
        
        if ip:
            # IP-based rules for downloads (mark 1 + RETURN) 
            iptables_commands.append(f"iptables -t mangle -A NETPILOT_WHITELIST -d {ip} -j MARK --set-mark 1")
            iptables_commands.append(f"iptables -t mangle -A NETPILOT_WHITELIST -d {ip} -j RETURN")
    
    # Add default limiting rule LAST (everyone else gets limited)
    iptables_commands.append("iptables -t mangle -A NETPILOT_WHITELIST -j MARK --set-mark 98")
    
    # Execute all commands in batch
    if iptables_commands:
        batch_command = "; ".join(iptables_commands)
        if not _execute_command(batch_command):
            logger.error("Failed to build whitelist chain rules")
            return False
    
    logger.info(f"Whitelist chain rebuilt successfully with {len(whitelisted_devices)} devices")
    return True

def _get_whitelisted_devices():
    """
    Get whitelisted devices from router state.
    Returns list of device data (MAC addresses).
    """
    try:
        state = get_router_state()
        devices = state.get('devices', {}).get('whitelist', [])
        logger.debug(f"Found {len(devices)} whitelisted devices in state")
        return devices
    except Exception as e:
        logger.warning(f"Failed to get whitelisted devices from state: {e}")
        return []


# === WHITELIST MODE ACTIVATION ===

def activate_whitelist_mode_rules():
    """
    NAIVE APPROACH: Complete teardown and rebuild for whitelist mode activation.
    
    This implements the exact manual solution that was proven to work:
    1. Complete teardown of ALL NetPilot rules and TC infrastructure
    2. Rebuild TC infrastructure on ALL interfaces with correct priorities
    3. Rebuild whitelist chain with MAC+IP+RETURN logic
    4. Activate with FORWARD chain (proven to work reliably)
    
    Benefits of this approach:
    - Simple and reliable
    - No rule conflicts or state management
    - Proven to work through manual testing
    - Easy to debug and maintain
    
    The redundant checks for existing rules are removed since we always
    start with a clean slate.
    """
    logger.info("Activating whitelist mode with proven working solution")
    
    try:
        # === PHASE 0: ENSURE STATE FILE EXISTS ===
        logger.info("Phase 0: Ensuring state file exists")
        _ensure_state_file_exists()
        
        # === PHASE 1: COMPLETE TEARDOWN ===
        logger.info("Phase 1: Complete teardown of all NetPilot rules")
        _complete_teardown()
        
        # === PHASE 2: REBUILD TC INFRASTRUCTURE ===
        logger.info("Phase 2: Rebuilding TC infrastructure on all interfaces")
        if not _rebuild_tc_infrastructure():
            return False, "Failed to rebuild TC infrastructure"
        
        # === PHASE 3: REBUILD WHITELIST CHAIN ===
        logger.info("Phase 3: Rebuilding whitelist chain with proven logic")
        if not _rebuild_whitelist_chain_proven():
            return False, "Failed to rebuild whitelist chain"
        
        # === PHASE 4: ACTIVATE WITH FORWARD CHAIN ===
        logger.info("Phase 4: Activating whitelist with FORWARD chain")
        if not _execute_command("iptables -t mangle -A FORWARD -j NETPILOT_WHITELIST"):
            logger.error("Failed to activate whitelist in FORWARD chain")
            return False, "Failed to activate whitelist mode"
        
        logger.info("Whitelist mode activated successfully with proven working approach")
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to activate whitelist mode: {str(e)}")
        return False, f"Whitelist mode activation failed: {str(e)}"

def deactivate_whitelist_mode_rules():
    """
    Deactivate whitelist mode using the naive complete teardown approach.
    This ensures all NetPilot rules are removed and full internet access is restored.
    """
    logger.info("Deactivating whitelist mode with complete teardown")
    
    try:
        # Use the complete teardown function for deactivation
        _complete_teardown()
        
        logger.info("Whitelist mode deactivated successfully - full internet access restored")
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to deactivate whitelist mode: {str(e)}")
        return False, f"Whitelist mode deactivation failed: {str(e)}"

# === BLACKLIST MODE ACTIVATION ===

def activate_blacklist_mode_rules():
    """
    Fast activation - single iptables jump commands for blacklist mode.
    According to Phase 3 plan:
    - iptables -A PREROUTING -j NETPILOT_BLACKLIST
    - iptables -A POSTROUTING -j NETPILOT_BLACKLIST
    """
    logger.info("Activating blacklist mode with iptables jump commands")
    
    try:
        # Ensure no other modes are active (clean slate)
        deactivate_all_modes_rules()
        
        # Add PREROUTING jump to blacklist chain
        if not _execute_command("iptables -t mangle -A PREROUTING -j NETPILOT_BLACKLIST"):
            logger.error("Failed to add PREROUTING jump to NETPILOT_BLACKLIST")
            return False, "Failed to add PREROUTING rule for blacklist mode"
        
        # Add POSTROUTING jump to blacklist chain (with cleaner command)
        postrouting_success = _execute_command("iptables -t mangle -A POSTROUTING -j NETPILOT_BLACKLIST")
        if not postrouting_success:
            logger.warning("Failed to add POSTROUTING jump to NETPILOT_BLACKLIST - trying alternative approach")
            
            # Try FORWARD chain as fallback (covers internal routing)
            forward_success = _execute_command("iptables -t mangle -A FORWARD -j NETPILOT_BLACKLIST")
            if not forward_success:
                logger.error("Failed to add both POSTROUTING and FORWARD jumps")
                # Clean up PREROUTING rule
                _execute_command("iptables -t mangle -D PREROUTING -j NETPILOT_BLACKLIST")
                return False, "Failed to add routing rules for blacklist mode"
            else:
                logger.info("Using FORWARD chain instead of POSTROUTING for blacklist mode")
        
        logger.info("Blacklist mode activated successfully with iptables rules")
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to activate blacklist mode: {str(e)}")
        return False, f"Blacklist mode activation failed: {str(e)}"

def deactivate_blacklist_mode_rules():
    """
    Fast deactivation - remove jump commands for blacklist mode.
    Handles both POSTROUTING and FORWARD chains in case of fallback usage.
    """
    logger.info("Deactivating blacklist mode by removing iptables jump commands")
    
    try:
        # Remove PREROUTING jump
        _execute_command("iptables -t mangle -D PREROUTING -j NETPILOT_BLACKLIST")
        
        # Remove POSTROUTING jump
        _execute_command("iptables -t mangle -D POSTROUTING -j NETPILOT_BLACKLIST")
        
        # Remove FORWARD jump (in case it was used as fallback)
        _execute_command("iptables -t mangle -D FORWARD -j NETPILOT_BLACKLIST")
        
        logger.info("Blacklist mode deactivated successfully")
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to deactivate blacklist mode: {str(e)}")
        return False, f"Blacklist mode deactivation failed: {str(e)}"

# === UNIVERSAL MODE MANAGEMENT ===

def deactivate_all_modes_rules():
    """
    Deactivates all modes using the naive complete teardown approach.
    This ensures clean state before activating a new mode and removes all NetPilot rules.
    """
    logger.debug("Deactivating all modes with complete teardown")
    
    try:
        # Use the complete teardown function
        _complete_teardown()
        
        logger.debug("All modes deactivated successfully with complete teardown")
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to deactivate all modes: {str(e)}")
        return False, f"Mode deactivation failed: {str(e)}"

def get_active_mode_status():
    """
    Checks which mode is currently active by examining iptables rules.
    Returns the active mode ('whitelist', 'blacklist', or 'none').
    """
    logger.debug("Checking active mode status from iptables rules")
    
    try:
        # Get current iptables mangle table rules
        output, error = router_connection_manager.execute("iptables -t mangle -L PREROUTING -n")
        
        if error:
            logger.warning(f"Could not get iptables status: {error}")
            return 'unknown', f"Could not determine active mode: {error}"
        
        # Parse output to see which chain is active
        if 'NETPILOT_WHITELIST' in output:
            return 'whitelist', None
        elif 'NETPILOT_BLACKLIST' in output:
            return 'blacklist', None
        else:
            return 'none', None
            
    except Exception as e:
        logger.error(f"Failed to get active mode status: {str(e)}")
        return 'unknown', f"Status check failed: {str(e)}"

def validate_mode_activation():
    """
    Validates that the mode activation is working correctly.
    Returns detailed status of iptables rules and active mode.
    Checks PREROUTING, POSTROUTING, and FORWARD chains.
    """
    logger.info("Validating mode activation status")
    
    try:
        validation_results = {
            'active_mode': None,
            'prerouting_rules': {},
            'postrouting_rules': {},
            'forward_rules': {}
        }
        
        # Check active mode
        active_mode, mode_error = get_active_mode_status()
        validation_results['active_mode'] = {
            'mode': active_mode,
            'error': mode_error
        }
        
        # Check PREROUTING rules
        output, _ = router_connection_manager.execute("iptables -t mangle -L PREROUTING -n --line-numbers")
        validation_results['prerouting_rules'] = {
            'has_whitelist_jump': 'NETPILOT_WHITELIST' in output if output else False,
            'has_blacklist_jump': 'NETPILOT_BLACKLIST' in output if output else False,
            'rules_output': output.strip() if output else 'No output'
        }
        
        # Check POSTROUTING rules
        output, _ = router_connection_manager.execute("iptables -t mangle -L POSTROUTING -n --line-numbers")
        validation_results['postrouting_rules'] = {
            'has_whitelist_jump': 'NETPILOT_WHITELIST' in output if output else False,
            'has_blacklist_jump': 'NETPILOT_BLACKLIST' in output if output else False,
            'rules_output': output.strip() if output else 'No output'
        }
        
        # Check FORWARD rules (fallback chain)
        output, _ = router_connection_manager.execute("iptables -t mangle -L FORWARD -n --line-numbers")
        validation_results['forward_rules'] = {
            'has_whitelist_jump': 'NETPILOT_WHITELIST' in output if output else False,
            'has_blacklist_jump': 'NETPILOT_BLACKLIST' in output if output else False,
            'rules_output': output.strip() if output else 'No output'
        }
        
        logger.info(f"Mode activation validation completed: {validation_results}")
        return True, validation_results
        
    except Exception as e:
        logger.error(f"Failed to validate mode activation: {str(e)}")
        return False, f"Validation failed: {str(e)}"

def add_device_to_active_whitelist(mac, ip=None):
    """
    Add device to whitelist while mode is active (no restart needed).
    """
    logger.info(f"Adding device to active whitelist: MAC={mac}, IP={ip}")
    
    # Add MAC rule with RETURN (insert at beginning for priority)
    if mac:
        _execute_command(f"iptables -t mangle -I NETPILOT_WHITELIST 1 -m mac --mac-source {mac} -j MARK --set-mark 1")
        _execute_command(f"iptables -t mangle -I NETPILOT_WHITELIST 2 -m mac --mac-source {mac} -j RETURN")
    
    # Add IP rule with RETURN if provided
    if ip:
        _execute_command(f"iptables -t mangle -I NETPILOT_WHITELIST 3 -d {ip} -j MARK --set-mark 1")
        _execute_command(f"iptables -t mangle -I NETPILOT_WHITELIST 4 -d {ip} -j RETURN")
    
    logger.info("Device added to active whitelist - immediately unlimited")

def add_device_to_active_blacklist(mac, ip=None):
    """
    Add device to blacklist while mode is active (no restart needed).
    """
    logger.info(f"Adding device to active blacklist: MAC={mac}, IP={ip}")
    
    # Add MAC rule for limiting
    if mac:
        _execute_command(f"iptables -t mangle -I NETPILOT_BLACKLIST 1 -m mac --mac-source {mac} -j MARK --set-mark 98")
    
    # Add IP rule for limiting if provided  
    if ip:
        _execute_command(f"iptables -t mangle -I NETPILOT_BLACKLIST 2 -d {ip} -j MARK --set-mark 98")
    
    logger.info("Device added to active blacklist - immediately limited")

def update_active_mode_limits(unlimited_rate=None, limited_rate=None):
    """
    Update TC rate limits while mode is active (no restart needed).
    """
    logger.info(f"Updating active mode limits: unlimited={unlimited_rate}, limited={limited_rate}")
    
    # Get current state if rates not provided
    if not unlimited_rate or not limited_rate:
        state = get_router_state()
        unlimited_rate = unlimited_rate or state['rates'].get('whitelist_full', '1000mbit')
        limited_rate = limited_rate or state['rates'].get('whitelist_limited', '50mbit')
    
    # Update TC classes on all interfaces
    output, _ = router_connection_manager.execute("ls /sys/class/net/ | grep -v lo")
    if output:
        interfaces = [iface.strip() for iface in output.split() if iface.strip()]
        
        for interface in interfaces:
            # Update unlimited class rate
            _execute_command(f"tc class change dev {interface} classid 1:1 htb rate {unlimited_rate}")
            # Update limited class rate  
            _execute_command(f"tc class change dev {interface} classid 1:10 htb rate {limited_rate}")
            
        logger.info(f"Updated limits on {len(interfaces)} interfaces - changes applied immediately")
        return True
    
    return False

def _ensure_state_file_exists():
    """
    Ensure state file exists before mode activation.
    Creates default state if missing.
    """
    logger.info("Checking if state file exists...")
    
    STATE_FILE_PATH = "/etc/config/netpilot_state.json"
    output, _ = router_connection_manager.execute(f"[ -f {STATE_FILE_PATH} ] && echo exists || echo missing")
    
    if output and output.strip() == "missing":
        logger.info("State file missing - creating default state file")
        from services.router_state_manager import write_router_state, _get_default_state
        write_router_state(_get_default_state())
        logger.info("Default state file created successfully")
    else:
        logger.info("State file already exists")
