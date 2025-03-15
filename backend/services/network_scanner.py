from scapy.all import ARP, Ether, srp
import socket
import concurrent.futures
import json
import os
from utils.path_utils import get_data_folder

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
    Scans the three most popular subnets: 192.168.0.1/24, 192.168.1.1/24, 10.0.0.1/24.
    Uses the same scanning method as in your original script.
    """
    all_devices = []
    json_path = os.path.join(get_data_folder(), "Ips_to_scan.json")
    with open(json_path, "r") as ips_file:
        ips_file = json.load(ips_file)
        subnets = ips_file["subnets"]
        

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

    # Resolve hostnames
    return get_device_names(all_devices)


def print_results(devices):
    """
    Prints the detected devices in the required format.
    """
    print("IP Address\t\tMAC Address\t\tDevice Name")
    print("--------------------------------------------------------")
    for device in devices:
        print(f"{device['ip']}\t\t{device['mac']}\t\t{device['hostname']}")


if __name__ == "__main__":
    devices = scan_network()
    print_results(devices)
