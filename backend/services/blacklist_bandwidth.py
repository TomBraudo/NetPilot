#!/usr/bin/env python3
from utils.ssh_client import ssh_manager
from utils.response_helpers import success, error
from db.tinydb_client import db_client
from utils.path_utils import get_data_folder
from utils.logging_config import get_logger
import os
import json

# Get logger for blacklist bandwidth service
logger = get_logger('blacklist.bandwidth')

# Get the blacklist config file path
blacklist_config_path = os.path.join(get_data_folder(), "blacklist_config.json")

def load_blacklist_config():
    """
    Loads the blacklist configuration from the config file
    
    Returns:
        dict: The blacklist configuration
    """
    with open(blacklist_config_path, 'r') as f:
        return json.load(f)

# Load initial config
blacklist_config = load_blacklist_config()

# Default settings
Wan_Interface = blacklist_config.get('Wan_Interface', "eth0")  # Default interface

def get_limit_rate():
    """
    Gets the current limit rate from the config file
    
    Returns:
        str: The current limit rate
    """
    config = load_blacklist_config()
    return config.get('Limit_Rate', "50mbit")

def get_full_rate():
    """
    Gets the current full rate from the config file
    
    Returns:
        str: The current full rate
    """
    config = load_blacklist_config()
    return config.get('Full_Rate', "1000mbit")

def update_blacklist_interface(interface):
    """
    Updates the blacklist interface in the blacklist config
    
    Returns:
        str: The interface that was set
        
    Raises:
        Exception: If there was an error updating the config
    """
    try:
        blacklist_config['Wan_Interface'] = interface
        with open(blacklist_config_path, 'w') as f:
            json.dump(blacklist_config, f)
        logger.info(f"Updated blacklist interface to {interface}")
        return interface
    except Exception as e:
        logger.error(f"Error updating blacklist interface: {str(e)}", exc_info=True)
        raise

def format_rate(rate):
    """
    Formats a rate value to include units if not already present.
    If the input is a number or numeric string, appends 'mbit'.
    If the input already has units, returns as is.
    
    Args:
        rate: The rate value (can be number, string with or without units)
        
    Returns:
        str: Formatted rate with units
    """
    try:
        # If it's already a string with units, return as is
        if isinstance(rate, str) and any(unit in rate.lower() for unit in ['mbit', 'kbit', 'gbit']):
            return rate
            
        # Convert to number and append mbit
        rate_num = float(rate)
        return f"{rate_num}mbit"
    except (ValueError, TypeError):
        # If conversion fails, return default
        logger.warning(f"Invalid rate format: {rate}, using default")
        return "50mbit"

def update_blacklist_limit_rate(rate):
    """
    Updates the blacklist limit rate in the blacklist config and reapplies the traffic control
    
    Args:
        rate: The rate value (can be number or string with/without units)
    
    Returns:
        str: The rate that was set
        
    Raises:
        Exception: If there was an error updating the config
    """
    try:
        formatted_rate = format_rate(rate)
        blacklist_config['Limit_Rate'] = formatted_rate
        with open(blacklist_config_path, 'w') as f:
            json.dump(blacklist_config, f)
        logger.info(f"Updated blacklist limit rate to {formatted_rate}")
        
        # Reapply traffic control with new rate
        setup_tc_with_iptables()
        
        return formatted_rate
    except Exception as e:
        logger.error(f"Error updating blacklist limit rate: {str(e)}", exc_info=True)
        raise

def update_blacklist_full_rate(rate):
    """
    Updates the blacklist full rate in the blacklist config and reapplies the traffic control
    
    Args:
        rate: The rate value (can be number or string with/without units)
    
    Returns:
        str: The rate that was set
        
    Raises:
        Exception: If there was an error updating the config
    """
    try:
        formatted_rate = format_rate(rate)
        blacklist_config['Full_Rate'] = formatted_rate
        with open(blacklist_config_path, 'w') as f:
            json.dump(blacklist_config, f)
        logger.info(f"Updated blacklist full rate to {formatted_rate}")
        
        # Reapply traffic control with new rate
        setup_tc_with_iptables()
        
        return formatted_rate
    except Exception as e:
        logger.error(f"Error updating blacklist full rate: {str(e)}", exc_info=True)
        raise

