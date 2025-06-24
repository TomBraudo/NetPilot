from scapy.all import ARP, Ether, srp
import socket
import concurrent.futures
import netifaces
import ipaddress
from utils.response_helpers import success
from utils.logging_config import get_logger
from db.device_repository import register_device
from utils.network_utils import print_results

logger = get_logger('services.network_scanner')

def scan_ip_range(ip_range):
    """
    Sends ARP requests in the given IP range and returns detected devices.
    This is the same scanning method as in your original script.
    """
    try:
        print(f"[DEBUG] Scanning {ip_range}...")
        arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip_range)
        result = srp(arp_request, timeout=1, verbose=False)[0]

        devices = []
        for sent, received in result:
            device = {
                "ip": received.psrc,
                "mac": received.hwsrc
            }
            if device not in devices:  # Avoid duplicates
                devices.append(device)

        return success(data=devices)
    except Exception as e:
        logger.error(f"Error scanning network: {str(e)}", exc_info=True)
        raise


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
    Scans the local network for active devices using ARP requests.
    Returns a list of devices with their IP and MAC addresses.
    """
    try:
        # Get the default gateway interface
        gateways = netifaces.gateways()
        default_gateway = gateways['default'][netifaces.AF_INET][1]
        
        # Get the IP address of the default gateway interface
        interface_ip = netifaces.ifaddresses(default_gateway)[netifaces.AF_INET][0]['addr']
        
        # Get the network mask
        netmask = netifaces.ifaddresses(default_gateway)[netifaces.AF_INET][0]['netmask']
        
        # Calculate the network address
        network = ipaddress.IPv4Network(f"{interface_ip}/{netmask}", strict=False)
        
        # Scan the network
        result = scan_ip_range(str(network))
        
        # Register each device in the database
        for device in result.get("data", []):
            try:
                hostname = socket.getfqdn(device["ip"])
                register_device(device["ip"], device["mac"], hostname)
            except Exception as e:
                logger.warning(f"Failed to register device {device['ip']}: {str(e)}")
                continue
        
        return result
    except Exception as e:
        logger.error(f"Error scanning network: {str(e)}", exc_info=True)
        raise


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
