#!/usr/bin/env python3
"""
Test script for Monitor API endpoints

This script tests the monitor endpoints to ensure they are properly configured
and can handle requests correctly.
"""

import requests
import json
import sys
import os

# Add the backend2 directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_monitor_endpoints():
    """Test all monitor endpoints"""
    
    base_url = "http://localhost:5000"  # Assuming the server runs on port 5000
    
    # Test data - we'll send requests without authentication for now
    headers = {
        "Content-Type": "application/json",
        "X-Dev-User-ID": "test-user-123",  # For development mode
        "X-Router-ID": "test-router-456",
        "X-Session-ID": "test-session-789"
    }
    
    endpoints_to_test = [
        {
            "url": f"{base_url}/api/monitor/current",
            "method": "GET",
            "description": "Get current devices monitor data"
        },
        {
            "url": f"{base_url}/api/monitor/last-week", 
            "method": "GET",
            "description": "Get last week devices monitor data"
        },
        {
            "url": f"{base_url}/api/monitor/last-month",
            "method": "GET", 
            "description": "Get last month devices monitor data"
        },
        {
            "url": f"{base_url}/api/monitor/device/AA:BB:CC:DD:EE:FF?period=current",
            "method": "GET",
            "description": "Get device monitor data by MAC address"
        }
    ]
    
    print("🧪 Testing Monitor API Endpoints")
    print("=" * 50)
    
    for endpoint in endpoints_to_test:
        print(f"\n📡 Testing: {endpoint['description']}")
        print(f"   URL: {endpoint['url']}")
        print(f"   Method: {endpoint['method']}")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'], headers=headers, timeout=10)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Success!")
                try:
                    data = response.json()
                    print(f"   📊 Response structure: {list(data.keys()) if isinstance(data, dict) else 'List/Other'}")
                except:
                    print("   📄 Non-JSON response")
            else:
                print(f"   ❌ Failed: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print("   🔌 Connection Error: Server might not be running")
        except Exception as e:
            print(f"   💥 Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_monitor_endpoints()
