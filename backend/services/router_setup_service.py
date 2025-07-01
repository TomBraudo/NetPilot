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



def setup_router_infrastructure(restart=False):
    """
    Sets up the basic TC infrastructure for NetPilot bandwidth management.
    This is now only used for one-time setup in start_session.
    Mode-specific setup is handled by mode activation services using naive approach.
    
    Args:
        restart (bool): If True, forces complete teardown and rebuild of all infrastructure.
    
    Returns:
        tuple: (success: bool, error_message: str|None)
    """
    logger.info("Setting up basic NetPilot TC infrastructure...")

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
        # Force removal of all existing infrastructure if restart
        if restart:
            logger.warning("RESTART FLAG SET - Forcing complete infrastructure rebuild...")
            
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
            
        # Clean up any legacy infrastructure
        logger.info("Cleaning up any legacy infrastructure...")
        _execute_command("nft delete table inet netpilot 2>/dev/null || true")

        # Set up TC infrastructure on all interfaces
        logger.info(f"Setting up TC infrastructure on {len(interfaces)} interfaces")
        
        for interface in interfaces:
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
            
            # Filter for mark 99 -> limited class
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

        # Create empty iptables chains
        logger.info("Creating empty iptables chains...")
        if not _execute_command("iptables -t mangle -N NETPILOT_WHITELIST"):
            logger.debug("NETPILOT_WHITELIST chain might already exist")
        
        if not _execute_command("iptables -t mangle -N NETPILOT_BLACKLIST"):
            logger.debug("NETPILOT_BLACKLIST chain might already exist")
        
        logger.info("Basic NetPilot infrastructure setup completed successfully!")
        logger.info(f"Infrastructure ready on {len(interfaces)} interfaces with rates: {unlimited_rate} unlimited, {limited_rate} limited")
        
        return True, None

    except Exception as e:
        logger.error(f"Failed to set up NetPilot infrastructure: {str(e)}", exc_info=True)
        return False, f"Infrastructure setup failed: {str(e)}"



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

