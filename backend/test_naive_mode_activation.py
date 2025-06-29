#!/usr/bin/env python3
"""
Test script for the naive mode activation approach.

This script demonstrates and tests the naive complete teardown/rebuild approach
for NetPilot whitelist mode activation.
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.mode_activation_service import (
    activate_whitelist_mode_rules,
    deactivate_whitelist_mode_rules,
    deactivate_all_modes_rules,
    _complete_teardown,
    _rebuild_tc_infrastructure,
    _rebuild_whitelist_chain_proven
)

def test_naive_approach():
    """
    Test the naive approach components individually.
    """
    print("=== TESTING NAIVE MODE ACTIVATION APPROACH ===\n")
    
    print("1. Testing complete teardown...")
    try:
        _complete_teardown()
        print("✅ Complete teardown executed successfully")
    except Exception as e:
        print(f"❌ Complete teardown failed: {e}")
        return False
    
    print("\n2. Testing TC infrastructure rebuild...")
    try:
        success = _rebuild_tc_infrastructure()
        if success:
            print("✅ TC infrastructure rebuild successful")
        else:
            print("❌ TC infrastructure rebuild failed")
            return False
    except Exception as e:
        print(f"❌ TC infrastructure rebuild failed: {e}")
        return False
    
    print("\n3. Testing whitelist chain rebuild...")
    try:
        success = _rebuild_whitelist_chain_proven()
        if success:
            print("✅ Whitelist chain rebuild successful")
        else:
            print("❌ Whitelist chain rebuild failed")
            return False
    except Exception as e:
        print(f"❌ Whitelist chain rebuild failed: {e}")
        return False
    
    print("\n4. Testing full whitelist mode activation...")
    try:
        success, error = activate_whitelist_mode_rules()
        if success:
            print("✅ Full whitelist mode activation successful")
        else:
            print(f"❌ Full whitelist mode activation failed: {error}")
            return False
    except Exception as e:
        print(f"❌ Full whitelist mode activation failed: {e}")
        return False
    
    print("\n5. Testing whitelist mode deactivation...")
    try:
        success, error = deactivate_whitelist_mode_rules()
        if success:
            print("✅ Whitelist mode deactivation successful")
        else:
            print(f"❌ Whitelist mode deactivation failed: {error}")
            return False
    except Exception as e:
        print(f"❌ Whitelist mode deactivation failed: {e}")
        return False
    
    print("\n=== ALL TESTS PASSED ===")
    print("The naive approach is working correctly!")
    print("\nKey benefits of this approach:")
    print("- Simple: Complete teardown and rebuild every time")
    print("- Reliable: No rule conflicts or state management issues")
    print("- Maintainable: Easy to debug and understand")
    print("- Proven: Based on manual testing that works 100%")
    print("- No redundant checks: We always start with a clean state")
    
    return True

def demonstrate_manual_commands():
    """
    Show the manual commands that the naive approach implements.
    """
    print("\n=== MANUAL COMMANDS IMPLEMENTED BY NAIVE APPROACH ===\n")
    
    print("PHASE 1: Complete Teardown")
    print("iptables -t mangle -D FORWARD -j NETPILOT_WHITELIST 2>/dev/null || true")
    print("iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true")
    print("iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true")
    print('for interface in $(ls /sys/class/net/ | grep -v lo); do')
    print('    tc qdisc del dev $interface root 2>/dev/null || true')
    print('done')
    
    print("\nPHASE 2: Rebuild TC Infrastructure")
    print('for interface in $(ls /sys/class/net/ | grep -v lo); do')
    print('    tc qdisc add dev $interface root handle 1: htb default 1')
    print('    tc class add dev $interface parent 1: classid 1:1 htb rate 1000mbit')
    print('    tc class add dev $interface parent 1: classid 1:10 htb rate 50mbit')
    print('    tc filter add dev $interface parent 1: protocol ip prio 1 handle 1 fw flowid 1:1')
    print('    tc filter add dev $interface parent 1: protocol ip prio 2 handle 98 fw flowid 1:10')
    print('done')
    
    print("\nPHASE 3: Rebuild Whitelist Chain")
    print("iptables -t mangle -N NETPILOT_WHITELIST")
    print("# For each whitelisted device:")
    print("iptables -t mangle -A NETPILOT_WHITELIST -m mac --mac-source AA:BB:CC:DD:EE:FF -j MARK --set-mark 1")
    print("iptables -t mangle -A NETPILOT_WHITELIST -m mac --mac-source AA:BB:CC:DD:EE:FF -j RETURN")
    print("# Default rule:")
    print("iptables -t mangle -A NETPILOT_WHITELIST -j MARK --set-mark 98")
    
    print("\nPHASE 4: Activate")
    print("iptables -t mangle -A FORWARD -j NETPILOT_WHITELIST")

if __name__ == "__main__":
    print("NetPilot Naive Mode Activation Test")
    print("====================================")
    
    # Show manual commands first
    demonstrate_manual_commands()
    
    # Run tests
    if test_naive_approach():
        sys.exit(0)
    else:
        sys.exit(1)
