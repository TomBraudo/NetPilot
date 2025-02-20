from scapy.all import ARP, Ether, srp
import socket
import subprocess
import platform
import re
import concurrent.futures

def get_local_subnet():
    """
    Detects the correct subnet for the active Ethernet interface (e.g., 192.168.1.0/24).
    Works on Windows, Linux, and macOS.
    """
    try:
        system = platform.system().lower()

        if system == "windows":
            # Use ipconfig and extract the IPv4 address of the "Ethernet adapter Ethernet"
            output = subprocess.check_output("ipconfig", shell=True, text=True)
            ethernet_section = re.search(r"Ethernet adapter Ethernet:([\s\S]*?)Default Gateway", output)

            if ethernet_section:
                ethernet_text = ethernet_section.group(1)
                ipv4_match = re.search(r"IPv4 Address[.\s]+:\s*(\d+\.\d+\.\d+\.\d+)", ethernet_text)
                subnet_match = re.search(r"Subnet Mask[.\s]+:\s*(\d+\.\d+\.\d+\.\d+)", ethernet_text)

                if ipv4_match and subnet_match:
                    ipv4 = ipv4_match.group(1)
                    subnet_mask = subnet_match.group(1)
                    return ip_to_cidr(ipv4, subnet_mask)

        else:
            # Use `ip route` for Linux/macOS to find the active interface's IP
            output = subprocess.check_output("ip route", shell=True, text=True)
            ipv4_match = re.search(r"default via \S+ dev (\S+) proto", output)
            
            if ipv4_match:
                interface = ipv4_match.group(1)
                output = subprocess.check_output(f"ip -4 addr show {interface}", shell=True, text=True)
                ipv4_match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/(\d+)", output)

                if ipv4_match:
                    ipv4 = ipv4_match.group(1)
                    cidr_prefix = ipv4_match.group(2)
                    return f"{ipv4.rsplit('.', 1)[0]}.0/{cidr_prefix}"

    except Exception as e:
        print(f"[ERROR] Could not detect subnet: {e}")
    
    return None  # No valid subnet found

def ip_to_cidr(ip, mask):
    """
    Converts an IP address and subnet mask to CIDR notation (e.g., 192.168.1.0/24).
    """
    ip_parts = list(map(int, ip.split(".")))
    mask_parts = list(map(int, mask.split(".")))

    # Calculate network address
    network_parts = [ip_parts[i] & mask_parts[i] for i in range(4)]
    network_address = ".".join(map(str, network_parts))

    # Calculate CIDR prefix
    cidr_prefix = sum(bin(part).count("1") for part in mask_parts)
    
    return f"{network_address}/{cidr_prefix}"

def scan_network():
    """
    Scans the local network using Scapy ARP requests.
    """
    subnet = get_local_subnet()
    if not subnet:
        return {"error": "Failed to detect subnet."}

    print(f"[DEBUG] Scanning network: {subnet}")

    # Create an ARP request for the correct subnet
    arp_request = ARP(pdst=subnet)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")  # Broadcast
    packet = ether / arp_request

    # Send packet and receive responses
    answered, _ = srp(packet, timeout=2, verbose=False)

    devices = []
    for sent, received in answered:
        devices.append({
            "ip": received.psrc,
            "mac": received.hwsrc,
            "hostname": "Resolving..."
        })

    # Use threads to resolve hostnames faster
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(resolve_hostname, device["ip"]): device for device in devices}
        for future in concurrent.futures.as_completed(futures):
            futures[future]["hostname"] = future.result()

    print("[DEBUG] Detected devices:", devices)
    return {"devices": devices}

def resolve_hostname(ip):
    """ Resolves a hostname from an IP address using reverse DNS lookup. """
    try:
        return socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.timeout):
        return "Unknown"
