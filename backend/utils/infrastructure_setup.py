"""
Infrastructure setup utilities for NetPilot router configuration.

This module contains functions for setting up and checking the persistent
infrastructure required for NetPilot's traffic management system.
"""

from enum import Enum
from utils.logging_config import get_logger

logger = get_logger('infrastructure_setup')


class InfrastructureComponent(Enum):
    """Enum representing different infrastructure components that need to be set up."""
    STATE_FILE = "state_file"
    IPTABLES_WHITELIST_CHAIN = "iptables_whitelist_chain"
    IPTABLES_BLACKLIST_CHAIN = "iptables_blacklist_chain"
    TC_SETUP = "tc_setup"
    NETWORK_INTERFACES = "network_interfaces"


def _execute_command_with_router_manager(router_connection_manager, command: str):
    """Execute command with proper error handling using the provided router connection manager."""
    _, err = router_connection_manager.execute(command, timeout=15)
    if err:
        error_lower = err.lower()
        if any(phrase in error_lower for phrase in [
            "file exists", "already exists", "cannot find", 
            "no such file", "chain already exists", "no chain/target/match",
            "bad rule", "does not exist"
        ]):
            return True
        logger.error(f"Command failed: {command} - Error: {err}")
        return False
    return True


def _setup_state_file(router_connection_manager):
    """
    Ensure the NetPilot state file exists with default configuration.
    
    Args:
        router_connection_manager: Router connection manager instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    from services.router_state_manager import write_router_state, _get_default_state
    
    STATE_FILE_PATH = "/etc/config/netpilot_state.json"
    output, _ = router_connection_manager.execute(f"[ -f {STATE_FILE_PATH} ] && echo exists || echo missing")
    if output.strip() == "missing":
        logger.info("Creating default state file")
        write_router_state(_get_default_state())
    
    return True


def _setup_iptables_chains(router_connection_manager, setup_whitelist=True, setup_blacklist=True):
    """
    Create empty iptables chains for NetPilot (NETPILOT_WHITELIST, NETPILOT_BLACKLIST).
    
    Args:
        router_connection_manager: Router connection manager instance
        setup_whitelist: Whether to set up the NETPILOT_WHITELIST chain
        setup_blacklist: Whether to set up the NETPILOT_BLACKLIST chain
        
    Returns:
        bool: True if successful, False otherwise
    """
    success = True
    
    if setup_whitelist:
        success &= _execute_command_with_router_manager(router_connection_manager, "iptables -t mangle -N NETPILOT_WHITELIST 2>/dev/null || true")
    
    if setup_blacklist:
        success &= _execute_command_with_router_manager(router_connection_manager, "iptables -t mangle -N NETPILOT_BLACKLIST 2>/dev/null || true")
    
    return success


def _setup_tc_infrastructure(router_connection_manager, interfaces, unlimited_rate, limited_rate):
    """
    Set up Traffic Control (TC) infrastructure on all network interfaces.
    
    Args:
        router_connection_manager: Router connection manager instance
        interfaces: List of network interface names
        unlimited_rate: Rate limit for unlimited traffic class
        limited_rate: Rate limit for limited traffic class
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Setting up TC infrastructure on {len(interfaces)} interfaces")
    
    for interface in interfaces:
        # Clean any existing TC setup first
        _execute_command_with_router_manager(router_connection_manager, f"tc qdisc del dev {interface} root 2>/dev/null || true")
        
        # Set up HTB qdisc with default class (unlimited)
        if not _execute_command_with_router_manager(router_connection_manager, f"tc qdisc add dev {interface} root handle 1: htb default 1"):
            return False
        
        # Class 1:1 - Unlimited traffic (default)
        if not _execute_command_with_router_manager(router_connection_manager, f"tc class add dev {interface} parent 1: classid 1:1 htb rate {unlimited_rate}"):
            return False
        
        # Class 1:10 - Limited traffic 
        if not _execute_command_with_router_manager(router_connection_manager, f"tc class add dev {interface} parent 1: classid 1:10 htb rate {limited_rate}"):
            return False
        
        # Filters for packet marking (same for both modes)
        if not _execute_command_with_router_manager(router_connection_manager, f"tc filter add dev {interface} parent 1: protocol ip prio 1 handle 1 fw flowid 1:1"):
            return False
        
        if not _execute_command_with_router_manager(router_connection_manager, f"tc filter add dev {interface} parent 1: protocol ip prio 2 handle 98 fw flowid 1:10"):
            return False
    
    return True


