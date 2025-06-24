from utils.ssh_client import ssh_manager
from utils.logging_config import get_logger

logger = get_logger('utils.traffic_control_helpers')

def get_all_network_interfaces_helper():
    """Gets all network interfaces from the router, excluding 'lo'."""
    cmd = "ls /sys/class/net/"
    output, error = ssh_manager.execute_command(cmd)
    if error:
        logger.error(f"Error getting network interfaces: {error}")
        raise Exception(f"Failed to get network interfaces: {error}")
    return [iface for iface in output.split() if iface not in ['lo']]

def _run_ssh_command(cmd: str):
    """Runs a command via SSH and raises an exception if an error occurs."""
    output, error = ssh_manager.execute_command(cmd)
    if error:
        logger.error(f"Command failed: {cmd}, Error: {error}")
        raise Exception(f"Command failed: {cmd}, Error: {error}")
    if output:
        logger.debug(f"Command output for '{cmd}': {output}")
    return True

def _setup_tc_on_single_interface(interface: str, limit_rate: str, full_rate: str):
    """Sets up TC rules on a single network interface."""
    logger.info(f"Setting up TC on {interface}: Limit Rate={limit_rate}, Full Rate={full_rate}")
    _run_ssh_command(f"tc qdisc del dev {interface} root 2>/dev/null || true")
    # Default traffic to class 1:1 (full_rate)
    _run_ssh_command(f"tc qdisc add dev {interface} root handle 1: htb default 1")
    # Class 1:1 for full rate traffic
    _run_ssh_command(f"tc class add dev {interface} parent 1: classid 1:1 htb rate {full_rate}")
    # Class 1:10 for limited rate traffic
    _run_ssh_command(f"tc class add dev {interface} parent 1: classid 1:10 htb rate {limit_rate}")
    # Filter: direct packets marked with '99' to the limited rate class (1:10)
    _run_ssh_command(f"tc filter add dev {interface} parent 1: protocol ip handle 99 fw flowid 1:10")
    logger.info(f"TC setup completed for interface {interface}")
    return True

def setup_traffic_rules(mode: str, ips_to_target: list, limit_rate: str, full_rate: str):
    """
    Sets up overall traffic control rules (iptables and tc) based on the mode.
    - 'whitelist': ips_to_target are whitelisted (full_rate), others are limited.
    - 'blacklist': ips_to_target are blacklisted (limit_rate), others are full_rate.
    """
    try:
        logger.info(f"Setting up traffic rules for mode: {mode}. Target IPs: {len(ips_to_target)}. Limit: {limit_rate}, Full: {full_rate}")
        
        # Clear all previous iptables mangle rules
        _run_ssh_command("iptables -t mangle -F")

        if mode == 'whitelist':
            # For whitelist mode:
            # 1. Mark all traffic with '99' (intended for limitation).
            # 2. Then, for each IP in ips_to_target (whitelisted IPs), change its mark to '0'.
            # Traffic marked '0' will use the default htb class (1:1, full_rate).
            # Traffic remaining marked '99' will be filtered by tc to class 1:10 (limit_rate).
            _run_ssh_command("iptables -t mangle -A PREROUTING -j MARK --set-mark 99")
            _run_ssh_command("iptables -t mangle -A POSTROUTING -j MARK --set-mark 99")
            for ip in ips_to_target:
                _run_ssh_command(f"iptables -t mangle -A PREROUTING -s {ip} -j MARK --set-mark 0")
                _run_ssh_command(f"iptables -t mangle -A POSTROUTING -d {ip} -j MARK --set-mark 0")
        elif mode == 'blacklist':
            # For blacklist mode:
            # 1. Only mark traffic related to ips_to_target (blacklisted IPs) with '99'.
            # Traffic marked '99' will be filtered by tc to class 1:10 (limit_rate).
            # Unmarked traffic (non-blacklisted) will use the default htb class (1:1, full_rate).
            for ip in ips_to_target:
                _run_ssh_command(f"iptables -t mangle -A PREROUTING -s {ip} -j MARK --set-mark 99")
                _run_ssh_command(f"iptables -t mangle -A POSTROUTING -d {ip} -j MARK --set-mark 99")
        else:
            raise ValueError(f"Invalid mode for setup_traffic_rules: {mode}. Must be 'whitelist' or 'blacklist'.")

        interfaces = get_all_network_interfaces_helper()
        if not interfaces:
            logger.warning("No network interfaces found to apply TC rules.")
            # Depending on desired behavior, could raise an error or return True if no interfaces means "success"
            return True 
            
        interface_results = []
        for interface_name in interfaces:
            result = _setup_tc_on_single_interface(interface_name, limit_rate, full_rate)
            interface_results.append(result)
        
        if not all(interface_results):
            logger.warning(f"Traffic control setup failed on some interfaces for mode {mode}")
            raise Exception(f"Traffic control setup failed on some interfaces for mode {mode}")

        logger.info(f"Traffic control with iptables set up successfully for mode {mode} on all interfaces")
        return True

    except Exception as e:
        logger.error(f"Error in setup_traffic_rules for mode {mode}: {str(e)}", exc_info=True)
        raise # Re-raise for the service layer to catch and return a proper HTTP response 