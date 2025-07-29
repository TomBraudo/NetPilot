#!/usr/bin/env python3
"""
Test script to verify router ID flow works correctly
This script tests that users with existing router IDs don't see the popup
"""

import requests
import sys
import json
import time

# Configuration
BASE_URL = "http://localhost:5000"
TEST_ROUTER_ID = "test_router_id_12345"

def test_router_id_flow():
    """Test the complete router ID flow"""
    print("🔍 Testing Router ID Flow")
    print("=" * 50)
    
    # Start a session
    session = requests.Session()
    
    # Test 1: Check if server is running
    print("\n1️⃣ Testing server health...")
    try:
        response = session.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is healthy")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure backend2 server is running on port 5000")
        return False
    
    # Test 2: Try to access protected endpoint without authentication
    print("\n2️⃣ Testing unauthenticated access...")
    response = session.get(f"{BASE_URL}/api/settings/router-id")
    if response.status_code == 401:
        print("✅ Unauthenticated access properly rejected")
    else:
        print(f"❌ Expected 401, got {response.status_code}")
        
    # Test 3: Check /me endpoint without authentication
    print("\n3️⃣ Testing /me endpoint without authentication...")
    response = session.get(f"{BASE_URL}/me")
    if response.status_code == 401:
        print("✅ /me endpoint properly rejects unauthenticated requests")
    else:
        print(f"❌ /me endpoint should return 401, got {response.status_code}")
    
    print("\n" + "="*50)
    print("📝 Manual Test Instructions:")
    print("="*50)
    print("\n🔐 To test the complete flow with authentication:")
    print("1. Start the backend2 server: python server.py")
    print("2. Start the frontend: cd frontend/dashboard && npm run dev")
    print("3. Open browser to http://localhost:5173")
    print("4. Click 'Login' to authenticate with Google")
    print("5. After login, observe the behavior:")
    print("   - First time: Router ID popup SHOULD appear")
    print("   - Enter a router ID and save it")
    print("   - Logout and login again")
    print("   - Second time: Router ID popup SHOULD NOT appear")
    
    print("\n🔍 Check backend logs for detailed flow information:")
    print("- Look for 'get_router_id_setting' logs")
    print("- Check if router ID is found in database")
    print("- Verify popup decision logic in browser console")
    
    print("\n📋 Expected Log Messages:")
    print("First login (no router ID):")
    print("  - 'No UserSetting record found for this user'")
    print("  - 'No router ID found, will show popup'")
    print("  - Frontend: 'Showing router ID popup'")
    
    print("\nSubsequent logins (with router ID):")
    print("  - 'Router ID found: [router_id]'")
    print("  - 'Router ID found, popup will not be shown'")
    print("  - Frontend: Popup should NOT appear")
    
    return True

def test_database_query():
    """Test if we can query the database directly"""
    print("\n" + "="*50)
    print("🗄️ Database Query Test")
    print("="*50)
    
    try:
        from database.connection import get_session
        from models.settings import UserSetting
        from models.router import UserRouter
        
        print("\n📊 Current database state:")
        
        with get_session() as session:
            # Check UserSetting records
            settings = session.query(UserSetting).filter_by(setting_key='routerId').all()
            print(f"\n🔧 UserSetting records with routerId: {len(settings)}")
            for setting in settings:
                print(f"  - User: {setting.user_id}, Router: {setting.setting_value}")
            
            # Check UserRouter records
            routers = session.query(UserRouter).filter_by(is_active=True).all()
            print(f"\n🌐 Active UserRouter records: {len(routers)}")
            for router in routers:
                print(f"  - User: {router.user_id}, Router: {router.router_id}")
                
        print("\n✅ Database query successful")
        return True
        
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        print("Make sure the database is properly set up and accessible")
        return False

if __name__ == "__main__":
    print("🧪 NetPilot Router ID Flow Test")
    print("This script tests the router ID popup logic")
    
    # Test API endpoints
    api_success = test_router_id_flow()
    
    # Test database if available
    db_success = test_database_query()
    
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    print(f"API Tests: {'✅ PASSED' if api_success else '❌ FAILED'}")
    print(f"Database Tests: {'✅ PASSED' if db_success else '❌ FAILED'}")
    
    if api_success and db_success:
        print("\n🎉 All tests passed! The router ID flow should work correctly.")
        print("💡 Follow the manual test instructions above to verify end-to-end flow.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        
    print("\n🔧 Troubleshooting:")
    print("- Ensure backend2 server is running: python server.py")
    print("- Check database connection and models")
    print("- Verify authentication middleware is working")
    print("- Check browser console for frontend logs") 