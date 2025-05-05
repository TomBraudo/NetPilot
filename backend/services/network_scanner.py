from utils.ssh_client import ssh_manager
from utils.response_helpers import success, error
from db.device_repository import register_device
import socket
import json
import ipaddress
import netifaces
import concurrent.futures
import time
from zeroconf import ServiceBrowser, Zeroconf

# Move imports to module level
import requests

def get_dhcp_leases():
    """
    Get DHCP leases from OpenWrt router
    """
    # First try the ubus call
    output, err = ssh_manager.execute_command("ubus call dhcp leases")
    if not err and output:
        try:
            data = json.loads(output)
            devices = []
            for lease in data.get("leases", []):
                ip = lease.get("ipaddr")
                if ip:
                    devices.append({
                        "ip": ip,
                        "mac": lease.get("macaddr", ""),
                        "hostname": lease.get("hostname", "Unknown"),
                        "source": "dhcp_lease"
                    })
            if devices:
                return devices
        except Exception as e:
            print(f"Failed to parse DHCP leases from ubus: {str(e)}")
    
    # Fallback to reading the DHCP leases file directly
    output, err = ssh_manager.execute_command("cat /tmp/dhcp.leases")
    if err or not output:
        return []
        
    devices = []
    try:
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                # Format: lease_time MAC IP hostname *
                mac = parts[1]
                ip = parts[2]
                hostname = parts[3]
                if hostname == "*":
                    hostname = "Unknown"
                devices.append({
                    "ip": ip,
                    "mac": mac,
                    "hostname": hostname,
                    "source": "dhcp_file"
                })
    except Exception as e:
        print(f"Failed to parse DHCP leases file: {str(e)}")
        
    return devices

def get_devices_from_arp():
    """
    Get devices from router's ARP table
    """
    output, err = ssh_manager.execute_command("ip -j neighbor")
    if err or not output:
        # Fallback to traditional output format if JSON isn't supported
        return get_devices_from_arp_traditional()
    
    devices = []
    try:
        neighbors = json.loads(output)
        for neighbor in neighbors:
            ip = neighbor.get("dst")
            # Skip non-IPv4 addresses
            if ip and neighbor.get("lladdr") and not ":" in ip:
                devices.append({
                    "ip": ip,
                    "mac": neighbor.get("lladdr", ""),
                    "hostname": "Unknown",
                    "source": "arp_table"
                })
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return get_devices_from_arp_traditional()
    except Exception as e:
        print(f"Failed to parse ARP table: {str(e)}")
        
    return devices

def get_devices_from_arp_traditional():
    """
    Parse the traditional output of 'ip neighbor' command
    """
    output, err = ssh_manager.execute_command("ip neighbor")
    if err:
        return []
        
    devices = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 5 and "lladdr" in line:
            ip = parts[0]
            # Skip non-IPv4 addresses
            if ":" in ip:
                continue
            mac = parts[4]
            devices.append({
                "ip": ip,
                "mac": mac,
                "hostname": "Unknown",
                "source": "arp_table"
            })
    
    return devices

def discover_with_mdns():
    """
    Discover devices using mDNS/Bonjour
    """
    discovered_devices = []
    
    class DeviceListener:
        def add_service(self, zeroconf, service_type, name):
            info = zeroconf.get_service_info(service_type, name)
            if info and info.addresses:
                # Get only IPv4 addresses
                ipv4_addresses = []
                for addr in info.addresses:
                    # Convert to IP string
                    ip_str = socket.inet_ntoa(addr)
                    # Check if it's IPv4 (no colons)
                    if not ":" in ip_str:
                        ipv4_addresses.append(ip_str)
                
                if not ipv4_addresses:
                    return
                    
                device_name = name.split('.')[0]  # Extract device name part
                
                # Check if this is actually a hostname or just a service name
                # Many services use descriptive names rather than hostnames
                if device_name.lower() in ["_http", "_device-info"]:
                    # Try to use a better name from properties
                    if info.properties:
                        for key, value in info.properties.items():
                            if key.lower() in [b'model', b'name', b'hostname']:
                                device_name = value.decode('utf-8', errors='ignore')
                                break
                
                for ip in ipv4_addresses:
                    discovered_devices.append({
                        "ip": ip,
                        "hostname": device_name,
                        "service_type": service_type,
                        "source": "mdns"
                    })
    
    try:
        zeroconf = Zeroconf()
        # Common service types to discover
        service_types = [
            "_apple-mobdev2._tcp.local.",
            "_companion-link._tcp.local.",
            "_device-info._tcp.local.",
            "_homekit._tcp.local.",
            "_http._tcp.local.",
            "_googlecast._tcp.local.",
            "_spotify-connect._tcp.local.",
            "_printer._tcp.local.",
            "_ipp._tcp.local.",
            "_smb._tcp.local.",
            "_workstation._tcp.local.",
            "_airplay._tcp.local.",
            "_raop._tcp.local.",     # AirPlay audio
            "_sleep-proxy._udp.local.", # Sleep proxy (Apple)
            "_hap._tcp.local."      # HomeKit
        ]
        
        browsers = [ServiceBrowser(zeroconf, service_type, DeviceListener()) 
                    for service_type in service_types]
        
        # Wait for discoveries to happen - extended to 15 seconds
        time.sleep(15)
        
        zeroconf.close()
    except Exception as e:
        print(f"mDNS discovery error: {str(e)}")
    
    return discovered_devices

