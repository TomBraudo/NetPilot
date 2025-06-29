from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager
from services.router_state_manager import write_router_state, get_router_state

logger = get_logger('services.router_setup')
router_connection_manager = RouterConnectionManager()

def _execute_command(command: str):
    """
    Executes a command on the router with proper error handling and idempotency.
    """
    _, err = router_connection_manager.execute(command, timeout=15)
    
    if err:
        error_lower = err.lower()
        # Check for idempotent operations that are safe to ignore
        if any(phrase in error_lower for phrase in [
            "file exists", "already exists", "cannot find", 
            "no such file", "chain already exists"
        ]):
            logger.debug(f"Idempotent operation (safe to ignore): {command}")
            return True
            
        # Real errors that should fail the setup
        logger.error(f"Command failed: {command} - Error: {err}")
        return False
    
    logger.debug(f"Command successful: {command}")
    return True

def _get_all_network_interfaces():
    """Gets all network interfaces from the router, excluding 'lo'."""
    output, error = router_connection_manager.execute("ls /sys/class/net/")
    if error:
        logger.error(f"Failed to get network interfaces: {error}")
        return []
    return [iface.strip() for iface in output.split() if iface.strip() not in ['lo', '']]

def _ensure_state_file_exists():
    """Create the default state file on the router if it does not already exist."""
    STATE_FILE_PATH = "/etc/config/netpilot_state.json"
    output, _ = router_connection_manager.execute(f"[ -f {STATE_FILE_PATH} ] && echo exists || echo missing")
    if output.strip() == "missing":
        logger.info("State file missing on router – creating default state file")
        from services.router_state_manager import _get_default_state
        write_router_state(_get_default_state())

def _check_tc_infrastructure_exists(interface):
    """
    Check if TC infrastructure already exists on a given interface.
    Returns True if all required TC components are present.
    """
    try:
        # Check if HTB qdisc exists
        output, err = router_connection_manager.execute(f"tc qdisc show dev {interface}")
        if err or "htb" not in output:
            return False
        
        # Check if classes exist
        output, err = router_connection_manager.execute(f"tc class show dev {interface}")
        if err or "1:1" not in output or "1:10" not in output:
            return False
        
        # Check if filters exist  
        output, err = router_connection_manager.execute(f"tc filter show dev {interface}")
        if err or "handle 0x62" not in output:  # Check for mark 98 (0x62) filter
            return False
            
        return True
    except Exception as e:
        logger.debug(f"Error checking TC infrastructure on {interface}: {str(e)}")
        return False

def _check_iptables_infrastructure_exists():
    """
    Check if iptables infrastructure (NetPilot chains) already exists.
    Returns (whitelist_exists, blacklist_exists).
    """
    try:
        # Check NETPILOT_WHITELIST chain
        output, err = router_connection_manager.execute("iptables -t mangle -L NETPILOT_WHITELIST -n 2>/dev/null")
        whitelist_exists = not err and output and "Chain NETPILOT_WHITELIST" in output
        
        # Check NETPILOT_BLACKLIST chain
        output, err = router_connection_manager.execute("iptables -t mangle -L NETPILOT_BLACKLIST -n 2>/dev/null")
        blacklist_exists = not err and output and "Chain NETPILOT_BLACKLIST" in output
        
        return whitelist_exists, blacklist_exists
    except Exception as e:
        logger.debug(f"Error checking iptables infrastructure: {str(e)}")
        return False, False

