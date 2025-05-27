from utils.logging_config import get_logger
from utils.ssh_client import ssh_manager
from utils.response_helpers import success, error
from utils.config_manager import config_manager
from db.device_repository import get_mac_from_ip
from db.device_groups_repository import get_rules_for_device, set_rule_for_device, remove_rule_from_device
from services.mode_state_service import get_current_mode_value, set_current_mode_value
from db.tinydb_client import db_client
from db.whitelist_management import add_to_whitelist, remove_from_whitelist, get_whitelist
from services.reset_rules import reset_all_tc_rules
import os
import json
from tinydb import Query

logger = get_logger('services.whitelist')

# Get the whitelist table directly
whitelist_table = db_client.bandwidth_whitelist
Device = Query()

def get_whitelist_devices():
    """Get all devices in the whitelist"""
    try:
        # Get devices from the whitelist table
        devices = get_whitelist()
        
        # Format the response
        formatted_devices = []
        for device in devices:
            formatted_devices.append({
                "ip": device.get("ip"),
                "mac": device.get("mac"),
                "hostname": device.get("name", "Unknown"),
                "last_seen": device.get("added_at")
            })
            
        return success(data=formatted_devices)
    except Exception as e:
        logger.error(f"Error getting whitelist: {str(e)}", exc_info=True)
        raise

def add_device_to_whitelist(ip):
    """Add a device to the whitelist"""
    try:
        # Add to whitelist table
        device = add_to_whitelist(ip)
        
        # Set rule for device
        set_rule_for_device(device["mac"], ip, "whitelist", True)
        
        # If whitelist mode is active, update TC rules
        if get_current_mode_value() == 'whitelist':
            setup_tc_with_iptables()
        
        return success(message=f"Device {ip} added to whitelist")
    except Exception as e:
        logger.error(f"Error adding device to whitelist: {str(e)}", exc_info=True)
        raise

def remove_device_from_whitelist(ip):
    """Remove a device from the whitelist"""
    try:
        # Get device info before removing
        device = whitelist_table.get(Device.ip == ip)
        if not device:
            raise ValueError(f"Device with IP {ip} not found in whitelist")
        
        # Remove from whitelist table
        remove_from_whitelist(ip)
        
        # Remove rule for device
        remove_rule_from_device(device["mac"], ip, "whitelist")
        
        # If whitelist mode is active, update TC rules
        if get_current_mode_value() == 'whitelist':
            setup_tc_with_iptables()
        
        return success(message=f"Device {ip} removed from whitelist")
    except Exception as e:
        logger.error(f"Error removing device from whitelist: {str(e)}", exc_info=True)
        raise

def clear_whitelist():
    """Clear all devices from the whitelist"""
    try:
        devices = get_whitelist()
        for device in devices:
            remove_device_from_whitelist(device["ip"])
        return success(message="Whitelist cleared")
    except Exception as e:
        logger.error(f"Error clearing whitelist: {str(e)}", exc_info=True)
        raise

def get_whitelist_limit_rate():
    """Get the current whitelist bandwidth limit rate"""
    try:
        config = config_manager.load_config('whitelist')
        return success(data={"rate": config.get('Limit_Rate', "50mbit")})
    except Exception as e:
        logger.error(f"Error getting whitelist limit rate: {str(e)}", exc_info=True)
        raise

def set_whitelist_limit_rate(rate):
    """Set the whitelist bandwidth limit rate"""
    try:
        config = config_manager.load_config('whitelist')
        config['Limit_Rate'] = format_rate(rate)
        config_manager.save_config('whitelist', config)
        logger.info(f"Updated whitelist limit rate to {config['Limit_Rate']}")
        
        # Check mode using the new service
        if get_current_mode_value() == 'whitelist':
            setup_tc_with_iptables()
        
        return success(data={"rate": config['Limit_Rate']})
    except Exception as e:
        logger.error(f"Error setting whitelist limit rate: {str(e)}", exc_info=True)
        raise

def get_whitelist_full_rate():
    """Get the current whitelist full bandwidth rate"""
    try:
        config = config_manager.load_config('whitelist')
        return success(data={"rate": config.get('Full_Rate', "100mbit")})
    except Exception as e:
        logger.error(f"Error getting whitelist full rate: {str(e)}", exc_info=True)
        raise

def set_whitelist_full_rate(rate):
    """Set the whitelist full bandwidth rate"""
    try:
        config = config_manager.load_config('whitelist')
        config['Full_Rate'] = format_rate(rate)
        config_manager.save_config('whitelist', config)
        logger.info(f"Updated whitelist full rate to {config['Full_Rate']}")
        
        # Check mode using the new service
        if get_current_mode_value() == 'whitelist':
            setup_tc_with_iptables()
        
        return success(data={"rate": config['Full_Rate']})
    except Exception as e:
        logger.error(f"Error setting whitelist full rate: {str(e)}", exc_info=True)
        raise