def discover_with_wsdiscovery():
    """Try Windows WS-Discovery protocol for hostname info"""
    discovered_devices = []
    
    # Simple WS-Discovery multicast probe
    probe_message = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" '
        'xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" '
        'xmlns:wsd="http://schemas.xmlsoap.org/ws/2005/04/discovery">'
        '<soap:Header>'
        '<wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>'
        '<wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>'
        '<wsa:MessageID>uuid:83081b70-a2aa-46cd-9ed5-8e6c9456383a</wsa:MessageID>'
        '</soap:Header>'
        '<soap:Body>'
        '<wsd:Probe/>'
        '</soap:Body>'
        '</soap:Envelope>'
    )
    
    # Send multicast WS-Discovery probe
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.settimeout(5)
        
        # Send to WS-Discovery multicast address
        sock.sendto(probe_message.encode(), ('239.255.255.250', 3702))
        
        # Listen for responses
        start_time = time.time()
        while time.time() - start_time < 3:  # Listen for 3 seconds
            try:
                data, addr = sock.recvfrom(8192)
                ip = addr[0]
                response = data.decode('utf-8', errors='ignore')
                
                # Extract hostname from response
                hostname = None
                if 'DeviceInfo' in response:
                    # Try to extract computer name
                    import re
                    match = re.search(r'<Computer.*?>(.*?)<\/Computer>', response)
                    if match:
                        hostname = match.group(1)
                    else:
                        # Look for other potential hostname fields
                        match = re.search(r'<Hostname.*?>(.*?)<\/Hostname>', response)
                        if match:
                            hostname = match.group(1)
                
                if hostname:
                    discovered_devices.append({
                        "ip": ip,
                        "hostname": hostname,
                        "source": "wsdiscovery"
                    })
            except socket.timeout:
                pass
    except Exception as e:
        print(f"WS-Discovery error: {str(e)}")
    finally:
        sock.close()
    
    return discovered_devices

def resolve_hostname(ip):
    """
    Try to get a hostname using DNS reverse lookup
    """
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return None
    except Exception:
        return None

def resolve_hostnames_for_devices(devices):
    """
    Try to resolve hostnames for devices that don't have one
    """
    def resolve(device):
        if device.get("hostname") in ["Unknown", ""]:
            hostname = resolve_hostname(device["ip"])
            if hostname:
                device["hostname"] = hostname
                device["source"] = f"{device.get('source', '')},dns"

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(resolve, devices)
    
    return devices

