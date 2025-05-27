#!/usr/bin/env python3
from utils.ssh_client import ssh_manager
from utils.response_helpers import success, error
from db.tinydb_client import db_client
from utils.path_utils import get_data_folder
from utils.logging_config import get_logger
import os
import json
from tinydb import Query

# Get logger for whitelist bandwidth service
logger = get_logger('whitelist.bandwidth')

# Get the whitelist config file path
whitelist_config_path = os.path.join(get_data_folder(), "whitelist_config.json")

def load_whitelist_config():
    """
    Loads the whitelist configuration from the config file
    
    Returns:
        dict: The whitelist configuration
    """
    with open(whitelist_config_path, 'r') as f:
        return json.load(f)

# Load initial config
whitelist_config = load_whitelist_config()

# Default settings
Wan_Interface = whitelist_config.get('Wan_Interface', "eth0")  # Default interface

def get_limit_rate():
    """
    Gets the current limit rate from the config file
    
    Returns:
        str: The current limit rate
    """
    config = load_whitelist_config()
    return config.get('Limit_Rate', "50mbit")

def get_full_rate():
    """
    Gets the current full rate from the config file
    
    Returns:
        str: The current full rate
    """
    config = load_whitelist_config()
    return config.get('Full_Rate', "1000mbit")

def update_whitelist_interface(interface):
    """
    Updates the whitelist interface in the whitelist config
    
    Returns:
        str: The interface that was set
        
    Raises:
        Exception: If there was an error updating the config
    """
    try:
        whitelist_config['Wan_Interface'] = interface
        with open(whitelist_config_path, 'w') as f:
            json.dump(whitelist_config, f)
        logger.info(f"Updated whitelist interface to {interface}")
        return interface
    except Exception as e:
        logger.error(f"Error updating whitelist interface: {str(e)}", exc_info=True)
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

def update_whitelist_limit_rate(rate):
    """
    Updates the whitelist limit rate in the whitelist config and reapplies the traffic control
    
    Args:
        rate: The rate value (can be number or string with/without units)
    
    Returns:
        str: The rate that was set
        
    Raises:
        Exception: If there was an error updating the config
    """
    try:
        formatted_rate = format_rate(rate)
        whitelist_config['Limit_Rate'] = formatted_rate
        with open(whitelist_config_path, 'w') as f:
            json.dump(whitelist_config, f)
        logger.info(f"Updated whitelist limit rate to {formatted_rate}")
        
        # Reapply traffic control with new rate
        setup_tc_with_iptables()
        
        return formatted_rate
    except Exception as e:
        logger.error(f"Error updating whitelist limit rate: {str(e)}", exc_info=True)
        raise

def update_whitelist_full_rate(rate):
    """
    Updates the whitelist full rate in the whitelist config and reapplies the traffic control
    
    Args:
        rate: The rate value (can be number or string with/without units)
    
    Returns:
        str: The rate that was set
        
    Raises:
        Exception: If there was an error updating the config
    """
    try:
        formatted_rate = format_rate(rate)
        whitelist_config['Full_Rate'] = formatted_rate
        with open(whitelist_config_path, 'w') as f:
            json.dump(whitelist_config, f)
        logger.info(f"Updated whitelist full rate to {formatted_rate}")
        
        # Reapply traffic control with new rate
        setup_tc_with_iptables()
        
        return formatted_rate
    except Exception as e:
        logger.error(f"Error updating whitelist full rate: {str(e)}", exc_info=True)
        raise

def get_whitelist_ips():
    """
    Retrieves the whitelist of IPs from the TinyDB database
    
    Returns:
        list: List of IP addresses
    """
    try:
        # Get whitelist entries directly from the client
        whitelist_entries = db_client.bandwidth_whitelist.all()
        
        # Extract IPs from entries
        whitelist_ips = [entry.get('ip') for entry in whitelist_entries if entry.get('ip')]
        
        if not whitelist_ips:
            logger.warning("No IPs found in whitelist")
            return []
            
        logger.info(f"Found {len(whitelist_ips)} IPs in whitelist")
        return whitelist_ips
    except Exception as e:
        logger.error(f"Error retrieving whitelist: {str(e)}", exc_info=True)
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

