from utils.ssh_client import ssh_manager

def find_interface_for_ip(target_ip):
    """
    Finds the correct network interface for a given IP address.
    """
    command = f"ip route get {target_ip}"
    output, error = ssh_manager.execute_command(command)
    if error:
        return None, f"Error finding interface: {error}"

    for line in output.split("\n"):
        parts = line.split()
        if target_ip in line:
            for i, part in enumerate(parts):
                if part == "dev":
                    return parts[i + 1], None

    return None, "No interface found."

def set_bandwidth_limit(target_ip, bandwidth_mbps):
    """
    Sets bandwidth limits for a given IP address.
    """
    interface, error = find_interface_for_ip(target_ip)
    if not interface:
        return {"error": error}

    commands = [
        f"tc qdisc add dev {interface} root handle 1: htb",
        f"tc class add dev {interface} parent 1: classid 1:1 htb rate {bandwidth_mbps}mbit ceil {bandwidth_mbps}mbit",
        f"tc filter add dev {interface} protocol ip parent 1:0 prio 1 u32 match ip dst {target_ip}/32 flowid 1:1"
    ]

    for command in commands:
        ssh_manager.execute_command(command)

    return {"success": f"Bandwidth limit set to {bandwidth_mbps} Mbps for IP {target_ip}."}

def remove_bandwidth_limit(target_ip):
    """
    Removes bandwidth limits for a given IP address.
    """
    interface, error = find_interface_for_ip(target_ip)
    if not interface:
        return {"error": error}

    commands = [
        f"tc filter del dev {interface} protocol ip parent 1:0 prio 1 u32 match ip dst {target_ip}/32 flowid 1:1",
        f"tc class del dev {interface} parent 1: classid 1:1",
        f"tc qdisc del dev {interface} root handle 1:"
    ]

    for command in commands:
        ssh_manager.execute_command(command)

    return {"success": f"Bandwidth limit removed for IP {target_ip}."}