def get_blacklist_ips():
    """
    Retrieves the blacklist of IPs from the TinyDB database
    
    Returns:
        list: List of IP addresses
    """
    try:
        # Get blacklist entries directly from the client
        blacklist_entries = db_client.bandwidth_blacklist.all()
        
        # Extract IPs from entries
        blacklist_ips = [entry.get('ip') for entry in blacklist_entries if entry.get('ip')]
        
        if not blacklist_ips:
            logger.warning("No IPs found in blacklist")
            return []
            
        logger.info(f"Found {len(blacklist_ips)} IPs in blacklist")
        return blacklist_ips
    except Exception as e:
        logger.error(f"Error retrieving blacklist: {str(e)}", exc_info=True)
        return []

def run_command(cmd):
    """
    Execute a command via SSH and handle errors
    """
    logger.debug(f"Executing command: {cmd}")
    output, error_msg = ssh_manager.execute_command(cmd)
    if error_msg and "No such file or directory" not in error_msg and "Cannot delete" not in error_msg:
        logger.warning(f"Command '{cmd}' returned error: {error_msg}")
    return output, error_msg

def get_all_network_interfaces():
    """
    Retrieves all available network interfaces on the router
    
    Returns:
        list: List of network interface names
    """
    output, _ = run_command("ls -1 /sys/class/net/ | grep -v lo")
    if output:
        interfaces = [iface.strip() for iface in output.split('\n') if iface.strip()]
        logger.info(f"Found network interfaces: {interfaces}")
        return interfaces
    logger.warning(f"No interfaces found, defaulting to {Wan_Interface}")
    return [Wan_Interface]  # Fallback to the default interface

def setup_tc_on_interface(interface, blacklist_ips, limit_rate=None, full_rate=None):
    """
    Sets up traffic control on a specific interface for blacklist mode
    
    Returns:
        bool: True if successful
    """
    try:
        # Get current rates if not specified
        if limit_rate is None:
            limit_rate = get_limit_rate()
        if full_rate is None:
            full_rate = get_full_rate()
            
        logger.info(f"Setting up traffic control on {interface} with limit {limit_rate}")
        
        # Clear previous rules for this interface
        run_command(f"tc qdisc del dev {interface} root 2>/dev/null || true")

        # Add root HTB qdisc
        run_command(f"tc qdisc add dev {interface} root handle 1: htb default 1")

        # Class 1: default for full bandwidth devices
        run_command(f"tc class add dev {interface} parent 1: classid 1:1 htb rate {full_rate}")

        # Class 10: limited bandwidth for blacklisted IPs
        run_command(f"tc class add dev {interface} parent 1: classid 1:10 htb rate {limit_rate}")

        # tc filter: mark 99 => limited bandwidth
        run_command(f"tc filter add dev {interface} parent 1: protocol ip handle 99 fw flowid 1:10")
        
        logger.info(f"Traffic control setup completed for interface {interface}")
        return True
    except Exception as e:
        logger.error(f"Error setting up TC on interface {interface}: {str(e)}", exc_info=True)
        return False

def setup_tc_with_iptables(blacklist_ips=None, wan_iface=Wan_Interface, limit_rate=None, full_rate=None):
    """
    Sets up traffic control with iptables to limit bandwidth for blacklisted IPs
    on all relevant interfaces
    
    Returns:
        bool: True if successful
    """
    try:
        # If no blacklist_ips are provided, get them from the database
        if blacklist_ips is None:
            blacklist_ips = get_blacklist_ips()
        
        logger.info(f"Blacklist contains {len(blacklist_ips)} IPs")
        
        # Get all network interfaces
        interfaces = get_all_network_interfaces()
        
        # Clear previous iptables rules
        run_command("iptables -t mangle -F")
        
        # iptables mangle rules: mark blacklist with mark 99
        for ip in blacklist_ips:
            run_command(f"iptables -t mangle -A PREROUTING -s {ip} -j MARK --set-mark 99")
            run_command(f"iptables -t mangle -A POSTROUTING -d {ip} -j MARK --set-mark 99")
        
        # Setup traffic control on each interface
        interface_results = []
        for interface in interfaces:
            result = setup_tc_on_interface(interface, blacklist_ips, limit_rate, full_rate)
            interface_results.append(result)
        
        # Return True only if all interfaces were successfully configured
        success = all(interface_results)
        if success:
            logger.info("Traffic control with iptables set up successfully on all interfaces")
        else:
            logger.warning("Traffic control setup failed on some interfaces")
        
        return success
    except Exception as e:
        logger.error(f"Error setting up TC with iptables: {str(e)}", exc_info=True)
        return False

