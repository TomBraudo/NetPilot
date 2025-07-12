#!/usr/bin/env python3
"""
Script to check the current state of iptables rules on the router.
This will help verify that old badly ordered rules were removed.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from managers.router_connection_manager import RouterConnectionManager

def check_router_rules():
    """Check the current iptables rules and TC setup on the router."""
    print("=" * 70)
    print("CHECKING ROUTER RULES AND INFRASTRUCTURE")
    print("=" * 70)
    
    router_manager = RouterConnectionManager()
    
    print("\n🔍 1. CHECKING NETPILOT_WHITELIST CHAIN:")
    print("   (Should show correct rule order if working)")
    output, err = router_manager.execute("iptables -t mangle -L NETPILOT_WHITELIST -n --line-numbers -v")
    if err:
        print(f"❌ Error: {err}")
    else:
        print(output)
        
    print("\n🔍 2. CHECKING NETPILOT_BLACKLIST CHAIN:")
    output, err = router_manager.execute("iptables -t mangle -L NETPILOT_BLACKLIST -n --line-numbers -v")
    if err:
        print(f"❌ Error: {err}")
    else:
        print(output)
    
    print("\n🔍 3. CHECKING WHICH CHAINS ARE ACTIVE IN PREROUTING:")
    print("   (Should show which NetPilot chains are being used)")
    output, err = router_manager.execute("iptables -t mangle -L PREROUTING -n --line-numbers")
    if err:
        print(f"❌ Error: {err}")
    else:
        print(output)
    
    print("\n🔍 4. CHECKING FORWARD CHAIN (fallback location):")
    output, err = router_manager.execute("iptables -t mangle -L FORWARD -n --line-numbers")
    if err:
        print(f"❌ Error: {err}")
    else:
        print(output)
    
    print("\n🔍 5. CHECKING TC SETUP ON ALL INTERFACES:")
    # Get all interfaces first
    output, err = router_manager.execute("ls /sys/class/net/ | grep -v lo")
    if err:
        print(f"❌ Error getting interfaces: {err}")
        return
    
    interfaces = [iface.strip() for iface in output.split() if iface.strip()]
    
    for interface in interfaces:
        print(f"\n   📡 Interface: {interface}")
        
        # Check qdisc
        print(f"      TC Qdisc:")
        output, err = router_manager.execute(f"tc qdisc show dev {interface}")
        if output:
            print(f"      {output.strip()}")
        
        # Check classes
        print(f"      TC Classes:")
        output, err = router_manager.execute(f"tc class show dev {interface}")
        if output:
            for line in output.strip().split('\n'):
                if line.strip():
                    print(f"      {line.strip()}")
        
        # Check filters
        print(f"      TC Filters:")
        output, err = router_manager.execute(f"tc filter show dev {interface}")
        if output:
            for line in output.strip().split('\n'):
                if line.strip():
                    print(f"      {line.strip()}")
    
    print("\n🔍 6. CHECKING CURRENT ROUTER STATE:")
    print("   (NetPilot state file content)")
    output, err = router_manager.execute("cat /etc/config/netpilot_state.json 2>/dev/null || echo 'State file not found'")
    if output:
        print(output)
    
    print("\n" + "=" * 70)
    print("ANALYSIS TIPS:")
    print("=" * 70)
    print("✅ GOOD SIGNS:")
    print("   - NETPILOT_WHITELIST chain exists but is empty (no device rules)")
    print("   - NETPILOT_WHITELIST only has default MARK --set-mark 98 rule")
    print("   - No specific MAC address rules in whitelist chain")
    print("   - TC infrastructure exists on all interfaces")
    print()
    print("❌ BAD SIGNS:")
    print("   - Old MAC address rules still present")
    print("   - Rules in wrong order (device rules AFTER default rule)")
    print("   - Multiple conflicting MARK rules")
    print("   - Missing TC infrastructure")
    print()
    print("🔧 WHAT TO LOOK FOR:")
    print("   - Your device MAC (d8:bb:c1:47:3a:43) should NOT appear in any chains")
    print("   - IP 192.168.1.122 should NOT appear in any chains")
    print("   - Whitelist chain should be clean with only default rule")

if __name__ == "__main__":
    check_router_rules()
