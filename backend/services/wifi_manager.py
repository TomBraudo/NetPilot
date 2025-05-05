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

def change_wifi_name(new_name, adapter_id="radio0"):
    """
    Changes the name of the specified WiFi adapter.
    
    Args:
        new_name: New name to set for the WiFi adapter
        adapter_id: ID of the adapter to change (default is "radio0")
        
    Returns:
        Success or error message
    """
    if not new_name:
        return error("Missing WiFi adapter name")
    
    # Validate adapter exists
    try:
        # Check if the adapter exists
        check_cmd = f"uci show wireless.{adapter_id}"
        check_output, check_error = ssh_manager.execute_command(check_cmd)
        
        if check_error or not check_output:
            return error(f"WiFi adapter '{adapter_id}' not found")
        
        # Set the WiFi interface name (SSID)
        commands = [
            f"uci set wireless.{adapter_id}.name='{new_name}'",
            "uci commit wireless",
            "wifi reload"
        ]
        
        for cmd in commands:
            output, err = ssh_manager.execute_command(cmd)
            if err:
                return error(f"Failed to change WiFi adapter name: {err}")
        
        # Wait for WiFi to reinitialize
        time.sleep(2)
        
        return success(f"WiFi adapter name changed to '{new_name}'")
        
    except Exception as e:
        return error(f"Error changing WiFi adapter name: {str(e)}")

def get_wifi_adapters():
    """
    Gets a list of all WiFi adapters in the router.
    
    Returns:
        Dictionary with success/error status and list of adapters
    """
    try:
        # Get all wifi-device sections
        cmd = "uci show wireless | grep wifi-device"
        output, err = ssh_manager.execute_command(cmd)
        
        if err:
            return error(f"Failed to get WiFi adapters: {err}")
        
        adapters = []
        for line in output.splitlines():
            if "=" in line:
                adapter_id = line.split('.')[1].split('=')[0]
                
                # Get adapter details
                disabled_cmd = f"uci show wireless.{adapter_id}.disabled"
                disabled_output, _ = ssh_manager.execute_command(disabled_cmd)
                
                is_disabled = "1" in disabled_output if disabled_output else False
                
                # Try to get the name if it exists
                name_cmd = f"uci get wireless.{adapter_id}.name 2>/dev/null || echo '{adapter_id}'"
                name_output, _ = ssh_manager.execute_command(name_cmd)
                
                adapters.append({
                    "id": adapter_id,
                    "name": name_output.strip() if name_output else adapter_id,
                    "disabled": is_disabled
                })
        
        return success(data={"adapters": adapters})
        
    except Exception as e:
        return error(f"Error getting WiFi adapters: {str(e)}")

def change_wifi_ssid(new_ssid, interface_num=0):
    """
    Changes the WiFi SSID (network name) for the specified interface.
    
    Args:
        new_ssid: New SSID to set
        interface_num: WiFi interface number (default 0 for primary interface)
        
    Returns:
        Success or error message
    """
    if not new_ssid:
        return error("SSID cannot be empty")
    
    try:
        # Set the new SSID
        commands = [
            f"uci set wireless.@wifi-iface[{interface_num}].ssid='{new_ssid}'",
            "uci commit wireless",
            "wifi reload"
        ]
        
        for cmd in commands:
            output, err = ssh_manager.execute_command(cmd)
            if err:
                return error(f"Failed to change WiFi SSID: {err}")
                
        # Wait for WiFi to initialize
        time.sleep(2)
        
        return success(f"WiFi SSID changed successfully to: {new_ssid}")
        
    except Exception as e:
        return error(f"Error changing WiFi SSID: {str(e)}")

def get_wifi_interfaces():
    """
    Gets a list of all WiFi interfaces in the router.
    
    Returns:
        Dictionary with success/error status and list of interfaces
    """
    try:
        # Get all wifi-iface sections
        cmd = "uci show wireless | grep wifi-iface"
        output, err = ssh_manager.execute_command(cmd)
        
        if err:
            return error(f"Failed to get WiFi interfaces: {err}")
        
        interfaces = []
        for line in output.splitlines():
            if "=" in line:
                # Get the interface number
                iface_section = line.split('.')[1].split('=')[0]
                iface_num = iface_section.replace("@wifi-iface[", "").replace("]", "")
                
                # Only proceed if we can extract a number
                if iface_num.isdigit():
                    # Get interface details
                    ssid_cmd = f"uci get wireless.@wifi-iface[{iface_num}].ssid 2>/dev/null || echo 'Unknown'"
                    ssid_output, _ = ssh_manager.execute_command(ssid_cmd)
                    
                    disabled_cmd = f"uci get wireless.@wifi-iface[{iface_num}].disabled 2>/dev/null || echo '0'"
                    disabled_output, _ = ssh_manager.execute_command(disabled_cmd)
                    
                    device_cmd = f"uci get wireless.@wifi-iface[{iface_num}].device 2>/dev/null || echo 'Unknown'"
                    device_output, _ = ssh_manager.execute_command(device_cmd)
                    
                    interfaces.append({
                        "num": int(iface_num),
                        "ssid": ssid_output.strip() if ssid_output else "Unknown",
                        "disabled": disabled_output.strip() == "1",
                        "device": device_output.strip() if device_output else "Unknown"
                    })
        
        # Sort interfaces by number
        interfaces.sort(key=lambda x: x["num"])
        
        return success(data={"interfaces": interfaces})
        
    except Exception as e:
        return error(f"Error getting WiFi interfaces: {str(e)}")