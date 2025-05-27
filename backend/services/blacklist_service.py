from utils.logging_config import get_logger
from utils.ssh_client import ssh_manager
from utils.response_helpers import success, error
from utils.config_manager import config_manager
from db.device_repository import get_mac_from_ip
from db.device_groups_repository import get_rules_for_device, set_rule_for_device, remove_rule_from_device
from services.bandwidth_mode import get_current_mode, set_mode
import os
import json
from tinydb import Query

logger = get_logger('services.blacklist')

def get_blacklist_devices():
    """Get all devices in the blacklist"""
    try:
        devices = get_rules_for_device("block")
        return {"status": "success", "data": devices}
    except Exception as e:
        logger.error(f"Error getting blacklist: {str(e)}", exc_info=True)
        raise

def add_device_to_blacklist(ip):
    """Add a device to the blacklist"""
    try:
        mac = get_mac_from_ip(ip)
        if not mac:
            raise ValueError(f"Device with IP {ip} not found in network")
        
        set_rule_for_device(mac, ip, "block", True)
        return {"status": "success", "message": f"Device {ip} added to blacklist"}
    except Exception as e:
        logger.error(f"Error adding device to blacklist: {str(e)}", exc_info=True)
        raise

def remove_device_from_blacklist(ip):
    """Remove a device from the blacklist"""
    try:
        mac = get_mac_from_ip(ip)
        if not mac:
            raise ValueError(f"Device with IP {ip} not found in network")
        
        remove_rule_from_device(mac, ip, "block")
        return {"status": "success", "message": f"Device {ip} removed from blacklist"}
    except Exception as e:
        logger.error(f"Error removing device from blacklist: {str(e)}", exc_info=True)
        raise

def clear_blacklist():
    """Clear all devices from the blacklist"""
    try:
        devices = get_rules_for_device("block")
        for device in devices:
            remove_rule_from_device(device["mac"], device["ip"], "block")
        return {"status": "success", "message": "Blacklist cleared"}
    except Exception as e:
        logger.error(f"Error clearing blacklist: {str(e)}", exc_info=True)
        raise

def get_blacklist_limit_rate():
    """Get the current blacklist bandwidth limit rate"""
    try:
        config = config_manager.load_config('blacklist')
        return config.get('Limit_Rate', "50mbit")
    except Exception as e:
        logger.error(f"Error getting blacklist limit rate: {str(e)}", exc_info=True)
        raise

def set_blacklist_limit_rate(rate):
    """Set the blacklist bandwidth limit rate"""
    try:
        config = config_manager.load_config('blacklist')
        config['Limit_Rate'] = format_rate(rate)
        config_manager.save_config('blacklist', config)
        logger.info(f"Updated blacklist limit rate to {config['Limit_Rate']}")
        
        if is_blacklist_mode():
            setup_tc_with_iptables()
        
        return config['Limit_Rate']
    except Exception as e:
        logger.error(f"Error setting blacklist limit rate: {str(e)}", exc_info=True)
        raise

def get_blacklist_full_rate():
    """Get the current blacklist full bandwidth rate"""
    try:
        config = config_manager.load_config('blacklist')
        return config.get('Full_Rate', "100mbit")
    except Exception as e:
        logger.error(f"Error getting blacklist full rate: {str(e)}", exc_info=True)
        raise

def set_blacklist_full_rate(rate):
    """Set the blacklist full bandwidth rate"""
    try:
        config = config_manager.load_config('blacklist')
        config['Full_Rate'] = format_rate(rate)
        config_manager.save_config('blacklist', config)
        logger.info(f"Updated blacklist full rate to {config['Full_Rate']}")
        
        if is_blacklist_mode():
            setup_tc_with_iptables()
        
        return config['Full_Rate']
    except Exception as e:
        logger.error(f"Error setting blacklist full rate: {str(e)}", exc_info=True)
        raise

def activate_blacklist_mode():
    """Activate blacklist mode"""
    try:
        # Set mode to blacklist
        set_mode('blacklist')
        
        # Setup traffic control
        if setup_tc_with_iptables():
            logger.info("Blacklist mode activated successfully")
            return True
        else:
            logger.error("Failed to activate blacklist mode")
            return False
    except Exception as e:
        logger.error(f"Error activating blacklist mode: {str(e)}", exc_info=True)
        raise

def deactivate_blacklist_mode():
    """Deactivate blacklist mode"""
    try:
        # Clear traffic control rules
        run_command("iptables -t mangle -F")
        
        # Get all network interfaces
        interfaces = get_all_network_interfaces()
        
        # Remove traffic control from each interface
        for interface in interfaces:
            run_command(f"tc qdisc del dev {interface} root 2>/dev/null || true")
        
        # Set mode to none
        set_mode('none')
        
        logger.info("Blacklist mode deactivated successfully")
        return True
    except Exception as e:
        logger.error(f"Error deactivating blacklist mode: {str(e)}", exc_info=True)
        raise

def is_blacklist_mode():
    """Check if blacklist mode is active"""
    return get_current_mode() == 'blacklist'

def format_rate(rate):
    """Format rate value to include units if not present"""
    if isinstance(rate, (int, float)):
        return f"{rate}mbit"
    return str(rate)

def get_all_network_interfaces():
    """Get all network interfaces"""
    cmd = "ls /sys/class/net/"
    output, error = ssh_manager.execute_command(cmd)
    if error:
        logger.error(f"Error getting network interfaces: {error}")
        return ["eth0"]  # Default to eth0 if command fails
    return [iface for iface in output.split() if iface not in ['lo']]

def run_command(cmd):
    """Run a command on the router"""
    output, error = ssh_manager.execute_command(cmd)
    if error:
        logger.error(f"Command failed: {cmd}, Error: {error}")
        return False
    return True

def setup_tc_on_interface(interface, blacklist_ips, limit_rate=None, full_rate=None):
    """Set up traffic control on a specific interface"""
    try:
        # Get current rates if not specified
        if limit_rate is None:
            limit_rate = get_blacklist_limit_rate()
        if full_rate is None:
            full_rate = get_blacklist_full_rate()
            
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

def setup_tc_with_iptables(blacklist_ips=None, limit_rate=None, full_rate=None):
    """Set up traffic control with iptables"""
    try:
        # If no blacklist_ips are provided, get them from the database
        if blacklist_ips is None:
            blacklist_ips = [device['ip'] for device in get_blacklist_devices()]
        
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