def setup_router_infrastructure(restart=False):
    """
    Sets up the new persistent iptables+tc infrastructure for NetPilot bandwidth management.
    Implements Phase 1 of the WHITELIST_BLACKLIST_IMPLEMENTATION.md plan.
    This completely replaces the old nftables approach with the proven working solution.
    
    OPTIMIZED: Now checks if infrastructure already exists before recreating it.
    
    Args:
        restart (bool): If True, forces complete teardown and rebuild of all infrastructure.
                       If False (default), only creates missing components (faster).
    
    Returns:
        tuple: (success: bool, error_message: str|None)
    """
    logger.info("Checking and setting up NetPilot infrastructure...")

    # Ensure state file exists first
    _ensure_state_file_exists()
    state = get_router_state()

    # Get rates from state file
    unlimited_rate = state['rates'].get('whitelist_full', '1000mbit')
    limited_rate = state['rates'].get('whitelist_limited', '50mbit')

    # Get all network interfaces
    interfaces = _get_all_network_interfaces()
    if not interfaces:
        logger.error("No network interfaces found on router")
        return False, "No network interfaces found"

    logger.info(f"Found interfaces: {interfaces}")
    logger.info(f"Using rates - Unlimited: {unlimited_rate}, Limited: {limited_rate}")

    try:
        # === PHASE 1: CHECK EXISTING INFRASTRUCTURE OR FORCE RESTART ===
        if restart:
            logger.warning("🔄 RESTART FLAG SET - Forcing complete infrastructure rebuild...")
            logger.info("Performing complete teardown of existing infrastructure...")
            
            # Force removal of all existing infrastructure
            for interface in interfaces:
                _execute_command(f"tc qdisc del dev {interface} root 2>/dev/null || true")
                logger.debug(f"Cleaned TC on {interface}")
            
            # Remove all iptables chains and rules
            _execute_command("iptables -t mangle -F 2>/dev/null || true")
            _execute_command("iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true") 
            _execute_command("iptables -t mangle -X NETPILOT_BLACKLIST 2>/dev/null || true")
            logger.debug("Cleaned iptables chains")
            
            # Remove legacy nftables
            _execute_command("nft delete table inet netpilot 2>/dev/null || true")
            
            # Force all infrastructure to be recreated
            whitelist_exists = False
            blacklist_exists = False
            tc_status = {interface: False for interface in interfaces}
            all_tc_ready = False
            
            logger.info("✅ Complete infrastructure teardown completed - proceeding with full rebuild")
            
        else:
            logger.info("Checking existing infrastructure...")
            
            # Check iptables chains
            whitelist_exists, blacklist_exists = _check_iptables_infrastructure_exists()
            logger.info(f"Iptables chains - Whitelist: {'✓' if whitelist_exists else '✗'}, Blacklist: {'✓' if blacklist_exists else '✗'}")
            
            # Check TC infrastructure on each interface
            tc_status = {}
            all_tc_ready = True
            for interface in interfaces:
                tc_exists = _check_tc_infrastructure_exists(interface)
                tc_status[interface] = tc_exists
                if not tc_exists:
                    all_tc_ready = False
                logger.info(f"TC on {interface}: {'✓' if tc_exists else '✗'}")
            
            # If everything exists, just validate and return (only when not restarting)
            if whitelist_exists and blacklist_exists and all_tc_ready:
                logger.info("🚀 All infrastructure already exists - skipping setup!")
                logger.info("Validating existing chain contents...")
                
                # Just populate chains with current devices (fast operation)
                from services.device_rule_service import rebuild_whitelist_chain, rebuild_blacklist_chain
                
                # Quick rebuild to ensure chains have current devices
                rebuild_whitelist_chain()
                rebuild_blacklist_chain()
                
                logger.info("Infrastructure validation completed - ready for use!")
                return True, None

        # === PHASE 2: CREATE MISSING INFRASTRUCTURE ===
        if restart:
            logger.info("🔨 Building fresh infrastructure from scratch...")
        else:
            logger.info("Some infrastructure missing - creating missing components...")
        
        # Clean up any remaining legacy infrastructure
        if not restart:  # Only if we haven't already cleaned in restart mode
            logger.info("Cleaning up any legacy infrastructure...")
            _execute_command("nft delete table inet netpilot 2>/dev/null || true")

        # === PHASE 3: SET UP TC INFRASTRUCTURE ON INTERFACES THAT NEED IT ===
        interfaces_to_setup = [iface for iface, exists in tc_status.items() if not exists]
        if interfaces_to_setup:
            logger.info(f"Setting up TC infrastructure on {len(interfaces_to_setup)} interfaces: {interfaces_to_setup}")
            
            for interface in interfaces_to_setup:
                logger.info(f"Setting up TC on interface: {interface}")
                
                # Clean existing TC setup on this interface
                _execute_command(f"tc qdisc del dev {interface} root 2>/dev/null || true")
                
                # Set up HTB qdisc with default class 1:1 (unlimited)
                if not _execute_command(f"tc qdisc add dev {interface} root handle 1: htb default 1"):
                    logger.error(f"Failed to add root qdisc on {interface}")
                    return False, f"Failed to set up TC root qdisc on {interface}"
                
                # Class 1:1 - Unlimited traffic (default)
                if not _execute_command(f"tc class add dev {interface} parent 1: classid 1:1 htb rate {unlimited_rate}"):
                    logger.error(f"Failed to add unlimited class on {interface}")
                    return False, f"Failed to set up unlimited class on {interface}"
                
                # Class 1:10 - Limited traffic 
                if not _execute_command(f"tc class add dev {interface} parent 1: classid 1:10 htb rate {limited_rate}"):
                    logger.error(f"Failed to add limited class on {interface}")
                    return False, f"Failed to set up limited class on {interface}"
                
                # Filter for mark 99 -> limited class (this is the key working filter)
                if not _execute_command(f"tc filter add dev {interface} parent 1: protocol ip prio 1 handle 99 fw flowid 1:10"):
                    logger.error(f"Failed to add filter for mark 99 on {interface}")
                    return False, f"Failed to set up TC filter on {interface}"
                
                # Filter for mark 98 -> limited class (whitelist mode)
                if not _execute_command(f"tc filter add dev {interface} parent 1: protocol ip prio 2 handle 98 fw flowid 1:10"):
                    logger.warning(f"Could not add whitelist filter on {interface}")
                
                # Filter for mark 97 -> limited class (blacklist mode)  
                if not _execute_command(f"tc filter add dev {interface} parent 1: protocol ip prio 3 handle 97 fw flowid 1:10"):
                    logger.warning(f"Could not add blacklist filter on {interface}")
                    
                logger.info(f"TC setup completed on {interface}")
        else:
            logger.info("✓ All TC infrastructure already exists")

        # === PHASE 4: CREATE MISSING IPTABLES CHAINS ===
        if not whitelist_exists:
            logger.info("Creating NETPILOT_WHITELIST chain...")
            if not _execute_command("iptables -t mangle -N NETPILOT_WHITELIST"):
                logger.error("Failed to create NETPILOT_WHITELIST chain")
                return False, "Failed to create NETPILOT_WHITELIST chain"
            
            # Initialize whitelist chain with default rule
            if not _execute_command("iptables -t mangle -A NETPILOT_WHITELIST -j MARK --set-mark 98"):
                logger.error("Failed to add default limiting rule to whitelist chain")
                return False, "Failed to set up whitelist chain default rule"
        else:
            logger.info("✓ NETPILOT_WHITELIST chain already exists")
        
        if not blacklist_exists:
            logger.info("Creating NETPILOT_BLACKLIST chain...")
            if not _execute_command("iptables -t mangle -N NETPILOT_BLACKLIST"):
                logger.error("Failed to create NETPILOT_BLACKLIST chain")
                return False, "Failed to create NETPILOT_BLACKLIST chain"
        else:
            logger.info("✓ NETPILOT_BLACKLIST chain already exists")
        
        setup_type = "COMPLETE REBUILD" if restart else "optimized setup"
        logger.info(f"NetPilot infrastructure {setup_type} completed successfully!")
        logger.info(f"Infrastructure ready on {len(interfaces)} interfaces with rates: {unlimited_rate} unlimited, {limited_rate} limited")
        
        # === PHASE 5: POPULATE CHAINS WITH EXISTING DEVICES ===
        logger.info("Populating chains with existing devices from state...")
        
        # Import here to avoid circular imports during startup
        from services.device_rule_service import rebuild_whitelist_chain, rebuild_blacklist_chain
        
        # Rebuild whitelist chain with existing devices
        whitelist_success, whitelist_error = rebuild_whitelist_chain()
        if not whitelist_success:
            logger.warning(f"Failed to rebuild whitelist chain: {whitelist_error}")
        
        # Rebuild blacklist chain with existing devices  
        blacklist_success, blacklist_error = rebuild_blacklist_chain()
        if not blacklist_success:
            logger.warning(f"Failed to rebuild blacklist chain: {blacklist_error}")

        completion_msg = "🎉 NetPilot infrastructure is ready for use!"
        if restart:
            completion_msg = "🔄 NetPilot infrastructure RESTART completed - fresh setup ready for use!"
        
        logger.info(completion_msg)
        return True, None

    except Exception as e:
        logger.error(f"Failed to set up NetPilot infrastructure: {str(e)}", exc_info=True)
        return False, f"Infrastructure setup failed: {str(e)}"

