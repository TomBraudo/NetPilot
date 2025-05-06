import logging
from utils.ssh_client import ssh_manager
from utils.response_helpers import success, error
from db.config_repository import set_system_config, get_system_config
import ipaddress
from db.device_repository import mark_device_as_protected

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ADMIN_DEVICE_KEY = "admin_device_mac"

def register_admin_device(ip_address=None, mac_address=None):
    """
    Register the current device as an admin device that should never be blocked.
    If no IP or MAC is provided, attempts to detect it from the request.
    
    Args:
        ip_address: IP address of admin device (optional)
        mac_address: MAC address of admin device (optional)
        
    Returns:
        Dictionary with success/error status and message
    """
    try:
        # If MAC is provided directly, use it
        if mac_address:
            admin_mac = mac_address.lower()
        # If IP is provided, look up the MAC
        elif ip_address:
            admin_mac = get_mac_from_ip(ip_address)
            if not admin_mac:
                return error(f"Could not find MAC address for IP {ip_address}")
        else:
            return error("Must provide either IP address or MAC address")
            
        # Save the admin MAC
        if set_system_config(ADMIN_DEVICE_KEY, admin_mac):
            # Ensure the admin device is protected in all filtering mechanisms
            ensure_admin_device_protected(admin_mac)
            return success(f"Device {admin_mac} registered as admin device and protected")
        else:
            return error("Failed to register admin device")
            
    except Exception as e:
        logger.error(f"Error registering admin device: {str(e)}")
        return error(f"Error registering admin device: {str(e)}")

def get_admin_device_mac():
    """
    Get the MAC address of the registered admin device.
    
    Returns:
        str: MAC address or None if not registered
    """
    return get_system_config(ADMIN_DEVICE_KEY, None)

def ensure_admin_device_protected(mac_address=None):
    """
    Ensure admin device is protected from blocking.
    If mac_address is provided, use that as admin MAC.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get admin MAC if not provided
        admin_mac = mac_address or get_admin_device_mac()
        
        if not admin_mac:
            logger.warning("No admin device registered, cannot protect")
            return False
        
        # Protect admin in WiFi (not in deny list)
        wifi_commands = []
        
        get_wifi_ifaces = "uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1"
        ifaces_output, _ = ssh_manager.execute_command(get_wifi_ifaces)
        
        if ifaces_output:
            for iface in ifaces_output.splitlines():
                if iface and iface.strip():
                    # In blacklist mode - ensure admin is NOT in deny list
                    wifi_commands.append(f"uci set wireless.{iface}.macfilter='deny'")
                    wifi_commands.append(f"uci del_list wireless.{iface}.maclist='{admin_mac}' 2>/dev/null")
        
        # Apply WiFi commands
        for cmd in wifi_commands:
            _, err = ssh_manager.execute_command(cmd)
            if err:
                logger.error(f"Error protecting admin in WiFi: {err}")
        
        # Remove any existing block rules for admin MAC
        block_rule_check = f"uci show firewall | grep -i 'NetPilot Block' | grep -i '{admin_mac}'"
        block_rule_output, _ = ssh_manager.execute_command(block_rule_check)
        
        if block_rule_output:
            # Parse rule section from output and delete it
            for line in block_rule_output.splitlines():
                if "=" in line:
                    try:
                        rule_section = line.split(".")[1].split(".")[0]
                        ssh_manager.execute_command(f"uci delete firewall.{rule_section}")
                    except:
                        logger.error(f"Error parsing rule section from: {line}")
        
        # Apply all changes
        ssh_manager.execute_command("uci commit wireless")
        ssh_manager.execute_command("uci commit firewall")
        ssh_manager.execute_command("wifi reload")
        ssh_manager.execute_command("/etc/init.d/firewall reload")
        
        logger.info(f"Admin device {admin_mac} is now protected")
        return True
    except Exception as e:
        logger.error(f"Error protecting admin device: {str(e)}")
        return False

def get_mac_from_ip(ip_address):
    """
    Get MAC address for an IP address using ARP table.
    
    Args:
        ip_address: IP address to look up
        
    Returns:
        str: MAC address or None if not found
    """
    try:
        # Check if IP is valid
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            logger.error(f"Invalid IP address: {ip_address}")
            return None
            
        # Try to get MAC from ARP table
        arp_cmd = f"ip neigh show | grep '{ip_address}' | awk '{{print $5}}'"
        mac_output, _ = ssh_manager.execute_command(arp_cmd)
        
        if mac_output and len(mac_output.strip()) > 0:
            return mac_output.strip().lower()
            
        # Try alternative - DHCP leases
        dhcp_cmd = f"cat /tmp/dhcp.leases | grep '{ip_address}' | awk '{{print $2}}'"
        dhcp_output, _ = ssh_manager.execute_command(dhcp_cmd)
        
        if dhcp_output and len(dhcp_output.strip()) > 0:
            return dhcp_output.strip().lower()
            
        # If still not found, ping the IP to update ARP table and try again
        ping_cmd = f"ping -c 1 -W 1 {ip_address} >/dev/null 2>&1"
        ssh_manager.execute_command(ping_cmd)
        
        # Try ARP again
        mac_output, _ = ssh_manager.execute_command(arp_cmd)
        
        if mac_output and len(mac_output.strip()) > 0:
            return mac_output.strip().lower()
            
        return None
    except Exception as e:
        logger.error(f"Error getting MAC from IP: {str(e)}")
        return None 