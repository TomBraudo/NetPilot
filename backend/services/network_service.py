from utils.logging_config import get_logger
from services.block_ip import block_mac_address, unblock_mac_address, get_blocked_devices
from services.reset_rules import reset_all_rules, reset_all_tc_rules
from services.network_scanner import scan_network
from services.router_scanner import scan_network_via_router
from services.speed_test import run_ookla_speedtest
from utils.ssh_client import ssh_manager
from db.device_repository import get_mac_from_ip
from db.device_groups_repository import set_rule_for_device, remove_rule_from_device

logger = get_logger('services.network')

def get_blocked_devices_list():
    """Get all currently blocked devices"""
    try:
        return get_blocked_devices()
    except Exception as e:
        logger.error(f"Error getting blocked devices: {str(e)}", exc_info=True)
        raise

def shutdown_server():
    """Gracefully shut down the server and SSH session"""
    try:
        response = reset_all_rules()
        ssh_manager.close_connection()
        return response
    except Exception as e:
        logger.error(f"Error shutting down server: {str(e)}", exc_info=True)
        raise

def perform_network_scan():
    """Perform a local network scan and return active devices"""
    try:
        return scan_network()
    except Exception as e:
        logger.error(f"Error performing network scan: {str(e)}", exc_info=True)
        raise

def perform_router_scan():
    """Perform a scan using the OpenWrt router's DHCP leases"""
    try:
        return scan_network_via_router()
    except Exception as e:
        logger.error(f"Error performing router scan: {str(e)}", exc_info=True)
        raise

def block_device(ip):
    """Block a device by IP address"""
    try:
        mac = get_mac_from_ip(ip)
        if not mac:
            raise ValueError("Device not found in network")
        
        # Set block rule using MAC
        set_rule_for_device(mac, ip, "block", True)
        return block_mac_address(mac)
    except Exception as e:
        logger.error(f"Error blocking device {ip}: {str(e)}", exc_info=True)
        raise

def unblock_device(ip):
    """Unblock a device by IP address"""
    try:
        mac = get_mac_from_ip(ip)
        if not mac:
            raise ValueError("Device not found in network")
        
        # Remove block rule using MAC
        remove_rule_from_device(mac, ip, "block")
        return unblock_mac_address(mac)
    except Exception as e:
        logger.error(f"Error unblocking device {ip}: {str(e)}", exc_info=True)
        raise

def reset_all_network_rules():
    """Reset all network rules (blocks and bandwidth limits)"""
    try:
        # Reset all traffic control rules
        reset_all_tc_rules()
        
        # Unblock all devices
        blocked_devices = get_blocked_devices()
        for device in blocked_devices.get('data', []):
            unblock_device(device['ip'])
        
        return True
    except Exception as e:
        logger.error(f"Error resetting network rules: {str(e)}", exc_info=True)
        raise

def run_speed_test():
    """Run an Ookla speed test"""
    try:
        return run_ookla_speedtest()
    except Exception as e:
        logger.error(f"Error running speed test: {str(e)}", exc_info=True)
        raise 