def update_infrastructure_rates(unlimited_rate=None, limited_rate=None):
    """
    Updates the TC class rates on all interfaces without rebuilding the entire infrastructure.
    This allows dynamic rate changes without disrupting active connections.
    """
    logger.info(f"Updating infrastructure rates - Unlimited: {unlimited_rate}, Limited: {limited_rate}")
    
    # Get current state if rates not provided
    if unlimited_rate is None or limited_rate is None:
        state = get_router_state()
        unlimited_rate = unlimited_rate or state['rates'].get('whitelist_full', '1000mbit')
        limited_rate = limited_rate or state['rates'].get('whitelist_limited', '50mbit')
    
    interfaces = _get_all_network_interfaces()
    if not interfaces:
        logger.error("No network interfaces found for rate update")
        return False, "No network interfaces found"
    
    try:
        for interface in interfaces:
            # Update unlimited class rate
            if not _execute_command(f"tc class change dev {interface} parent 1: classid 1:1 htb rate {unlimited_rate}"):
                logger.warning(f"Could not update unlimited rate on {interface}")
            
            # Update limited class rate  
            if not _execute_command(f"tc class change dev {interface} parent 1: classid 1:10 htb rate {limited_rate}"):
                logger.warning(f"Could not update limited rate on {interface}")
                
        logger.info(f"Rate update completed on {len(interfaces)} interfaces")
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to update infrastructure rates: {str(e)}")
        return False, f"Rate update failed: {str(e)}"

