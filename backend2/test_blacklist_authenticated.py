#!/usr/bin/env python3
"""
Test script for the blacklist endpoints with authentication
"""

import requests
import json
import time
import webbrowser
from urllib.parse import urlparse, parse_qs

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/blacklist-new"

def authenticate_with_google():
    """Authenticate with Google OAuth and return session"""
    session = requests.Session()
    
    print("Starting Google OAuth authentication...")
    
    # Step 1: Get the login URL
    try:
        response = session.get(f"{BASE_URL}/login")
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 302:  # Redirect to Google
            auth_url = response.headers.get('Location')
            print(f"Auth URL: {auth_url}")
            
            # Open browser for user to authenticate
            print("Opening browser for Google authentication...")
            webbrowser.open(auth_url)
            
            # Wait for user to complete authentication
            input("Please complete the Google authentication in your browser and press Enter to continue...")
            
            # Step 2: Check if we're authenticated by trying to access a protected endpoint
            print("Checking authentication status...")
            test_response = session.get(f"{BASE_URL}/api/health")
            print(f"Health check status: {test_response.status_code}")
            
            if test_response.status_code == 200:
                print("✅ Authentication successful!")
                return session
            else:
                print("❌ Authentication failed")
                return None
                
        else:
            print(f"Unexpected response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Authentication error: {e}")
        return None

def test_blacklist_endpoints_authenticated(session):
    """Test all blacklist endpoints with authentication"""
    
    print("\nTesting Blacklist Endpoints (Authenticated)")
    print("=" * 50)
    
    # Test 1: Get blacklist (should be empty initially)
    print("\n1. Testing GET /api/blacklist-new/")
    try:
        response = session.get(API_BASE)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Add device to blacklist
    print("\n2. Testing POST /api/blacklist-new/")
    test_device = {
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "device_name": "Test Device",
        "reason": "Testing blacklist functionality"
    }
    
    try:
        response = session.post(API_BASE, json=test_device)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            device_id = data.get('data', {}).get('id')
        else:
            print(f"Error: {response.text}")
            device_id = None
    except Exception as e:
        print(f"Error: {e}")
        device_id = None
    
    # Test 3: Get specific device
    if device_id:
        print(f"\n3. Testing GET /api/blacklist-new/{device_id}")
        try:
            response = session.get(f"{API_BASE}/{device_id}")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 4: Update device
    if device_id:
        print(f"\n4. Testing PUT /api/blacklist-new/{device_id}")
        update_data = {
            "device_name": "Updated Test Device",
            "reason": "Updated reason for blacklisting"
        }
        
        try:
            response = session.put(f"{API_BASE}/{device_id}", json=update_data)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 5: Get all devices again
    print("\n5. Testing GET /api/blacklist-new/ (after adding device)")
    try:
        response = session.get(API_BASE)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 6: Delete device
    if device_id:
        print(f"\n6. Testing DELETE /api/blacklist-new/{device_id}")
        try:
            response = session.delete(f"{API_BASE}/{device_id}")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 7: Verify device is deleted
    print("\n7. Testing GET /api/blacklist-new/ (after deletion)")
    try:
        response = session.get(API_BASE)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("Authenticated blacklist endpoint testing completed!")

def main():
    """Main test function"""
    print("Blacklist Endpoint Authentication Test")
    print("=" * 50)
    
    # Authenticate
    session = authenticate_with_google()
    
    if session:
        # Test endpoints with authentication
        test_blacklist_endpoints_authenticated(session)
    else:
        print("❌ Could not authenticate. Exiting.")

if __name__ == "__main__":
    main() 