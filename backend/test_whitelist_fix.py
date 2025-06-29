#!/usr/bin/env python3
"""
Quick test to check whitelisted devices and router state.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.router_state_manager import get_router_state
from services.mode_activation_service import activate_whitelist_mode_rules, deactivate_whitelist_mode_rules

def check_whitelist_state():
    """Check what devices are currently whitelisted."""
    print("=" * 50)
    print("CHECKING WHITELIST STATE")
    print("=" * 50)
    
    try:
        state = get_router_state()
        
        print("\n1. Router State Structure:")
        print(f"Available keys: {list(state.keys())}")
        
        print("\n2. Devices Structure:")
        devices = state.get('devices', {})
        print(f"Devices keys: {list(devices.keys())}")
        
        print("\n3. Whitelisted Devices:")
        whitelist = devices.get('whitelist', [])
        print(f"Number of whitelisted devices: {len(whitelist)}")
        for i, device in enumerate(whitelist):
            print(f"  {i+1}. {device}")
        
        print("\n4. Blacklisted Devices:")
        blacklist = devices.get('blacklist', [])
        print(f"Number of blacklisted devices: {len(blacklist)}")
        for i, device in enumerate(blacklist):
            print(f"  {i+1}. {device}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_fixed_whitelist():
    """Test the fixed whitelist activation."""
    print("\n" + "=" * 50)
    print("TESTING FIXED WHITELIST ACTIVATION")
    print("=" * 50)
    
    try:
        # First deactivate to clean state
        print("\n1. Deactivating current mode...")
        deactivate_whitelist_mode_rules()
        
        # Now activate with the fixed version
        print("\n2. Activating whitelist mode with fixes...")
        success, error = activate_whitelist_mode_rules()
        
        if success:
            print("✅ Whitelist mode activated successfully!")
            print("\nNow test your internet speed and see if your device is unlimited.")
            print("If it's still limited, run these commands on the router:")
            print("  iptables -t mangle -L NETPILOT_WHITELIST -n --line-numbers -v")
            print("  # Check if your device rules are BEFORE the default rule")
        else:
            print(f"❌ Whitelist mode activation failed: {error}")
            
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_whitelist_state()
    test_fixed_whitelist()