def reset_infrastructure():
    """
    Complete teardown of NetPilot infrastructure for troubleshooting.
    This removes all TC and iptables rules and can be used when infrastructure becomes corrupted.
    """
    logger.warning("Performing complete infrastructure reset...")
    
    try:
        interfaces = _get_all_network_interfaces()
        
        # Remove all TC rules from all interfaces
        for interface in interfaces:
            _execute_command(f"tc qdisc del dev {interface} root 2>/dev/null || true")
        
        # Remove all iptables chains and rules
        _execute_command("iptables -t mangle -F 2>/dev/null || true")
        _execute_command("iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true")
        _execute_command("iptables -t mangle -X NETPILOT_BLACKLIST 2>/dev/null || true")
        
        # Remove nftables if present
        _execute_command("nft delete table inet netpilot 2>/dev/null || true")
        
        logger.info("Infrastructure reset completed")
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to reset infrastructure: {str(e)}")
        return False, f"Infrastructure reset failed: {str(e)}"

def validate_infrastructure():
    """
    Validates that the NetPilot infrastructure is properly set up.
    Returns detailed status of TC classes, filters, and iptables chains.
    """
    logger.info("Validating NetPilot infrastructure...")
    
    try:
        interfaces = _get_all_network_interfaces()
        validation_results = {
            'interfaces_found': len(interfaces),
            'interfaces': interfaces,
            'tc_status': {},
            'iptables_chains': {}
        }
        
        # Check TC setup on each interface
        for interface in interfaces:
            output, _ = router_connection_manager.execute(f"tc class show dev {interface}")
            validation_results['tc_status'][interface] = {
                'has_classes': '1:1' in output and '1:10' in output,
                'classes_output': output.strip() if output else 'No output'
            }
        
        # Check iptables chains
        output, _ = router_connection_manager.execute("iptables -t mangle -L -n")
        validation_results['iptables_chains'] = {
            'has_whitelist_chain': 'NETPILOT_WHITELIST' in output,
            'has_blacklist_chain': 'NETPILOT_BLACKLIST' in output,
            'chains_output': output.strip() if output else 'No output'
        }
        
        logger.info(f"Infrastructure validation completed: {validation_results}")
        return True, validation_results
        
    except Exception as e:
        logger.error(f"Failed to validate infrastructure: {str(e)}")
        return False, f"Validation failed: {str(e)}"

def rebuild_all_device_chains():
    """
    Rebuilds all device chains from the current state.
    Useful when chains become corrupted or out of sync with the database.
    """
    logger.info("Rebuilding all device chains from state...")
    
    try:
        from services.device_rule_service import rebuild_whitelist_chain, rebuild_blacklist_chain
        
        results = {
            'whitelist': {},
            'blacklist': {}
        }
        
        # Rebuild whitelist chain
        whitelist_success, whitelist_error = rebuild_whitelist_chain()
        results['whitelist'] = {
            'success': whitelist_success,
            'error': whitelist_error if not whitelist_success else None
        }
        
        # Rebuild blacklist chain
        blacklist_success, blacklist_error = rebuild_blacklist_chain()
        results['blacklist'] = {
            'success': blacklist_success,
            'error': blacklist_error if not blacklist_success else None
        }
        
        overall_success = whitelist_success and blacklist_success
        logger.info(f"Device chains rebuild completed. Success: {overall_success}")
        
        return overall_success, results
        
    except Exception as e:
        logger.error(f"Failed to rebuild device chains: {str(e)}")
        return False, f"Chain rebuild failed: {str(e)}"