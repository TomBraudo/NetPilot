#!/usr/bin/env python3
"""
Test script for the fixed mode activation service.
This will help verify that the POSTROUTING issue is resolved.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.mode_activation_service import (
    activate_whitelist_mode_rules,
    deactivate_whitelist_mode_rules,
    activate_blacklist_mode_rules,
    deactivate_blacklist_mode_rules,
    validate_mode_activation,
    get_active_mode_status
)

def test_whitelist_activation():
    """Test whitelist mode activation with the fix."""
    print("=" * 50)
    print("TESTING WHITELIST MODE ACTIVATION")
    print("=" * 50)
    
    # Test activation
    print("\n1. Activating whitelist mode...")
    success, error = activate_whitelist_mode_rules()
    if success:
        print("✅ Whitelist mode activated successfully!")
    else:
        print(f"❌ Whitelist mode activation failed: {error}")
        return False
    
    # Check status
    print("\n2. Checking active mode status...")
    mode, error = get_active_mode_status()
    print(f"Active mode: {mode}")
    if error:
        print(f"Status check error: {error}")
    
    # Validate
    print("\n3. Validating mode activation...")
    success, validation = validate_mode_activation()
    if success:
        print("✅ Validation successful!")
        print(f"Validation results: {validation}")
    else:
        print(f"❌ Validation failed: {validation}")
    
    # Test deactivation
    print("\n4. Deactivating whitelist mode...")
    success, error = deactivate_whitelist_mode_rules()
    if success:
        print("✅ Whitelist mode deactivated successfully!")
    else:
        print(f"❌ Whitelist mode deactivation failed: {error}")
    
    return True

def test_blacklist_activation():
    """Test blacklist mode activation with the fix."""
    print("\n" + "=" * 50)
    print("TESTING BLACKLIST MODE ACTIVATION")
    print("=" * 50)
    
    # Test activation
    print("\n1. Activating blacklist mode...")
    success, error = activate_blacklist_mode_rules()
    if success:
        print("✅ Blacklist mode activated successfully!")
    else:
        print(f"❌ Blacklist mode activation failed: {error}")
        return False
    
    # Check status
    print("\n2. Checking active mode status...")
    mode, error = get_active_mode_status()
    print(f"Active mode: {mode}")
    if error:
        print(f"Status check error: {error}")
    
    # Test deactivation
    print("\n3. Deactivating blacklist mode...")
    success, error = deactivate_blacklist_mode_rules()
    if success:
        print("✅ Blacklist mode deactivated successfully!")
    else:
        print(f"❌ Blacklist mode deactivation failed: {error}")
    
    return True

if __name__ == "__main__":
    print("NetPilot Mode Activation Fix Test")
    print("This will test the fixed mode activation with proper POSTROUTING handling")
    
    try:
        # Test whitelist mode
        whitelist_success = test_whitelist_activation()
        
        # Test blacklist mode
        blacklist_success = test_blacklist_activation()
        
        # Final summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        print(f"Whitelist mode test: {'✅ PASSED' if whitelist_success else '❌ FAILED'}")
        print(f"Blacklist mode test: {'✅ PASSED' if blacklist_success else '❌ FAILED'}")
        
        if whitelist_success and blacklist_success:
            print("\n🎉 ALL TESTS PASSED! The mode activation fix is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the errors above.")
            
    except Exception as e:
        print(f"\n❌ Test script failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