def setup_tc_on_interface(interface, whitelist_ips, limit_rate=None, full_rate=None):
    """
    Sets up traffic control on a specific interface
    
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
        run_command(f"tc qdisc add dev {interface} root handle 1: htb default 10")

        # Class 10: default for limited devices
        run_command(f"tc class add dev {interface} parent 1: classid 1:10 htb rate {limit_rate}")

        # Class 1: full bandwidth for whitelisted IPs
        run_command(f"tc class add dev {interface} parent 1: classid 1:1 htb rate {full_rate} ceil {full_rate}")

        # tc filter: mark 99 => full bandwidth
        run_command(f"tc filter add dev {interface} parent 1: protocol ip handle 99 fw flowid 1:1")
        
        logger.info(f"Traffic control setup completed for interface {interface}")
        return True
    except Exception as e:
        logger.error(f"Error setting up TC on interface {interface}: {str(e)}", exc_info=True)
        return False

def setup_tc_with_iptables(whitelist_ips=None, wan_iface=Wan_Interface, limit_rate=None, full_rate=None):
    """
    Sets up traffic control with iptables to limit bandwidth for non-whitelisted IPs
    on all relevant interfaces
    
    Returns:
        bool: True if successful
    """
    try:
        # If no whitelist_ips are provided, get them from the database
        if whitelist_ips is None:
            whitelist_ips = get_whitelist_ips()
        
        logger.info(f"Whitelist contains {len(whitelist_ips)} IPs")
        
        # Get all network interfaces
        interfaces = get_all_network_interfaces()
        
        # Clear previous iptables rules
        run_command("iptables -t mangle -F")
        
        # iptables mangle rules: mark whitelist with mark 99
        for ip in whitelist_ips:
            run_command(f"iptables -t mangle -A PREROUTING -s {ip} -j MARK --set-mark 99")
            run_command(f"iptables -t mangle -A POSTROUTING -d {ip} -j MARK --set-mark 99")
        
        # Setup traffic control on each interface
        interface_results = []
        for interface in interfaces:
            result = setup_tc_on_interface(interface, whitelist_ips, limit_rate, full_rate)
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

def add_single_device_to_tc(ip, name=None, description=None):
    """
    Adds a single device to traffic control rules
    
    Args:
        ip (str): IP address of the device
        name (str, optional): Name of the device
        description (str, optional): Description of the device
    
    Returns:
        bool: True if successful
        
    Raises:
        Exception: If there was an error adding the device
    """
    try:
        logger.info(f"Adding device {ip} to traffic control rules")
        
        # Get MAC address from database
        mac = get_mac_from_ip(ip)
        if not mac:
            raise ValueError(f"Device with IP {ip} not found in network")
        
        # 1. Add to database first
        from datetime import datetime
        entry = {
            'ip': ip,
            'mac': mac,
            'name': name or f"Device-{ip}",
            'description': description or "",
            'added_at': str(datetime.now())
        }
        db_client.bandwidth_whitelist.insert(entry)
        
        # 2. Ensure whitelist mode is activated
        from services.bandwidth_mode import set_mode
        set_mode('whitelist')
        
        # 3. Add iptables marking rules
        run_command(f"iptables -t mangle -A PREROUTING -s {ip} -j MARK --set-mark 99")
        run_command(f"iptables -t mangle -A POSTROUTING -d {ip} -j MARK --set-mark 99")
        
        # 4. Get all network interfaces
        interfaces = get_all_network_interfaces()
        
        # 5. Ensure tc filter is set up correctly on each interface
        for interface in interfaces:
            # Check if the interface has traffic control set up
            output, _ = run_command(f"tc qdisc show dev {interface}")
            if "htb" in output:
                # Ensure the filter is properly configured
                run_command(f"tc filter add dev {interface} parent 1: protocol ip handle 99 fw flowid 1:1")
            else:
                # If no traffic control is set up, set it up for this interface
                setup_tc_on_interface(interface, [ip])
        
        logger.info(f"Device {ip} (MAC: {mac}) successfully added to traffic control on all interfaces")
        return True
    except Exception as e:
        logger.error(f"Error adding device to traffic control: {str(e)}", exc_info=True)
        raise

def remove_single_device_from_tc(ip):
    """
    Removes a single device from traffic control rules
    
    Args:
        ip (str): IP address to remove
    
    Returns:
        bool: True if successful
        
    Raises:
        Exception: If there was an error removing the device
    """
    try:
        logger.info(f"Removing device {ip} from traffic control rules")
        
        # Get MAC address from database
        mac = get_mac_from_ip(ip)
        if not mac:
            raise ValueError(f"Device with IP {ip} not found in network")
        
        # 1. Remove iptables marking rules
        run_command(f"iptables -t mangle -D PREROUTING -s {ip} -j MARK --set-mark 99 2>/dev/null || true")
        run_command(f"iptables -t mangle -D POSTROUTING -d {ip} -j MARK --set-mark 99 2>/dev/null || true")
        
        # No need to update tc filters on interfaces since they operate on mark 99,
        # and we've just removed the marking for this IP
        
        logger.info(f"Device {ip} (MAC: {mac}) successfully removed from traffic control")
        return True
    except Exception as e:
        logger.error(f"Error removing device from traffic control: {str(e)}", exc_info=True)
        raise

def activate_whitelist_mode():
    """
    Activates whitelist mode on the router, setting up traffic control
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Activating whitelist mode on router")
        # Setup traffic control
        whitelist_ips = get_whitelist_ips()
        result = setup_tc_with_iptables(whitelist_ips)
        logger.info(f"Whitelist mode activation {'succeeded' if result else 'failed'}")
        return result
    except Exception as e:
        logger.error(f"Error activating whitelist mode: {str(e)}", exc_info=True)
        return False