def add_single_device_to_blacklist(ip):
    """
    Adds a single device to blacklist and traffic control rules
    
    Args:
        ip (str): IP address of the device
    
    Returns:
        bool: True if successful
        
    Raises:
        Exception: If there was an error adding the device
    """
    try:
        logger.info(f"Adding device {ip} to blacklist and traffic control rules")
        
        # 1. Add iptables marking rules
        run_command(f"iptables -t mangle -A PREROUTING -s {ip} -j MARK --set-mark 99")
        run_command(f"iptables -t mangle -A POSTROUTING -d {ip} -j MARK --set-mark 99")
        
        # 2. Get all network interfaces
        interfaces = get_all_network_interfaces()
        
        # 3. Ensure tc filter is set up correctly on each interface
        for interface in interfaces:
            # Check if the interface has traffic control set up
            output, _ = run_command(f"tc qdisc show dev {interface}")
            if "htb" in output:
                # Ensure the filter is properly configured
                run_command(f"tc filter add dev {interface} parent 1: protocol ip handle 99 fw flowid 1:10")
        
        logger.info(f"Device {ip} successfully added to blacklist and traffic control on all interfaces")
        return True
    except Exception as e:
        logger.error(f"Error adding device to blacklist: {str(e)}", exc_info=True)
        raise

def remove_single_device_from_blacklist(ip):
    """
    Removes a single device from blacklist and traffic control rules
    
    Args:
        ip (str): IP address to remove
    
    Returns:
        bool: True if successful
        
    Raises:
        Exception: If there was an error removing the device
    """
    try:
        logger.info(f"Removing device {ip} from blacklist and traffic control rules")
        
        # 1. Remove iptables marking rules
        run_command(f"iptables -t mangle -D PREROUTING -s {ip} -j MARK --set-mark 99 2>/dev/null || true")
        run_command(f"iptables -t mangle -D POSTROUTING -d {ip} -j MARK --set-mark 99 2>/dev/null || true")
        
        # No need to update tc filters on interfaces since they operate on mark 99,
        # and we've just removed the marking for this IP
        
        logger.info(f"Device {ip} successfully removed from blacklist and traffic control")
        return True
    except Exception as e:
        logger.error(f"Error removing device from blacklist: {str(e)}", exc_info=True)
        raise

def activate_blacklist_mode():
    """
    Activates blacklist mode on the router, setting up traffic control
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Activating blacklist mode on router")
        # Setup traffic control
        blacklist_ips = get_blacklist_ips()
        result = setup_tc_with_iptables(blacklist_ips)
        logger.info(f"Blacklist mode activation {'succeeded' if result else 'failed'}")
        return result
    except Exception as e:
        logger.error(f"Error activating blacklist mode: {str(e)}", exc_info=True)
        return False

def deactivate_blacklist_mode():
    """
    Deactivates blacklist mode on the router, removing all traffic control rules
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Deactivating blacklist mode on router")
        # Get all network interfaces
        interfaces = get_all_network_interfaces()
        
        # Remove traffic control from each interface
        for interface in interfaces:
            run_command(f"tc qdisc del dev {interface} root 2>/dev/null || true")
        
        # Clear all iptables rules
        run_command("iptables -t mangle -F")
        
        logger.info("Blacklist mode deactivated on router")
        return True
    except Exception as e:
        logger.error(f"Error deactivating blacklist mode: {str(e)}", exc_info=True)
        return False

def main():
    """
    Main function to set up the blacklist-based bandwidth limiting
    """
    logger.info("Running blacklist_bandwidth main function")
    # Setup traffic control
    result = activate_blacklist_mode()
    logger.info(f"Blacklist mode activation result: {result}")
    
if __name__ == "__main__":
    main() 