def activate_whitelist_mode():
    """Activate whitelist mode"""
    try:
        # Use the new service to set the mode
        set_current_mode_value('whitelist')
        setup_tc_with_iptables()
        return success(message="Whitelist mode activated")
    except Exception as e:
        logger.error(f"Error activating whitelist mode: {str(e)}", exc_info=True)
        raise

def deactivate_whitelist_mode():
    """Deactivate whitelist mode"""
    try:
        # Perform cleanup first
        reset_all_tc_rules() 
        # Then set mode to none using the new service
        set_current_mode_value('none')
        return success(message="Whitelist mode deactivated")
    except Exception as e:
        logger.error(f"Error deactivating whitelist mode: {str(e)}", exc_info=True)
        raise

def is_whitelist_mode_internal():
    """Check if whitelist mode is active (internal use)"""
    return get_current_mode_value() == 'whitelist'

def is_whitelist_mode():
    """Check if whitelist mode is active (API response)"""
    try:
        is_active = get_current_mode_value() == 'whitelist'
        return success(data={"active": is_active})
    except Exception as e:
        logger.error(f"Error checking whitelist mode: {str(e)}", exc_info=True)
        raise

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
        raise Exception(f"Failed to get network interfaces: {error}")
    return [iface for iface in output.split() if iface not in ['lo']]

def run_command(cmd):
    """Run a command on the router"""
    output, error = ssh_manager.execute_command(cmd)
    if error:
        logger.error(f"Command failed: {cmd}, Error: {error}")
        raise Exception(f"Command failed: {cmd}, Error: {error}")
    return True

def setup_tc_on_interface(interface, whitelist_ips, limit_rate=None, full_rate=None):
    """Set up traffic control on a specific interface"""
    try:
        # Get current rates if not specified
        if limit_rate is None:
            limit_rate = get_whitelist_limit_rate()
        if full_rate is None:
            full_rate = get_whitelist_full_rate()
            
        logger.info(f"Setting up traffic control on {interface} with limit {limit_rate}")
        
        # Clear previous rules for this interface
        run_command(f"tc qdisc del dev {interface} root 2>/dev/null || true")

        # Add root HTB qdisc
        run_command(f"tc qdisc add dev {interface} root handle 1: htb default 10")

        # Class 1: full bandwidth for whitelisted IPs
        run_command(f"tc class add dev {interface} parent 1: classid 1:1 htb rate {full_rate}")

        # Class 10: limited bandwidth for non-whitelisted IPs
        run_command(f"tc class add dev {interface} parent 1: classid 1:10 htb rate {limit_rate}")

        # tc filter: mark 99 => limited bandwidth
        run_command(f"tc filter add dev {interface} parent 1: protocol ip handle 99 fw flowid 1:10")
        
        logger.info(f"Traffic control setup completed for interface {interface}")
        return True
    except Exception as e:
        logger.error(f"Error setting up TC on interface {interface}: {str(e)}", exc_info=True)
        return False

def setup_tc_with_iptables(whitelist_ips=None, limit_rate=None, full_rate=None):
    """Set up traffic control with iptables"""
    try:
        # If no whitelist_ips are provided, get them from the database
        if whitelist_ips is None:
            result = get_whitelist_devices()
            if result.get("status") == "success":
                whitelist_ips = [device['ip'] for device in result.get("data", [])]
            else:
                whitelist_ips = []
        
        logger.info(f"Whitelist contains {len(whitelist_ips)} IPs")
        
        # Get all network interfaces
        interfaces = get_all_network_interfaces()
        
        # Clear previous iptables rules
        run_command("iptables -t mangle -F")
        
        # iptables mangle rules: mark non-whitelist with mark 99
        run_command("iptables -t mangle -A PREROUTING -j MARK --set-mark 99")
        run_command("iptables -t mangle -A POSTROUTING -j MARK --set-mark 99")
        
        # Remove mark for whitelisted IPs
        for ip in whitelist_ips:
            run_command(f"iptables -t mangle -A PREROUTING -s {ip} -j MARK --set-mark 0")
            run_command(f"iptables -t mangle -A POSTROUTING -d {ip} -j MARK --set-mark 0")
        
        # Setup traffic control on each interface
        interface_results = []
        for interface in interfaces:
            result = setup_tc_on_interface(interface, whitelist_ips, limit_rate, full_rate)
            interface_results.append(result)
        
        # Return True only if all interfaces were successfully configured
        success = all(interface_results)
        if success:
            logger.info("Traffic control with iptables set up successfully on all interfaces")
            return success(message="Traffic control with iptables set up successfully")
        else:
            logger.warning("Traffic control setup failed on some interfaces")
            raise Exception("Traffic control setup failed on some interfaces")
    except Exception as e:
        logger.error(f"Error setting up TC with iptables: {str(e)}", exc_info=True)
        raise 