import sys
import os
# Add the parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Now use regular import
from utils.ssh_client import ssh_manager

# These commands will install all required packages for NetPilot features
commands = [
    # Update package lists
    "opkg update",
    
    # Core networking packages
    "opkg install firewall4",           # Firewall management
    "opkg install iptables",            # Base iptables
    "opkg install iptables-mod-ipopt",  # IP options module for iptables
    "opkg install ip-full",             # Full IP utilities
    "opkg install uci",                 # Unified Configuration Interface
    
    # DNS and DHCP
    "opkg install dnsmasq",             # DNS and DHCP server
    "opkg install odhcpd-ipv6only",     # DHCPv6 server
    
    # Traffic control for bandwidth limiting
    "opkg install tc",                  # Traffic Control utility
    "opkg install kmod-sched",          # Kernel scheduler
    "opkg install kmod-sched-core",     # Core scheduler modules
    
    # SSH server for remote management
    "opkg install dropbear",            # Lightweight SSH server
    
    # MAC address filtering
    "opkg install wpad",                # Wireless tools including hostapd
    
    # QoS packages
    "opkg install qos-scripts",         # Quality of Service scripts
    "opkg install luci-app-qos",        # QoS application
    
    # Time-based access control dependencies
    "opkg install cron",                # Scheduler for time-based rules
    
    # Useful utilities
    "opkg install curl",                # For HTTP requests
    "opkg install wget",                # Alternative download tool
    "opkg install ca-certificates",     # SSL certificates
    
    # Network analysis tools
    "opkg install tcpdump",             # Network packet analyzer
    "opkg install nmap",                # Network exploration tool
    
    # Save installed package list
    "opkg list-installed > /tmp/installed_packages.txt",
    
    # Restart essential services
    "/etc/init.d/network restart",
    "/etc/init.d/firewall restart",
    "wifi reload"
]

if __name__ == "__main__":
    print("Installing all required packages for NetPilot features...")
    
    for cmd in commands:
        print(f"Executing: {cmd}")
        output, error = ssh_manager.execute_command(cmd)
        
        if output:
            print(f"Output: {output}")
        
        if error:
            print(f"Error: {error}")
        
        print("-" * 50)
    
    print("Package installation completed!")
    print("\n==== INSTALLED PACKAGES ====")
    output, _ = ssh_manager.execute_command("cat /tmp/installed_packages.txt")
    print(output)
    
    print("\n==== VERIFYING FUNCTIONALITY ====")
    # Verify iptables is working
    output, error = ssh_manager.execute_command("iptables -L")
    if error:
        print("WARNING: iptables verification failed!")
    else:
        print("iptables: OK")
    
    # Verify traffic control is working
    output, error = ssh_manager.execute_command("tc -h")
    if error:
        print("WARNING: tc verification failed!")
    else:
        print("traffic control: OK")
    
    # Verify UCI is working
    output, error = ssh_manager.execute_command("uci show wireless")
    if error:
        print("WARNING: uci verification failed!")
    else:
        print("uci: OK")
    
    print("\nAll required packages have been installed for:")
    print("1. Device blocking (iptables, firewall4)")
    print("2. Bandwidth limiting (tc, kmod-sched)")
    print("3. WiFi management (wpad, uci)")
    print("4. QoS priority controls (qos-scripts)")
    print("5. Access scheduling (cron)")
    print("6. Blacklist/Whitelist functionality")
    print("\nYour NetPilot system should now have all required dependencies.")