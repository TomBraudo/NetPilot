import re
from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager

logger = get_logger('services.block_ip')
router_connection_manager = RouterConnectionManager()

def block_ip(ip_address: str):
    """Adds an IP to the block list firewall rule."""
    if not ip_address:
        return None, "IP address is required"

    try:
        # Step 1: Get the MAC address for the given IP from the router's ARP table
        arp_cmd = f"arp -n | grep '{ip_address}' | awk '{{print $3}}'"
        mac_address, arp_err = router_connection_manager.execute(arp_cmd)

        if arp_err or not mac_address:
            # As a fallback, try getting it from DHCP leases
            lease_cmd = f"cat /tmp/dhcp.leases | grep '{ip_address}' | awk '{{print $2}}'"
            mac_address, lease_err = router_connection_manager.execute(lease_cmd)
            if lease_err or not mac_address:
                return None, f"Could not find MAC for IP {ip_address} via ARP or DHCP lease"

        mac_address = mac_address.strip()
        
        # Step 2: Add a firewall rule to block the MAC address
        rule_comment = f"Block-{mac_address.replace(':', '-')}"
        block_cmd = (
            f"uci add firewall rule; "
            f"uci set firewall.@rule[-1].name='{rule_comment}'; "
            f"uci set firewall.@rule[-1].src='lan'; "
            f"uci set firewall.@rule[-1].src_mac='{mac_address}'; "
            f"uci set firewall.@rule[-1].target='REJECT'; "
            f"uci commit firewall; "
            f"/etc/init.d/firewall restart"
        )
        _, block_err = router_connection_manager.execute(block_cmd)
        
        if block_err and "uci: Entry not found" not in block_err:
             # Ignore "entry not found" which can be a benign warning
            return None, f"Failed to apply block rule: {block_err}"
            
        return f"Successfully blocked IP {ip_address} (MAC: {mac_address})", None

    except RuntimeError as e:
        logger.error(f"Connection error blocking IP: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Error blocking IP {ip_address}: {str(e)}", exc_info=True)
        return None, f"An unexpected error occurred while blocking IP {ip_address}"

def unblock_ip(ip_address: str):
    """Removes an IP from the block list."""
    if not ip_address:
        return None, "IP address is required"

    try:
        # Step 1: Find MAC for the IP
        arp_cmd = f"arp -n | grep '{ip_address}' | awk '{{print $3}}'"
        mac_address, arp_err = router_connection_manager.execute(arp_cmd)

        if arp_err or not mac_address:
            lease_cmd = f"cat /tmp/dhcp.leases | grep '{ip_address}' | awk '{{print $2}}'"
            mac_address, lease_err = router_connection_manager.execute(lease_cmd)
            if lease_err or not mac_address:
                return None, f"Could not find MAC for IP {ip_address} to unblock"
        
        mac_address = mac_address.strip()
        rule_comment = f"Block-{mac_address.replace(':', '-')}"
        
        # Step 2: Find and delete the corresponding firewall rule
        # This is complex because UCI identifies rules by index. We find the index first.
        find_cmd = f"uci show firewall | grep \"{rule_comment}\" | sed 's/\\[\\([0-9]*\\)\\].*/\\1/'"
        rule_index, find_err = router_connection_manager.execute(find_cmd)
        
        if find_err or not rule_index:
            return None, f"Block rule for MAC {mac_address} not found. Maybe already unblocked."
            
        rule_index = rule_index.strip().split('\n')[0] # Get first index if multiple
        
        unblock_cmd = (
            f"uci delete firewall.@rule[{rule_index}]; "
            f"uci commit firewall; "
            f"/etc/init.d/firewall restart"
        )
        _, unblock_err = router_connection_manager.execute(unblock_cmd)
        
        if unblock_err:
            return None, f"Failed to apply unblock rule: {unblock_err}"

        return f"Successfully unblocked IP {ip_address} (MAC: {mac_address})", None

    except RuntimeError as e:
        logger.error(f"Connection error unblocking IP: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Error unblocking IP {ip_address}: {str(e)}", exc_info=True)
        return None, f"An unexpected error occurred while unblocking IP {ip_address}"

def get_blocked_ips():
    """Retrieves a list of all MAC addresses blocked by the firewall."""
    try:
        # Find rules with names/comments starting with 'Block-'
        cmd = "uci show firewall | grep -E \"\\.name='Block-.*'\" | sed -E \"s/.*='Block-(.*)'/\\1/\""
        blocked_macs_str, err = router_connection_manager.execute(cmd)

        if err:
            return None, f"Failed to get blocked list: {err}"

        blocked_macs = [mac.replace('-', ':') for mac in blocked_macs_str.strip().split('\n') if mac]
        
        if not blocked_macs:
            return [], None

        # Now, map these MACs back to current IPs from the ARP table for user convenience
        arp_table_str, _ = router_connection_manager.execute("arp -n")
        
        ip_mac_pairs = re.findall(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*?([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})", arp_table_str)
        
        arp_map = {mac.lower(): ip for ip, mac in ip_mac_pairs}
        
        blocked_list = []
        for mac in blocked_macs:
            blocked_list.append({
                "mac": mac,
                "ip": arp_map.get(mac.lower(), "N/A") # IP might not be in ARP if device is offline
            })

        return blocked_list, None

    except RuntimeError as e:
        logger.error(f"Connection error getting blocked IPs: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Error getting blocked list: {str(e)}", exc_info=True)
        return None, "An unexpected error occurred while getting blocked IPs"