def get_mac_vendor(mac_address):
    """
    Query MAC address vendor database to determine device manufacturer
    """
    # This could be extended to use an API or local database
    # For now, we'll return a simplified implementation
    mac_prefix = mac_address.replace(':', '').replace('-', '').upper()[:6]
    
    # Check for common vendors (this is a minimal example)
    vendors = {
        "F0F61C": "Apple",
        "FCFC48": "Apple",
        "F0766F": "Apple",
        "9CF387": "Apple",
        "B06FE0": "Samsung",
        "F42665": "Samsung",
        "18E2C2": "Samsung",
        "001801": "Actiontec",
        "001A11": "Google",
        "94EB2C": "Google",
        "3CBC93": "Google",
        "D8BBC1": "ASUS/Intel",
        "204747": "Dell",
        "001C23": "Dell",
        "B8C253": "Apple",
        "D89E3F": "Apple",
        "B8E856": "Apple",
        "5C969D": "Apple",
        "BC52B7": "Apple",
        "C01ADA": "Apple", 
        "B8137E": "Apple",
        "68DBCA": "Apple",
        "701AB8": "Intel",
        "D80D17": "TP-Link"
    }
    
    return vendors.get(mac_prefix, "Unknown")

def enrich_device_info(devices):
    """
    Add additional information to devices where available
    """
    for device in devices:
        # Add MAC vendor info for devices with a MAC
        if device.get("mac"):
            device["vendor"] = get_mac_vendor(device["mac"])
        
        # Try to guess device type based on hostname and other factors
        hostname = device.get("hostname", "").lower()
        if any(name in hostname for name in ["iphone", "ipad", "macbook", "imac", "mac"]):
            device["device_type"] = "Apple Device"
        elif any(name in hostname for name in ["android", "pixel", "galaxy", "oneplus"]):
            device["device_type"] = "Android Device"
        elif any(name in hostname for name in ["echo", "alexa"]):
            device["device_type"] = "Amazon Echo"
        elif any(name in hostname for name in ["chromecast", "nest"]):
            device["device_type"] = "Google Device"
        elif "printer" in hostname or device.get("service_type", "").startswith("_ipp"):
            device["device_type"] = "Printer"
        else:
            device["device_type"] = "Unknown"
    
    return devices

def fingerprint_device(ip, mac):
    """
    Advanced device fingerprinting similar to Fing
    """
    device_info = {"ip": ip, "mac": mac}
    
    # 1. Check common ports for service signatures
    common_ports = {
        22: "SSH (likely network device)",
        23: "Telnet (likely network device or IoT)",
        80: "HTTP (web interface)",
        443: "HTTPS (secure web interface)",
        445: "SMB (Windows/NAS device)",
        554: "RTSP (camera/media device)",
        1883: "MQTT (IoT device)",
        8080: "HTTP alternate (IoT/camera)",
        8443: "HTTPS alternate (IoT/camera)",
        9100: "Printer"
    }
    
    open_ports = []
    for port in common_ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)  # Short timeout for quick scanning
                result = s.connect_ex((ip, port))
                if result == 0:
                    open_ports.append(port)
        except:
            pass
    
    # Save open ports
    device_info["open_ports"] = open_ports
    
    # 2. HTTP detection for devices with web interfaces
    if 80 in open_ports or 8080 in open_ports:
        try:
            # Try port 80 first, then 8080
            port = 80 if 80 in open_ports else 8080
            url = f"http://{ip}:{port}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=2)
            
            # Extract information from headers and content
            if "Server" in response.headers:
                device_info["http_server"] = response.headers["Server"]
            
            # Look for device type indicators in HTML content
            content = response.text.lower()
            if "router" in content:
                device_info["device_type"] = "Router"
            elif "nas" in content or "network storage" in content:
                device_info["device_type"] = "NAS"
            elif "camera" in content or "webcam" in content:
                device_info["device_type"] = "IP Camera"
            elif "printer" in content:
                device_info["device_type"] = "Printer"
        except:
            pass
    
    # 3. UPnP detection
    try:
        import urllib.request
        upnp_url = f"http://{ip}:1900/rootDesc.xml"
        response = urllib.request.urlopen(upnp_url, timeout=1)
        if response.status == 200:
            content = response.read().decode("utf-8")
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            
            # Extract device information from UPnP XML
            device_element = root.find(".//device")
            if device_element is not None:
                for key in ["deviceType", "friendlyName", "manufacturer", "modelName"]:
                    element = device_element.find(key)
                    if element is not None and element.text:
                        device_info[f"upnp_{key.lower()}"] = element.text
    except:
        pass
    
    # Classify device based on collected data
    classify_device(device_info)
    
    return device_info

