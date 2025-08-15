#!/usr/bin/env python3
"""
Test script to verify the simplified device group creation works correctly
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Add the backend2 directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.device_group_service import create_device_group, get_user_device_groups
from services.device_service import get_user_devices
import uuid

def test_simplified_group_creation():
    """Test the simplified group creation flow"""
    print("🧪 Testing Simplified Device Group Creation")
    print("=" * 50)
    
    # Test parameters (use your actual user_id and router_id)
    test_user_id = str(uuid.uuid4())  # Replace with actual user ID
    test_router_id = "test_router_123"  # Replace with actual router ID
    
    try:
        # Step 1: Check if we have any devices for this user/router
        print("Step 1: Checking existing devices...")
        devices = get_user_devices(test_user_id, test_router_id)
        print(f"Found {len(devices)} existing devices")
        
        if len(devices) == 0:
            print("⚠️  No devices found. Create some devices first to test group creation with devices.")
            device_ids = []
        else:
            device_ids = [str(devices[0].id)]  # Use first device for testing
            print(f"Will use device {device_ids[0]} for testing")
        
        # Step 2: Create a test group
        print("\nStep 2: Creating device group...")
        group_name = f"Test Group {uuid.uuid4().hex[:8]}"
        
        group = create_device_group(
            user_id=test_user_id,
            router_id=test_router_id,
            name=group_name,
            description="Test group created by simplified flow",
            device_ids=device_ids
        )
        
        print(f"✅ Successfully created group: {group.name}")
        print(f"   Group ID: {group.id}")
        print(f"   Devices in group: {len(group.devices)}")
        
        # Step 3: Verify group can be retrieved
        print("\nStep 3: Verifying group retrieval...")
        groups = get_user_device_groups(test_user_id, test_router_id)
        created_group = next((g for g in groups if g.id == group.id), None)
        
        if created_group:
            print(f"✅ Group found in database with {len(created_group.devices)} devices")
            print("✅ All tests passed! Simplified flow is working correctly.")
            return True
        else:
            print("❌ Group not found in database")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simplified_group_creation()
    sys.exit(0 if success else 1)
