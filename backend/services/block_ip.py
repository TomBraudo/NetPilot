from utils.ssh_client import ssh_manager
from utils.logging_config import get_logger
from utils.response_helpers import success
from db.device_repository import get_device_by_ip, get_device_by_mac

logger = get_logger('services.block_ip')

def block_device_by_ip(target_ip):
    """
    Blocks a device by IP address (translates IP to MAC and blocks it)
    """
    try:
        # Get device info from database
        device = get_device_by_ip(target_ip)
        if not device or not device.get('mac'):
            raise ValueError(f"IP {target_ip} not found in network.")

        commands_block = [
            "uci add_list wireless.@wifi-iface[1].maclist='{mac_address}'",
            "uci set wireless.@wifi-iface[1].macfilter='deny'",
            "uci commit wireless",
            "wifi"
        ]

        # Block the MAC address
        for cmd in commands_block:
            cmd = cmd.format(mac_address=device['mac'])
            output, error = ssh_manager.execute_command(cmd)
            if error:
                raise Exception(f"Failed to execute command: {cmd}, Error: {error}")

        return success(message=f"Device with IP {target_ip} (MAC {device['mac']}) is blocked.")
    except Exception as e:
        logger.error(f"Error blocking device: {str(e)}", exc_info=True)
        raise

def unblock_device_by_ip(target_ip):
    """
    Unblocks a device by IP address (translates IP to MAC and unblocks it)
    """
    try:
        # Get device info from database
        device = get_device_by_ip(target_ip)
        if not device or not device.get('mac'):
            raise ValueError(f"IP {target_ip} not found in network.")

        commands_unblock = [
            "uci del_list wireless.@wifi-iface[1].maclist='{mac_address}'",
            "uci commit wireless",
            "wifi"
        ]

        # Unblock the MAC address
        for cmd in commands_unblock:
            cmd = cmd.format(mac_address=device['mac'])
            output, error = ssh_manager.execute_command(cmd)
            if error:
                raise Exception(f"Failed to execute command: {cmd}, Error: {error}")

        return success(message=f"Device with IP {target_ip} (MAC {device['mac']}) is unblocked.")
    except Exception as e:
        logger.error(f"Error unblocking device: {str(e)}", exc_info=True)
        raise

def get_blocked_devices():
    """
    Gets a list of all currently blocked devices
    """
    try:
        # Get the list of blocked MAC addresses
        output, error = ssh_manager.execute_command("uci get wireless.@wifi-iface[1].maclist")
        if error:
            raise Exception(f"Failed to get blocked devices: {error}")

        # Parse the output
        blocked_macs = output.strip().split() if output.strip() else []
        
        # Get device info for each blocked MAC
        blocked_devices = []
        for mac in blocked_macs:
            device = get_device_by_mac(mac)
            if device:
                blocked_devices.append({
                    "ip": device.get("ip", "Unknown"),
                    "mac": mac,
                    "hostname": device.get("hostname", "Unknown")
                })

        return success(data=blocked_devices)
    except Exception as e:
        logger.error(f"Error getting blocked devices: {str(e)}", exc_info=True)
        raise
