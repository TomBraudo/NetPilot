from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager

logger = get_logger('services.wifi')
router_connection_manager = RouterConnectionManager()

def enable_wifi():
    """
    Enables WiFi on the OpenWrt router.
    """
    try:
        status_cmd = "uci show wireless.@wifi-device[0].disabled"
        status_output, status_error = router_connection_manager.execute(status_cmd)
        
        if status_error:
            return None, f"Failed to check WiFi status: {status_error}"
        
        if "disabled='0'" in status_output:
            return "WiFi is already enabled", None
            
        commands = [
            "uci set wireless.@wifi-device[0].disabled='0'",
            "uci set wireless.@wifi-iface[0].disabled='0'",
            "uci commit wireless",
            "wifi"
        ]
        
        for cmd in commands:
            _, err = router_connection_manager.execute(cmd)
            if err:
                return None, f"Failed to execute enable command: {err}"
                
        ssid_cmd = "uci get wireless.@wifi-iface[0].ssid"
        ssid_output, ssid_error = router_connection_manager.execute(ssid_cmd)
        
        if ssid_error:
            return "WiFi enabled, but could not retrieve current SSID.", None
            
        return f"WiFi enabled successfully with SSID: {ssid_output.strip()}", None
        
    except RuntimeError as e:
        logger.error(f"Connection error enabling WiFi: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Unexpected error enabling WiFi: {str(e)}", exc_info=True)
        return None, f"An unexpected error occurred: {str(e)}"

def change_wifi_password(password, interface_num=0):
    """
    Changes the WiFi password for the specified interface.
    """
    if not password or len(password) < 8:
        return None, "Password must be at least 8 characters"
        
    try:
        commands = [
            f"uci set wireless.@wifi-iface[{interface_num}].key='{password}'",
            f"uci set wireless.@wifi-iface[{interface_num}].encryption='psk2'",
            "uci commit wireless",
            "wifi"
        ]
        
        for cmd in commands:
            _, err = router_connection_manager.execute(cmd)
            if err:
                return None, f"Failed to execute password change command: {err}"
                
        ssid_cmd = f"uci get wireless.@wifi-iface[{interface_num}].ssid"
        ssid_output, ssid_error = router_connection_manager.execute(ssid_cmd)
        
        if ssid_error:
            return "WiFi password changed successfully.", None
        
        return f"WiFi password changed for network: {ssid_output.strip()}", None
        
    except RuntimeError as e:
        logger.error(f"Connection error changing WiFi password: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Unexpected error changing WiFi password: {str(e)}", exc_info=True)
        return None, f"An unexpected error occurred: {str(e)}"

def get_wifi_status():
    """
    Gets the current WiFi status.
    """
    try:
        enabled_cmd = "uci show wireless.@wifi-device[0].disabled"
        enabled_output, enabled_error = router_connection_manager.execute(enabled_cmd)
        if enabled_error:
            return None, f"Failed to get WiFi enabled status: {enabled_error}"
            
        ssid_cmd = "uci get wireless.@wifi-iface[0].ssid"
        ssid_output, ssid_error = router_connection_manager.execute(ssid_cmd)
        
        encryption_cmd = "uci get wireless.@wifi-iface[0].encryption"
        encryption_output, encryption_error = router_connection_manager.execute(encryption_cmd)
        
        is_enabled = "disabled='0'" in enabled_output or "disabled=0" in enabled_output
        
        status_data = {
            "enabled": is_enabled,
            "ssid": ssid_output.strip() if not ssid_error else "Unknown",
            "encryption": encryption_output.strip() if not encryption_error else "Unknown"
        }
        return status_data, None
        
    except RuntimeError as e:
        logger.error(f"Connection error getting WiFi status: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Unexpected error getting WiFi status: {str(e)}", exc_info=True)
        return None, f"An unexpected error occurred: {str(e)}"

def change_wifi_ssid(ssid, interface_num=0):
    """
    Changes the WiFi SSID for the specified interface.
    """
    if not ssid:
        return None, "SSID cannot be empty"
        
    try:
        commands = [
            f"uci set wireless.@wifi-iface[{interface_num}].ssid='{ssid}'",
            "uci commit wireless",
            "wifi"
        ]
        
        for cmd in commands:
            _, err = router_connection_manager.execute(cmd)
            if err:
                return None, f"Failed to execute SSID change command: {err}"
                
        return f"WiFi SSID changed successfully to: {ssid}", None
        
    except RuntimeError as e:
        logger.error(f"Connection error changing WiFi SSID: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Unexpected error changing WiFi SSID: {str(e)}", exc_info=True)
        return None, f"An unexpected error occurred: {str(e)}"

def get_wifi_ssid(interface_num=0):
    """
    Gets the current WiFi SSID for the specified interface.
    """
    try:
        ssid_cmd = f"uci get wireless.@wifi-iface[{interface_num}].ssid"
        ssid_output, ssid_error = router_connection_manager.execute(ssid_cmd)
        
        if ssid_error:
            return None, f"Failed to get SSID for interface {interface_num}"
            
        return {"ssid": ssid_output.strip()}, None
        
    except RuntimeError as e:
        logger.error(f"Connection error getting WiFi SSID: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Error getting WiFi SSID: {str(e)}", exc_info=True)
        return None, f"An unexpected error occurred: {str(e)}" 