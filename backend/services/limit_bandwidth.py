from utils.ssh_client import ssh_manager
from utils.response_helpers import success, error
from db.device_repository import get_mac_from_ip

def find_interface_for_ip(target_ip):
    """
    Finds the network interface for a given IP address.
    """
    command = f"ip route get {target_ip}"
    output, error = ssh_manager.execute_command(command)
    
    if error:
        return None, f"Failed to find interface: {error}"
        
    # Extract interface name from output
    parts = output.split()
    if len(parts) >= 3:
        return parts[2], None
    return None, "Interface not found in route output"

def get_bandwidth_limit(target_ip):
    """
    Retrieves the bandwidth limit for a given IP address.
    """
    # Get MAC address from database
    mac_address = get_mac_from_ip(target_ip)
    if not mac_address:
        return error(f"IP {target_ip} not found in network.")

    interface, error = find_interface_for_ip(target_ip)
    if not interface:
        return error(f"Interface not found for {target_ip}")

    # Check for tc filter related to the target IP
    command = f"tc filter show dev {interface} | grep {target_ip}"
    output, error = ssh_manager.execute_command(command)

    if error:
        return error(f"Failed to check bandwidth limit: {error}")

    if not output:
        return error(f"No bandwidth limit found for IP {target_ip} on {interface}.")
    
    # Extract the bandwidth limit from tc class
    command = f"tc class show dev {interface} | grep 'htb'"
    class_output, error = ssh_manager.execute_command(command)

    if error:
        return error(f"Failed to retrieve bandwidth class: {error}")

    # Parse the output to extract bandwidth information
    limit_info = None
    for line in class_output.split("\n"):
        if "rate" in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "rate":
                    limit_info = parts[i+1]
                    break

    if limit_info:
        return success(f"Bandwidth limit for {target_ip} is {limit_info}.")
    else:
        return error(f"Bandwidth limit not found in class settings for {target_ip}.")

def set_bandwidth_limit(target_ip, bandwidth_mbps):
    """
    Sets bandwidth limits for a given IP address.
    """
    # Get MAC address from database
    mac_address = get_mac_from_ip(target_ip)
    if not mac_address:
        return error(f"IP {target_ip} not found in network.")

    interface, error = find_interface_for_ip(target_ip)
    if not interface:
        return error(f"Interface not found for {target_ip}")

    commands = [
        f"tc qdisc add dev {interface} root handle 1: htb",
        f"tc class add dev {interface} parent 1: classid 1:1 htb rate {bandwidth_mbps}mbit ceil {bandwidth_mbps}mbit",
        f"tc filter add dev {interface} protocol ip parent 1:0 prio 1 u32 match ip dst {target_ip}/32 flowid 1:1"
    ]

    for command in commands:
        output, error = ssh_manager.execute_command(command)
        if error:
            return error(f"Failed to set bandwidth limit: {error}")

    return success(f"Bandwidth limit set to {bandwidth_mbps} Mbps for IP {target_ip}.")

def remove_bandwidth_limit(target_ip):
    """
    Removes bandwidth limits for a given IP address.
    """
    # Get MAC address from database
    mac_address = get_mac_from_ip(target_ip)
    if not mac_address:
        return error(f"IP {target_ip} not found in network.")

    interface, error = find_interface_for_ip(target_ip)
    if not interface:
        return error(f"Interface not found for {target_ip}")

    commands = [
        f"tc filter del dev {interface} protocol ip parent 1:0 prio 1 u32 match ip dst {target_ip}/32 flowid 1:1",
        f"tc class del dev {interface} parent 1: classid 1:1",
        f"tc qdisc del dev {interface} root handle 1:"
    ]

    for command in commands:
        output, error = ssh_manager.execute_command(command)
        if error and "No such file or directory" not in error:
            return error(f"Failed to remove bandwidth limit: {error}")

    return success(f"Bandwidth limit removed for IP {target_ip}.")