def classify_device(device_info):
    """
    Determine device type based on collected fingerprint data
    """
    # Start with existing open port classification
    if device_info.get("open_ports"):
        ports = device_info["open_ports"]
        
        if 22 in ports and 80 in ports:
            device_info["device_type"] = "Network Device"
            
        if 445 in ports and 139 in ports:
            device_info["device_type"] = "Windows PC/Server"
            
        if 548 in ports or 5009 in ports:
            device_info["device_type"] = "Apple Device"
            
        if 9100 in ports or 631 in ports:
            device_info["device_type"] = "Printer"
    
    # Override with more specific information if available
    if "upnp_devicetype" in device_info:
        upnp_type = device_info["upnp_devicetype"].lower()
        
        if "mediarenderer" in upnp_type:
            device_info["device_type"] = "Media Device"
        elif "urn:schemas-upnp-org:device:InternetGatewayDevice" in upnp_type:
            device_info["device_type"] = "Router/Gateway"
    
    # Additional heuristics based on port combinations
    if device_info.get("device_type") == "Unknown":
        ports = device_info.get("open_ports", [])
        if set([5000, 5001, 5357, 1900]) & set(ports):
            device_info["device_type"] = "Media/Smart TV"
        elif 8080 in ports and 554 in ports:
            device_info["device_type"] = "IP Camera"
        elif 80 in ports and 53 in ports:
            device_info["device_type"] = "Router"

def get_router_specific_devices():
    """
    Try to get device information using router-specific methods
    """
    # Try to detect router type for more targeted extraction
    router_info, _ = ssh_manager.execute_command("cat /etc/os-release")
    
    # Array to hold all devices from router-specific methods
    devices = []
    
    # OpenWrt-specific methods
    if "openwrt" in router_info.lower():
        # Method 1: STA list from wireless (connected Wi-Fi clients)
        output, _ = ssh_manager.execute_command("iwinfo | grep -A 1 'STA' | grep -o '[0-9A-F]\\{2\\}:[0-9A-F]\\{2\\}:[0-9A-F]\\{2\\}:[0-9A-F]\\{2\\}:[0-9A-F]\\{2\\}:[0-9A-F]\\{2\\}'")
        for mac in output.splitlines():
            if mac:
                # Get IP from MAC using ip neigh
                ip_output, _ = ssh_manager.execute_command(f"ip neigh | grep '{mac}' | awk '{{print $1}}'")
                ip = ip_output.strip()
                if ip:
                    devices.append({"ip": ip, "mac": mac, "source": "wifi_clients"})
        
        # Method 2: WiFi association list with signal strength
        output, _ = ssh_manager.execute_command("for i in $(ls /var/run/hostapd-*); do hostapd_cli -p $(dirname $i) -i $(basename $i | cut -d'-' -f2) all_sta; done")
        for line in output.splitlines():
            if "=" in line and "dot11RSNAStatsSTAAddress" in line:
                mac = line.split('=')[1].strip()
                # Get IP from MAC
                ip_output, _ = ssh_manager.execute_command(f"ip neigh | grep '{mac}' | awk '{{print $1}}'")
                ip = ip_output.strip()
                if ip:
                    devices.append({"ip": ip, "mac": mac, "source": "hostapd"})
        
        # Method 3: Connection tracking table
        output, _ = ssh_manager.execute_command("cat /proc/net/nf_conntrack | grep -v '127.0.0.1' | grep 'ESTABLISHED'")
        for line in output.splitlines():
            if "src=" in line and "dst=" in line:
                parts = line.split()
                src_ip = None
                dst_ip = None
                for part in parts:
                    if part.startswith("src="):
                        src_ip = part.split("=")[1]
                    elif part.startswith("dst="):
                        dst_ip = part.split("=")[1]
                
                if src_ip and not src_ip.startswith("192.168.") and not src_ip.startswith("10."):
                    # This is an external IP, so dst_ip is our local device
                    ip = dst_ip
                    # Get MAC from IP
                    mac_output, _ = ssh_manager.execute_command(f"ip neigh | grep '{ip}' | awk '{{print $5}}'")
                    mac = mac_output.strip()
                    if mac and ip not in [d["ip"] for d in devices]:
                        devices.append({"ip": ip, "mac": mac, "source": "conntrack"})
    
    # Method 4: Works for most routers - check arp table for recent entries
    output, _ = ssh_manager.execute_command("grep -v '^IP' /proc/net/arp | grep -v '0x0' | awk '{print $1,$4}'")
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            ip = parts[0]
            mac = parts[1]
            if ip and mac and ip not in [d["ip"] for d in devices]:
                devices.append({"ip": ip, "mac": mac, "source": "arp_proc"})
    
    return devices

