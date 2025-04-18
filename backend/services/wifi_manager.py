import time
from utils.ssh_client import ssh_manager
from utils.response_helpers import success, error

def enable_wifi():
    """
    Enables WiFi on the OpenWrt router with default settings.
    Returns success or error message.
    """
    try:
        # Check if WiFi is already enabled
        status_cmd = "uci show wireless.@wifi-device[0].disabled"
        status_output, status_error = ssh_manager.execute_command(status_cmd)
        
        if status_error:
            return error(f"Failed to check WiFi status: {status_error}")
        
        # If WiFi is already enabled, just return success
        if "disabled='0'" in status_output:
            return success("WiFi is already enabled")
            
        # Enable the physical radio device (usually radio0)
        commands = [
            "uci set wireless.@wifi-device[0].disabled='0'",
            "uci set wireless.@wifi-iface[0].disabled='0'",
            "uci commit wireless",
            "wifi"
        ]
        
        for cmd in commands:
            output, err = ssh_manager.execute_command(cmd)
            if err:
                return error(f"Failed to enable WiFi: {err}")
                
        # Wait for WiFi to initialize
        time.sleep(2)
        
        # Get the current SSID
        ssid_cmd = "uci get wireless.@wifi-iface[0].ssid"
        ssid_output, ssid_error = ssh_manager.execute_command(ssid_cmd)
        
        if ssid_error:
            return success("WiFi enabled successfully, but couldn't retrieve SSID")
            
        return success(f"WiFi enabled successfully with SSID: {ssid_output}")
        
    except Exception as e:
        return error(f"Error enabling WiFi: {str(e)}")

def change_wifi_password(password, interface_num=0):
    """
    Changes the WiFi password for the specified interface.
    
    Args:
        password: New password to set
        interface_num: WiFi interface number (default 0 for primary interface)
        
    Returns:
        Success or error message
    """
    if not password or len(password) < 8:
        return error("Password must be at least 8 characters")
        
    try:
        # Set the new password
        commands = [
            f"uci set wireless.@wifi-iface[{interface_num}].key='{password}'",
            f"uci set wireless.@wifi-iface[{interface_num}].encryption='psk2'",
            "uci commit wireless",
            "wifi"
        ]
        
        for cmd in commands:
            output, err = ssh_manager.execute_command(cmd)
            if err:
                return error(f"Failed to change WiFi password: {err}")
                
        # Get the current SSID for the response
        ssid_cmd = f"uci get wireless.@wifi-iface[{interface_num}].ssid"
        ssid_output, ssid_error = ssh_manager.execute_command(ssid_cmd)
        
        if ssid_error:
            return success("WiFi password changed successfully")
        
        return success(f"WiFi password changed successfully for network: {ssid_output}")
        
    except Exception as e:
        return error(f"Error changing WiFi password: {str(e)}")

def get_wifi_status():
    """
    Gets the current WiFi status including SSID and enabled state.
    Returns a dictionary with status information.
    """
    try:
        # Check if radio is enabled
        enabled_cmd = "uci show wireless.@wifi-device[0].disabled"
        enabled_output, enabled_error = ssh_manager.execute_command(enabled_cmd)
        
        if enabled_error:
            return error("Failed to get WiFi status")
            
        # Get SSID
        ssid_cmd = "uci get wireless.@wifi-iface[0].ssid"
        ssid_output, ssid_error = ssh_manager.execute_command(ssid_cmd)
        
        # Get encryption type
        encryption_cmd = "uci get wireless.@wifi-iface[0].encryption"
        encryption_output, encryption_error = ssh_manager.execute_command(encryption_cmd)
        
        is_enabled = "disabled='0'" in enabled_output or "disabled=0" in enabled_output
        
        return success(data={
            "enabled": is_enabled,
            "ssid": ssid_output.strip() if not ssid_error else "Unknown",
            "encryption": encryption_output.strip() if not encryption_error else "Unknown"
        })
        
    except Exception as e:
        return error(f"Error getting WiFi status: {str(e)}")