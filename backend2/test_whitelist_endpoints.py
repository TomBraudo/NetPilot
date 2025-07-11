#!/usr/bin/env python3
"""
Test script for the new whitelist endpoints
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/whitelist-new"

def test_whitelist_endpoints():
    """Test all whitelist endpoints"""
    
    print("Testing Whitelist Endpoints")
    print("=" * 50)
    
    # Test 1: Get whitelist (should be empty initially)
    print("\n1. Testing GET /api/whitelist-new/")
    try:
        response = requests.get(API_BASE)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Add device to whitelist
    print("\n2. Testing POST /api/whitelist-new/")
    test_device = {
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "device_name": "Test Device",
        "description": "Testing whitelist functionality"
    }
    
    try:
        response = requests.post(API_BASE, json=test_device)
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
        print(f"\n3. Testing GET /api/whitelist-new/{device_id}")
        try:
            response = requests.get(f"{API_BASE}/{device_id}")
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
        print(f"\n4. Testing PUT /api/whitelist-new/{device_id}")
        update_data = {
            "device_name": "Updated Test Device",
            "description": "Updated description for whitelisting"
        }
        
        try:
            response = requests.put(f"{API_BASE}/{device_id}", json=update_data)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 5: Get all devices again
    print("\n5. Testing GET /api/whitelist-new/ (after adding device)")
    try:
        response = requests.get(API_BASE)
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
        print(f"\n6. Testing DELETE /api/whitelist-new/{device_id}")
        try:
            response = requests.delete(f"{API_BASE}/{device_id}")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 7: Verify device is deleted
    print("\n7. Testing GET /api/whitelist-new/ (after deletion)")
    try:
        response = requests.get(API_BASE)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("Whitelist endpoint testing completed!")

if __name__ == "__main__":
    test_whitelist_endpoints() 