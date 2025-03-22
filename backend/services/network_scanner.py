from scapy.all import ARP, Ether, srp
import socket
import concurrent.futures
import json
import os
from utils.path_utils import get_data_folder
import netifaces
import ipaddress
from utils.response_helpers import success, error

def scan(ip_range):
    """
    Sends ARP requests in the given IP range and returns detected devices.
    This is the same scanning method as in your original script.
    """
    print(f"[DEBUG] Scanning {ip_range}...")
    arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip_range)
    result = srp(arp_request, timeout=1, verbose=False)[0]

    devices = []
    for sent, received in result:
        device = {"ip": received.psrc, "mac": received.hwsrc}
        if device not in devices:  # Avoid duplicates
            devices.append(device)

    return devices


def get_device_names(devices):
    """
    Resolves hostnames for detected devices using reverse DNS.
    Uses threading to speed up resolution.
    """
    def resolve(device):
        try:
            device["hostname"] = socket.gethostbyaddr(device["ip"])[0]
        except socket.herror:
            device["hostname"] = "Unknown"

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(resolve, devices)

    return devices

def scan_network():
    """
    Adds the currently active subnet to the list of subnets in `Ips_to_scan.json`,
    then scans all subnets in parallel, removing duplicate devices.
    """
    json_path = os.path.join(get_data_folder(), "Ips_to_scan.json")
    
    # Load existing subnets from the file
    if os.path.exists(json_path):
        with open(json_path, "r") as ips_file:
            ips_data = json.load(ips_file)
    else:
        ips_data = {"subnets": []}
    
    # Get the active network subnet
    active_network = get_active_network()
    if active_network:
        active_subnet = active_network["subnet"]
        
        # Add active subnet if not already in the list
        if active_subnet not in ips_data["subnets"]:
            ips_data["subnets"].append(active_subnet)
            with open(json_path, "w") as ips_file:
                json.dump(ips_data, ips_file, indent=4)
    
    subnets = ips_data["subnets"]
    all_devices = []
    
    # Scan all subnets in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = executor.map(scan, subnets)

    # Collect results and remove duplicates
    seen = set()
    for devices in results:
        for device in devices:
            key = (device["ip"], device["mac"])
            if key not in seen:
                seen.add(key)
                all_devices.append(device)

    # Resolve hostnames for detected devices
    devices_with_hostnames = get_device_names(all_devices)

    return success(data=devices_with_hostnames)


def print_results(devices):
    """
    Prints the detected devices in the required format.
    """
    print("IP Address\t\tMAC Address\t\tDevice Name")
    print("--------------------------------------------------------")
    for device in devices:
        print(f"{device['ip']}\t\t{device['mac']}\t\t{device['hostname']}")

def get_active_network():
    # Get the default gateway
    gateways = netifaces.gateways()
    default_gateway = gateways.get('default', {}).get(netifaces.AF_INET, None)

    if not default_gateway:
        print("No default gateway found. Check your network connection.")
        return None

    gateway_ip, interface = default_gateway  # Get the gateway IP and interface

    # Get IP information for the active interface
    iface_info = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [{}])[0]
    ip_address = iface_info.get('addr')

    if not ip_address:
        print(f"No IP address found for interface {interface}")
        return None

    # Compute the /24 subnet
    subnet = ipaddress.IPv4Network(f"{ip_address}/24", strict=False)

    return {
        "interface": interface,
        "ip_address": ip_address,
        "gateway": gateway_ip,
        "subnet": str(subnet)
    }

if __name__ == "__main__":
    devices = scan_network()
    print_results(devices)
