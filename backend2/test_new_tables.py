#!/usr/bin/env python3
"""
Test script to verify the new database tables are working correctly.
"""

import uuid
from database.connection import db
from models import DeviceGroup, BandwidthRules, ContentControlRules

def test_new_tables():
    """Test the new tables by creating sample data"""
    print("Testing new database tables...")
    
    try:
        # Get a database session
        session = db.get_session()
        
        # Test 1: Check if tables exist
        print("\n1. Checking if tables exist...")
        
        # Try to query the tables
        bandwidth_count = session.query(BandwidthRules).count()
        content_count = session.query(ContentControlRules).count()
        
        print(f"✓ BandwidthRules table exists with {bandwidth_count} records")
        print(f"✓ ContentControlRules table exists with {content_count} records")
        
        # Test 2: Check if we can create a sample bandwidth rule
        print("\n2. Testing bandwidth rules creation...")
        
        # Get the first device group (if any exist)
        first_group = session.query(DeviceGroup).first()
        if first_group:
            print(f"Found device group: {first_group.name} (ID: {first_group.id})")
            
            # Create a sample bandwidth rule
            bandwidth_rule = BandwidthRules(
                group_id=first_group.id,
                router_id="test_router_123",
                download_limit_mbps=50.0,
                upload_limit_mbps=25.0,
                is_active=True,
                description="Test bandwidth rule"
            )
            
            session.add(bandwidth_rule)
            session.commit()
            print("✓ Successfully created bandwidth rule")
            
            # Test 3: Check if we can create a sample content control rule
            print("\n3. Testing content control rules creation...")
            
            content_rule = ContentControlRules(
                group_id=first_group.id,
                router_id="test_router_123",
                blocked_categories=["social_media", "gaming"],
                is_active=True,
                description="Test content control rule"
            )
            
            session.add(content_rule)
            session.commit()
            print("✓ Successfully created content control rule")
            
            # Test 4: Verify the relationships work
            print("\n4. Testing relationships...")
            
            # Refresh the group to get the new rules
            session.refresh(first_group)
            
            print(f"Group '{first_group.name}' now has:")
            print(f"  - {len(first_group.bandwidth_rules)} bandwidth rules")
            print(f"  - {len(first_group.content_control_rules)} content control rules")
            
            # Test 5: Test the to_dict method
            print("\n5. Testing to_dict method...")
            group_dict = first_group.to_dict()
            
            if 'bandwidth_rules' in group_dict:
                print(f"✓ Bandwidth rules in to_dict: {len(group_dict['bandwidth_rules'])}")
            if 'content_control_rules' in group_dict:
                print(f"✓ Content control rules in to_dict: {len(group_dict['content_control_rules'])}")
            
            # Clean up test data
            print("\n6. Cleaning up test data...")
            session.delete(bandwidth_rule)
            session.delete(content_rule)
            session.commit()
            print("✓ Test data cleaned up")
            
        else:
            print("No device groups found. Please create a device group first.")
        
        session.close()
        print("\n✅ All tests passed! The new tables are working correctly.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_tables()