def correlate_device_data():
    """Cross-reference data from multiple router tables to identify devices"""
    devices = {}
    
    # Get data from multiple sources
    output, _ = ssh_manager.execute_command("cat /tmp/dhcp.leases")
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 4:
            mac = parts[1].lower()
            ip = parts[2]
            hostname = parts[3]
            devices[mac] = {
                "ip": ip,
                "mac": mac,
                "hostname": hostname if hostname != "*" else "Unknown"
            }
    
    # Add wireless stations
    output, _ = ssh_manager.execute_command("iwinfo assoclist")
    for line in output.splitlines():
        if "SNR" in line and ":" in line:
            mac = None
            for part in line.split():
                if ":" in part and len(part) == 17:  # MAC address format
                    mac = part.lower()
                    break
            
            if mac:
                # Look up IP for this MAC
                ip_cmd, _ = ssh_manager.execute_command(f"ip neigh | grep -i {mac} | awk '{{print $1}}'")
                ip = ip_cmd.strip()
                
                if mac in devices:
                    devices[mac]["source"] = f"{devices[mac].get('source', '')},wifi"
                    if "signal" not in devices[mac]:
                        devices[mac]["signal"] = "Connected via WiFi"
                else:
                    devices[mac] = {
                        "mac": mac,
                        "source": "wifi",
                        "signal": "Connected via WiFi"
                    }
                    if ip:
                        devices[mac]["ip"] = ip
    
    # Add devices seen in auth.log (ssh attempts)
    output, _ = ssh_manager.execute_command("grep 'sshd' /var/log/auth.log | grep 'from' | sed -E 's/.*from ([^ ]+).*/\\1/' | sort | uniq")
    for line in output.splitlines():
        ip = line.strip()
        if ip and not ":" in ip:  # IPv4 only
            # Check if we have a MAC for this IP
            mac_cmd, _ = ssh_manager.execute_command(f"ip neigh | grep {ip} | awk '{{print $5}}'")
            mac = mac_cmd.strip().lower()
            
            if mac and mac in devices:
                devices[mac]["ssh_access"] = "Yes"
            elif mac:
                devices[mac] = {
                    "ip": ip,
                    "mac": mac,
                    "ssh_access": "Yes",
                    "source": "auth_log"
                }
    
    return list(devices.values())

def get_netbios_names():
    """Query NetBIOS names using nbtscan or direct UDP queries"""
    discovered_devices = []
    
    # Try using nbtscan on router if available
    output, err = ssh_manager.execute_command("which nbtscan && nbtscan -q 192.168.1.0/24")
    if not err and output and "not found" not in output:
        for line in output.splitlines():
            if ':' in line:  # nbtscan output format: IP : NETBIOS NAME
                parts = line.split(':', 1)
                if len(parts) == 2:
                    ip = parts[0].strip()
                    hostname = parts[1].strip()
                    discovered_devices.append({
                        "ip": ip,
                        "hostname": hostname,
                        "source": "netbios"
                    })
    else:
        # Direct NetBIOS UDP query for each device in ARP table
        output, _ = ssh_manager.execute_command("ip neigh | grep -v FAILED | awk '{print $1}'")
        for ip in output.splitlines():
            if ip and not ':' in ip:  # Only IPv4
                try:
                    # Send NetBIOS Name Service query
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.settimeout(1)
                    
                    # NetBIOS Name Service query packet (simplified)
                    payload = bytearray([
                        0x82, 0x28, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
                        0x00, 0x00, 0x00, 0x00, 0x20, 0x43, 0x4b, 0x41,
                        0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41,
                        0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41,
                        0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41,
                        0x41, 0x41, 0x41, 0x41, 0x41, 0x00, 0x00, 0x21,
                        0x00, 0x01
                    ])
                    
                    s.sendto(payload, (ip, 137))
                    data, _ = s.recvfrom(1024)
                    
                    # Extract NetBIOS name from response
                    if len(data) > 56:
                        hostname = data[57:73].decode('ascii').strip()
                        if hostname:
                            discovered_devices.append({
                                "ip": ip,
                                "hostname": hostname.strip('\x00'),
                                "source": "netbios"
                            })
                except:
                    pass
                finally:
                    s.close()
    
    return discovered_devices

