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
    NAIVE APPROACH: Complete teardown of mode-specific NetPilot rules only.
    
    This function removes mode-specific components but keeps persistent infrastructure:
    - All iptables jump rules from all chains
    - All NetPilot chain contents (flush but don't delete chains)
    - Keep TC infrastructure intact (set up once in start_session)
    
    This ensures mode switching is fast while keeping the persistent setup.
    """
    logger.info("Performing teardown of mode-specific NetPilot rules")
    
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
    
    # Flush NetPilot chains but keep them for reuse (don't delete)
    _execute_command("iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true")
    _execute_command("iptables -t mangle -F NETPILOT_BLACKLIST 2>/dev/null || true")
    
    # NOTE: TC infrastructure is kept intact (set up once in start_session)
    logger.info("Mode-specific teardown finished - persistent infrastructure preserved")



def activate_whitelist_mode_rules():
    """
    NAIVE APPROACH: Complete teardown and rebuild for whitelist mode activation.
    
    This implements the exact manual solution that was proven to work:
    1. Complete teardown of ALL NetPilot rules and TC infrastructure
    2. Rebuild TC infrastructure on ALL interfaces with correct priorities
    3. Rebuild whitelist chain with IP+RETURN logic
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
        
        # === PHASE 2: TC INFRASTRUCTURE CHECK (NAIVE APPROACH) ===  
        logger.info("Phase 2: TC infrastructure already setup once in start_session - skipping rebuild")
        
        # === PHASE 3: REBUILD WHITELIST CHAIN ===
        logger.info("Phase 3: Rebuilding whitelist chain from database state")
        from services.device_rule_service import rebuild_whitelist_chain
        success, error = rebuild_whitelist_chain()
        if not success:
            return False, f"Failed to rebuild whitelist chain: {error}"
        
        # === PHASE 4: ACTIVATE WITH FORWARD CHAIN ===
        logger.info("Phase 4: Activating whitelist with FORWARD chain")
        if not _execute_command("iptables -t mangle -A FORWARD -j NETPILOT_WHITELIST"):
            logger.error("Failed to activate whitelist in FORWARD chain")
            return False, "Failed to activate whitelist mode"
        
        # === PHASE 5: APPLY RATE LIMITS FROM STATE FILE ===
        logger.info("Phase 5: Applying stored rate limits to TC classes")
        if not update_active_mode_limits():
            logger.warning("Failed to update rate limits - mode activated but using default rates")
            # Don't fail the entire activation for rate limit issues
        
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
    NAIVE APPROACH: Complete teardown and rebuild for blacklist mode.
    """
    logger.info("Activating blacklist mode using naive approach (complete teardown and rebuild)")
    
    try:
        # === PHASE 1: COMPLETE TEARDOWN ===
        logger.info("Phase 1: Complete teardown of all NetPilot rules")
        _complete_teardown()
        
        # === PHASE 2: REBUILD BLACKLIST CHAIN ===
        logger.info("Phase 2: Rebuilding blacklist chain from database state")
        from services.device_rule_service import rebuild_blacklist_chain
        success, error = rebuild_blacklist_chain()
        if not success:
            return False, f"Failed to rebuild blacklist chain: {error}"
        
        # === PHASE 3: ACTIVATE WITH FORWARD CHAIN ===
        logger.info("Phase 3: Activating blacklist with FORWARD chain")
        if not _execute_command("iptables -t mangle -A FORWARD -j NETPILOT_BLACKLIST"):
            logger.error("Failed to activate blacklist in FORWARD chain")
            return False, "Failed to activate blacklist mode"
        
        # === PHASE 4: APPLY RATE LIMITS FROM STATE FILE ===
        logger.info("Phase 4: Applying stored rate limits to TC classes")
        if not update_active_mode_limits():
            logger.warning("Failed to update rate limits - mode activated but using default rates")
            # Don't fail the entire activation for rate limit issues
        
        logger.info("Blacklist mode activated successfully using naive approach")
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to activate blacklist mode: {str(e)}")
        return False, f"Blacklist mode activation failed: {str(e)}"

def deactivate_blacklist_mode_rules():
    """
    NAIVE APPROACH: Complete teardown for blacklist mode deactivation.
    """
    logger.info("Deactivating blacklist mode using naive approach (complete teardown)")
    
    try:
        # Complete teardown - removes all mode-specific rules
        _complete_teardown()
        
        logger.info("Blacklist mode deactivated successfully using naive approach")
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

def add_device_to_active_whitelist(ip):
    """
    Add device to whitelist while mode is active (no restart needed).
    Uses IP-only logic for consistency.
    """
    logger.info(f"Adding device to active whitelist: IP={ip}")
    
    # Add IP rules with RETURN (insert at beginning for priority)
    _execute_command(f"iptables -t mangle -I NETPILOT_WHITELIST 1 -s {ip} -j MARK --set-mark 1")
    _execute_command(f"iptables -t mangle -I NETPILOT_WHITELIST 2 -s {ip} -j RETURN")
    _execute_command(f"iptables -t mangle -I NETPILOT_WHITELIST 3 -d {ip} -j MARK --set-mark 1")
    _execute_command(f"iptables -t mangle -I NETPILOT_WHITELIST 4 -d {ip} -j RETURN")
    
    logger.info("Device added to active whitelist - immediately unlimited")

def add_device_to_active_blacklist(ip):
    """
    Add device to blacklist while mode is active (no restart needed).
    Uses IP-only logic for consistency.
    """
    logger.info(f"Adding device to active blacklist: IP={ip}")
    
    # Add IP rules for limiting
    _execute_command(f"iptables -t mangle -I NETPILOT_BLACKLIST 1 -s {ip} -j MARK --set-mark 98")
    _execute_command(f"iptables -t mangle -I NETPILOT_BLACKLIST 2 -d {ip} -j MARK --set-mark 98")
    
    logger.info("Device added to active blacklist - immediately limited")
    
    logger.info("Device added to active blacklist - immediately limited")

def update_active_mode_limits(unlimited_rate=None, limited_rate=None):
    """
    Update TC rate limits while mode is active (no restart needed).
    Automatically detects the active mode and uses appropriate rates.
    """
    logger.info(f"Updating active mode limits: unlimited={unlimited_rate}, limited={limited_rate}")
    
    # Get current state to determine active mode and rates
    state = get_router_state()
    active_mode = state.get('active_mode', 'none')
    
    if active_mode == 'none':
        logger.warning("No mode is active - cannot update limits")
        return False
    
    # Get rates based on active mode if not provided
    if not unlimited_rate or not limited_rate:
        if active_mode == 'whitelist':
            unlimited_rate = unlimited_rate or state['rates'].get('whitelist_full', '1000mbit')
            limited_rate = limited_rate or state['rates'].get('whitelist_limited', '50mbit')
        elif active_mode == 'blacklist':
            # In blacklist mode, unlimited rate is still needed for TC class 1:1 (non-blacklisted devices)
            unlimited_rate = unlimited_rate or state['rates'].get('whitelist_full', '1000mbit')  # Use whitelist_full for non-blacklisted
            limited_rate = limited_rate or state['rates'].get('blacklist_limited', '50mbit')  # Use blacklist_limited for blacklisted
        else:
            logger.error(f"Unknown active mode: {active_mode}")
            return False
    
    # Update TC classes on all interfaces
    output, _ = router_connection_manager.execute("ls /sys/class/net/ | grep -v lo")
    if output:
        interfaces = [iface.strip() for iface in output.split() if iface.strip()]
        
        for interface in interfaces:
            # Update unlimited class rate (1:1)
            _execute_command(f"tc class change dev {interface} classid 1:1 htb rate {unlimited_rate}")
            # Update limited class rate (1:10)
            _execute_command(f"tc class change dev {interface} classid 1:10 htb rate {limited_rate}")
            
        logger.info(f"Updated limits on {len(interfaces)} interfaces for {active_mode} mode - changes applied immediately")
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

def remove_device_from_active_blacklist(ip):
    """
    Remove device from blacklist while mode is active (no restart needed).
    Uses IP-only logic for consistency.
    """
    logger.info(f"Removing device from active blacklist: IP={ip}")
    
    # Remove IP rules for limiting (both source and destination)
    _execute_command(f"iptables -t mangle -D NETPILOT_BLACKLIST -s {ip} -j MARK --set-mark 98")
    _execute_command(f"iptables -t mangle -D NETPILOT_BLACKLIST -d {ip} -j MARK --set-mark 98")
    
    # Also try removing with old mark 97 (in case there are legacy rules)
    _execute_command(f"iptables -t mangle -D NETPILOT_BLACKLIST -s {ip} -j MARK --set-mark 97")
    _execute_command(f"iptables -t mangle -D NETPILOT_BLACKLIST -d {ip} -j MARK --set-mark 97")
    
    logger.info("Device removed from active blacklist - immediately unlimited")

def remove_device_from_active_whitelist(ip):
    """
    Remove device from whitelist while mode is active (no restart needed).
    Uses IP-only logic for consistency.
    """
    logger.info(f"Removing device from active whitelist: IP={ip}")
    
    # Remove IP rules (both MARK and RETURN rules for source and destination)
    _execute_command(f"iptables -t mangle -D NETPILOT_WHITELIST -s {ip} -j MARK --set-mark 1")
    _execute_command(f"iptables -t mangle -D NETPILOT_WHITELIST -s {ip} -j RETURN")
    _execute_command(f"iptables -t mangle -D NETPILOT_WHITELIST -d {ip} -j MARK --set-mark 1")
    _execute_command(f"iptables -t mangle -D NETPILOT_WHITELIST -d {ip} -j RETURN")
    
    logger.info("Device removed from active whitelist - now follows default rules")
