def print_results(devices):
    """
    Prints the detected devices in a formatted table.
    
    Args:
        devices (list): List of device dictionaries containing 'ip', 'mac', and 'hostname' keys
    """
    print("IP Address\t\tMAC Address\t\tDevice Name")
    print("--------------------------------------------------------")
    for device in devices:
        print(f"{device['ip']}\t\t{device['mac']}\t\t{device['hostname']}") 