def discover_with_llmnr():
    """Discover devices using LLMNR (Link-Local Multicast Name Resolution)"""
    discovered_devices = []
    
    # Get list of IPs from ARP table
    output, _ = ssh_manager.execute_command("ip neigh | grep -v FAILED | awk '{print $1}'")
    ips = [ip.strip() for ip in output.splitlines() if ip and not ':' in ip]
    
    for ip in ips:
        try:
            # Send LLMNR query for this IP
            reverse_ip = '.'.join(reversed(ip.split('.'))) + '.in-addr.arpa'
            
            # Use DNS module to create and send LLMNR query
            import dns.message
            import dns.rdatatype
            import dns.query
            
            query = dns.message.make_query(reverse_ip, dns.rdatatype.PTR)
            response = dns.query.udp(query, '224.0.0.252', timeout=1, port=5355)
            
            # Extract hostname from response
            if response.answer:
                for answer in response.answer:
                    for item in answer.items:
                        if hasattr(item, 'target'):
                            hostname = str(item.target).rstrip('.')
                            discovered_devices.append({
                                "ip": ip,
                                "hostname": hostname,
                                "source": "llmnr"
                            })
        except:
            pass
    
    return discovered_devices

def try_ssh_identification():
    """Try to SSH into devices to get hostname (limited to devices with SSH)"""
    discovered_devices = []
    
    # Get list of IPs with port 22 open
    output, _ = ssh_manager.execute_command("nmap -n -p22 --open 192.168.1.0/24 -oG - | grep /open/ | awk '{print $2}'")
    ssh_hosts = [ip.strip() for ip in output.splitlines() if ip]
    
    for ip in ssh_hosts:
        # Try to SSH with timeout
        output, _ = ssh_manager.execute_command(f"timeout 3 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 {ip} hostname")
        if output and not _ and len(output.strip()) > 0:
            hostname = output.strip()
            discovered_devices.append({
                "ip": ip,
                "hostname": hostname,
                "source": "ssh"
            })
    
    return discovered_devices

def get_snmp_info():
    """Try SNMP walk to get device information"""
    discovered_devices = []
    
    # Get list of all local IPs
    output, _ = ssh_manager.execute_command("ip neigh | grep -v FAILED | awk '{print $1}'")
    ips = [ip.strip() for ip in output.splitlines() if ip and not ':' in ip]
    
    for ip in ips:
        # Try common SNMP community strings
        for community in ["public", "private", "cisco"]:
            output, _ = ssh_manager.execute_command(f"snmpget -v2c -c {community} -t 1 {ip} sysName.0 2>/dev/null")
            if output and "STRING:" in output:
                hostname = output.split("STRING:", 1)[1].strip().strip('"\'')
                if hostname:
                    discovered_devices.append({
                        "ip": ip,
                        "hostname": hostname,
                        "source": "snmp"
                    })
                    break  # Stop trying community strings if one works
    
    return discovered_devices