def _cleanup_legacy_infrastructure(router_connection_manager):
    """
    Clean up any legacy NetPilot infrastructure.
    
    Args:
        router_connection_manager: Router connection manager instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    return _execute_command_with_router_manager(router_connection_manager, "nft delete table inet netpilot 2>/dev/null || true")


def _get_network_interfaces(router_connection_manager):
    """
    Get all available network interfaces (excluding loopback).
    
    Args:
        router_connection_manager: Router connection manager instance
        
    Returns:
        tuple: (interfaces_list, error_message) - (list of interfaces, None if successful or error message)
    """
    output, error = router_connection_manager.execute("ls /sys/class/net/")
    if error:
        return None, f"Failed to get network interfaces: {error}"
    
    interfaces = [iface.strip() for iface in output.split() if iface.strip() not in ['lo', '']]
    if not interfaces:
        return None, "No network interfaces found"
    
    return interfaces, None


def setup_persistent_infrastructure(missing_components=None):
    """
    Set up one-time persistent infrastructure:
    - TC infrastructure on all interfaces (same for both whitelist and blacklist)
    - Empty iptables chains (NETPILOT_WHITELIST, NETPILOT_BLACKLIST)
    - State file initialization
    
    This is the optimized part that only needs to be done once per session.
    Only sets up components that are specified in the missing_components list.
    
    Args:
        missing_components: List of InfrastructureComponent enums indicating which components need setup.
                          If None, all components will be set up (backward compatibility).
    
    Returns:
        tuple: (bool, str) - (True if successful, error message if failed)
    """
    from managers.router_connection_manager import RouterConnectionManager
    from services.router_state_manager import get_router_state
    
    # If no missing components specified, set up all components (backward compatibility)
    if missing_components is None:
        missing_components = list(InfrastructureComponent)
    
    router_connection_manager = RouterConnectionManager()
    
    try:
        # 1. Setup state file (if needed)
        if InfrastructureComponent.STATE_FILE in missing_components:
            logger.info("Setting up state file...")
            if not _setup_state_file(router_connection_manager):
                return False, "Failed to set up state file"
        else:
            logger.info("State file is already set up correctly - skipping")
        
        # Get configuration from state (needed for TC setup rates)
        interfaces = None
        unlimited_rate = None
        limited_rate = None
        
        # Only get network interfaces and rates if we need them for TC setup
        if (InfrastructureComponent.NETWORK_INTERFACES in missing_components or 
            InfrastructureComponent.TC_SETUP in missing_components):
            
            state = get_router_state()
            unlimited_rate = state['rates'].get('whitelist_full', '1000mbit')
            limited_rate = state['rates'].get('whitelist_limited', '50mbit')
            
            # 2. Get network interfaces (if needed)
            if InfrastructureComponent.NETWORK_INTERFACES in missing_components:
                logger.info("Checking network interfaces...")
                interfaces, error_msg = _get_network_interfaces(router_connection_manager)
                if interfaces is None:
                    return False, error_msg
            else:
                # Still need to get interfaces if TC setup is needed
                if InfrastructureComponent.TC_SETUP in missing_components:
                    interfaces, error_msg = _get_network_interfaces(router_connection_manager)
                    if interfaces is None:
                        return False, error_msg
        
        # 3. Set up TC infrastructure on all interfaces (if needed)
        if InfrastructureComponent.TC_SETUP in missing_components:
            logger.info("Setting up TC infrastructure...")
            if not _setup_tc_infrastructure(router_connection_manager, interfaces, unlimited_rate, limited_rate):
                return False, "Failed to set up TC infrastructure"
        else:
            logger.info("TC infrastructure is already set up correctly - skipping")
        
        # 4. Create empty iptables chains (if needed)
        setup_whitelist = InfrastructureComponent.IPTABLES_WHITELIST_CHAIN in missing_components
        setup_blacklist = InfrastructureComponent.IPTABLES_BLACKLIST_CHAIN in missing_components
        
        if setup_whitelist or setup_blacklist:
            logger.info("Setting up iptables chains...")
            if not _setup_iptables_chains(router_connection_manager, setup_whitelist, setup_blacklist):
                return False, "Failed to set up iptables chains"
        else:
            logger.info("Iptables chains are already set up correctly - skipping")
        
        # 5. Clean up any legacy infrastructure (always do this if any component was missing)
        if missing_components:
            logger.info("Cleaning up legacy infrastructure...")
            if not _cleanup_legacy_infrastructure(router_connection_manager):
                return False, "Failed to clean up legacy infrastructure"
        
        # Log success message
        setup_components = [comp.value for comp in missing_components]
        if setup_components:
            logger.info(f"Infrastructure setup completed for components: {', '.join(setup_components)}")
            if interfaces:
                logger.info(f"Setup applied to {len(interfaces)} interfaces")
        else:
            logger.info("No infrastructure setup needed - all components are already correct")
        
        return True, None
        
    except Exception as e:
        logger.error(f"Failed to set up persistent infrastructure: {str(e)}")
        return False, f"Infrastructure setup failed: {str(e)}"


def check_existing_infrastructure():
    """
    Check if the required NetPilot infrastructure is already set up:
    - TC classes on interfaces 
    - Iptables chains (NETPILOT_WHITELIST, NETPILOT_BLACKLIST)
    - State file existence
    
    Returns:
        tuple: (bool, list[InfrastructureComponent], str) - (
            True if all infrastructure exists,
            list of missing/incorrect components,
            descriptive message
        )
    """
    from managers.router_connection_manager import RouterConnectionManager
    from services.router_state_manager import get_router_state
    
    router_connection_manager = RouterConnectionManager()
    missing_components = []
    issues = []
    
    try:
        # 1. Check state file
        STATE_FILE_PATH = "/etc/config/netpilot_state.json"
        output, _ = router_connection_manager.execute(f"[ -f {STATE_FILE_PATH} ] && echo exists || echo missing")
        if output.strip() == "missing":
            logger.info("State file missing - infrastructure setup needed")
            missing_components.append(InfrastructureComponent.STATE_FILE)
            issues.append("State file not found")
        
        # 2. Check if iptables whitelist chain exists
        output, _ = router_connection_manager.execute("iptables -t mangle -L NETPILOT_WHITELIST -n 2>/dev/null && echo exists || echo missing")
        if output.strip() == "missing":
            logger.info("NETPILOT_WHITELIST chain missing - infrastructure setup needed")
            missing_components.append(InfrastructureComponent.IPTABLES_WHITELIST_CHAIN)
            issues.append("NETPILOT_WHITELIST chain not found")

        # 3. Check if iptables blacklist chain exists
        output, _ = router_connection_manager.execute("iptables -t mangle -L NETPILOT_BLACKLIST -n 2>/dev/null && echo exists || echo missing")
        if output.strip() == "missing":
            logger.info("NETPILOT_BLACKLIST chain missing - infrastructure setup needed")
            missing_components.append(InfrastructureComponent.IPTABLES_BLACKLIST_CHAIN)
            issues.append("NETPILOT_BLACKLIST chain not found")
        
        # 4. Check network interfaces and TC setup
        output, _ = router_connection_manager.execute("ls /sys/class/net/")
        interfaces = [iface.strip() for iface in output.split() if iface.strip() not in ['lo', '']]
        
        if not interfaces:
            logger.info("No network interfaces found")
            missing_components.append(InfrastructureComponent.NETWORK_INTERFACES)
            issues.append("No network interfaces found")
        else:
            # Check the first interface that's not loopback for TC setup
            test_interface = interfaces[0]
            output, _ = router_connection_manager.execute(f"tc class show dev {test_interface} | grep '1:1\|1:10' | wc -l")
            if not output.strip() or int(output.strip()) < 2:  # We expect at least 2 classes (1:1 and 1:10)
                logger.info(f"TC classes missing on {test_interface} - infrastructure setup needed")
                missing_components.append(InfrastructureComponent.TC_SETUP)
                issues.append(f"TC setup incomplete on interface {test_interface}")
        
        # Determine overall status and message
        if not missing_components:
            logger.info("All required infrastructure found - skipping setup")
            return True, [], "All infrastructure components are properly set up"
        else:
            component_names = [comp.value for comp in missing_components]
            message = f"Missing or incorrect components: {', '.join(component_names)}. Issues: {'; '.join(issues)}"
            return False, missing_components, message
        
    except Exception as e:
        logger.error(f"Error checking existing infrastructure: {str(e)}")
        return False, [comp for comp in InfrastructureComponent], f"Infrastructure check failed: {str(e)}"