def deactivate_whitelist_mode():
    """
    Deactivates whitelist mode on the router, removing all traffic control rules
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Deactivating whitelist mode on router")
        # Get all network interfaces
        interfaces = get_all_network_interfaces()
        
        # Remove traffic control from each interface
        for interface in interfaces:
            run_command(f"tc qdisc del dev {interface} root 2>/dev/null || true")
        
        # Clear all iptables rules
        run_command("iptables -t mangle -F")
        
        logger.info("Whitelist mode deactivated on router")
        return True
    except Exception as e:
        logger.error(f"Error deactivating whitelist mode: {str(e)}", exc_info=True)
        return False

def remove_from_whitelist(ip):
    """
    Removes a device from the whitelist database and traffic control if active
    
    Args:
        ip (str): IP address to remove
        
    Returns:
        bool: True if successful
        
    Raises:
        ValueError: If the IP was not found in whitelist
        Exception: If there was an error removing the device
    """
    try:
        # Get MAC address from database
        mac = get_mac_from_ip(ip)
        if not mac:
            raise ValueError(f"Device with IP {ip} not found in network")
            
        # Remove from database
        Device = Query()
        removed = db_client.bandwidth_whitelist.remove((Device.ip == ip) & (Device.mac == mac))
        
        if not removed:
            logger.warning(f"Attempted to remove IP {ip} that does not exist in whitelist")
            raise ValueError(f"Device with IP {ip} not found in whitelist")
            
        logger.info(f"Removed device with IP {ip} (MAC: {mac}) from whitelist")
        return True
    except Exception as e:
        logger.error(f"Error removing device from whitelist: {str(e)}", exc_info=True)
        raise

def clear_whitelist():
    """
    Clears all entries from the whitelist database and traffic control if active
    
    Returns:
        bool: True if successful
        
    Raises:
        Exception: If there was an error clearing the whitelist
    """
    try:
        logger.info("Clearing all entries from whitelist")
        
        # Clear the whitelist table
        db_client.bandwidth_whitelist.truncate()
        
        # If whitelist mode is active, clear traffic control rules
        if is_whitelist_mode():
            logger.info("Whitelist mode is active, clearing traffic control rules")
            # Clear iptables rules
            run_command("iptables -t mangle -F")
            
            # Get all network interfaces
            interfaces = get_all_network_interfaces()
            
            # Remove traffic control from each interface
            for interface in interfaces:
                run_command(f"tc qdisc del dev {interface} root 2>/dev/null || true")
        
        logger.info("Successfully cleared whitelist")
        return True
    except Exception as e:
        logger.error(f"Error clearing whitelist: {str(e)}", exc_info=True)
        raise

def main():
    """
    Main function to set up the whitelist-based bandwidth limiting
    """
    logger.info("Running whitelist_bandwidth main function")
    # Setup traffic control
    result = activate_whitelist_mode()
    logger.info(f"Whitelist mode activation result: {result}")
    
if __name__ == "__main__":
    main()