def scan_network():
    """
    Comprehensive network scanning with multiple methods
    """
    # Standard methods
    dhcp_devices = get_dhcp_leases()
    arp_devices = get_devices_from_arp()
    mdns_devices = discover_with_mdns()
    
    # Additional hostname discovery methods
    wsdiscovery_devices = discover_with_wsdiscovery()
    netbios_devices = get_netbios_names()
    llmnr_devices = discover_with_llmnr()
    ssh_devices = try_ssh_identification()
    snmp_devices = get_snmp_info()
    correlated_devices = correlate_device_data()
    
    # Get router-specific device information
    router_specific_devices = get_router_specific_devices()
    
    # Combine all devices with IP as the key
    all_devices = {}
    
    # Process all device sources, starting with basic info and adding more specific info
    for device_list in [
        arp_devices, 
        router_specific_devices, 
        dhcp_devices, 
        mdns_devices,
        wsdiscovery_devices,
        netbios_devices,
        llmnr_devices,
        ssh_devices,
        snmp_devices,
        correlated_devices
    ]:
        for device in device_list:
            # Skip devices without IP
            if not device.get("ip"):
                continue
                
            ip = device["ip"]
            # Skip IPv6 addresses
            if ":" in ip:
                continue
                
            if ip in all_devices:
                # Update existing device with additional info
                existing = all_devices[ip]
                
                # Hostname priority: 
                # mDNS > NetBIOS > WS-Discovery > SNMP > DHCP > correlated > other
                hostname_priority = {
                    "mdns": 1,
                    "netbios": 2, 
                    "wsdiscovery": 3,
                    "snmp": 4,
                    "dhcp_lease": 5,
                    "dhcp_file": 5,
                    "wifi": 6,
                    "ssh": 7,
                    "llmnr": 8,
                    "correlated": 9,
                    "dns": 10,
                    "arp_table": 11,
                    "unknown": 99
                }
                
                new_source = device.get("source", "unknown")
                existing_source = existing.get("source", "unknown")
                
                # Determine the priority of the new and existing hostname sources
                new_priority = 99
                for source_type, priority in hostname_priority.items():
                    if source_type in new_source:
                        new_priority = min(new_priority, priority)
                
                existing_priority = 99
                for source_type, priority in hostname_priority.items():
                    if source_type in existing_source:
                        existing_priority = min(existing_priority, priority)
                
                # Update hostname if new source is higher priority or existing is Unknown
                if ((device.get("hostname") and device["hostname"] != "Unknown") and 
                    (new_priority < existing_priority or existing.get("hostname", "Unknown") == "Unknown")):
                    existing["hostname"] = device["hostname"]
                
                # Update MAC if missing
                if device.get("mac") and not existing.get("mac"):
                    existing["mac"] = device["mac"]
                
                # Append source
                existing["source"] = f"{existing.get('source', '')},{device.get('source', 'unknown')}"
                
                # Copy any other fields that don't exist in the existing device
                for key, value in device.items():
                    if key not in existing and key not in ["ip", "mac", "hostname", "source"]:
                        existing[key] = value
            else:
                # Add new device
                all_devices[ip] = device
    
    # Convert dict back to list
    device_list = list(all_devices.values())
    
    # Do additional fingerprinting
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        fingerprinting_tasks = []
        for device in device_list:
            if device.get("device_type", "Unknown") == "Unknown" and device.get("ip") and device.get("mac"):
                task = executor.submit(fingerprint_device, device["ip"], device["mac"])
                fingerprinting_tasks.append((device, task))
        
        # Collect fingerprinting results
        for device, task in fingerprinting_tasks:
            try:
                fingerprint_result = task.result(timeout=10)
                for key, value in fingerprint_result.items():
                    if key not in device or (key == "device_type" and device[key] == "Unknown"):
                        device[key] = value
            except Exception as e:
                print(f"Fingerprinting error for {device['ip']}: {str(e)}")
    
    # Final enrichment pass
    device_list = enrich_device_info(device_list)
    
    # Register devices in database
    for device in device_list:
        register_device(
            device["ip"], 
            device.get("mac", "Unknown"), 
            device.get("hostname", "Unknown")
        )
    
    return success(data=device_list)

def get_active_network():
    """
    Get information about the currently active network
    """
    try:
        # Get the default gateway
        gateways = netifaces.gateways()
        default_gateway = gateways.get('default', {}).get(netifaces.AF_INET, None)

        if not default_gateway:
            return error("No default gateway found. Check your network connection.")

        gateway_ip, interface = default_gateway  # Get the gateway IP and interface

        # Get IP information for the active interface
        iface_info = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [{}])[0]
        ip_address = iface_info.get('addr')

        if not ip_address:
            return error(f"No IP address found for interface {interface}")

        # Compute the subnet
        netmask = iface_info.get('netmask', '255.255.255.0')
        network = ipaddress.IPv4Network(f"{ip_address}/{netmask}", strict=False)

        network_info = {
            "interface": interface,
            "ip_address": ip_address,
            "gateway": gateway_ip,
            "subnet": str(network),
            "netmask": netmask
        }
        
        return success(data=network_info)
    except Exception as e:
        return error(f"Failed to get network information: {str(e)}")

if __name__ == "__main__":
    # This allows running the scanner directly for testing
    result = scan_network()
    print(json.dumps(result, indent=2))