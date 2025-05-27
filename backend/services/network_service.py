from utils.logging_config import get_logger
from services.block_ip import block_device_by_ip, unblock_device_by_ip, get_blocked_devices
from services.reset_rules import reset_all_rules, reset_all_tc_rules
from services.network_scanner import scan_network
from services.router_scanner import scan_network_via_router
from services.speed_test import run_ookla_speedtest
from utils.ssh_client import ssh_manager
from db.device_repository import get_mac_from_ip
from db.device_groups_repository import set_rule_for_device, remove_rule_from_device
from utils.response_helpers import success

logger = get_logger('services.network')

def get_blocked_devices_list():
    """Get all currently blocked devices"""
    try:
        devices = get_blocked_devices()
        return success(data=devices)
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

def block_device(ip):
    """Block a device by IP"""
    try:
        block_device_by_ip(ip)
        return success(message=f"Device {ip} blocked successfully")
    except Exception as e:
        logger.error(f"Error blocking device: {str(e)}", exc_info=True)
        raise

def unblock_device(ip):
    """Unblock a device by IP"""
    try:
        unblock_device_by_ip(ip)
        return success(message=f"Device {ip} unblocked successfully")
    except Exception as e:
        logger.error(f"Error unblocking device: {str(e)}", exc_info=True)
        raise

def reset_network_rules():
    """Reset all network rules"""
    try:
        reset_all_rules()
        reset_all_tc_rules()
        return success(message="Network rules reset successfully")
    except Exception as e:
        logger.error(f"Error resetting network rules: {str(e)}", exc_info=True)
        raise 