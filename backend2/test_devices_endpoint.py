#!/usr/bin/env python3
"""
Simple test script to check if the devices endpoint is working
Run this from the backend2 directory
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:5000"
ROUTER_ID = "e4fbea8e8f1c372c919be32613793c6c1e8313dd8a9b38bef9a9b45114ad1c1f"  # From the logs

def test_devices_endpoint():
    print("🧪 Testing devices endpoint...")
    
    # Test GET /api/devices
    print("📡 Testing GET /api/devices")
    try:
        response = requests.get(f"{BASE_URL}/api/devices?routerId={ROUTER_ID}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ GET devices endpoint working")
            data = response.json()
            print(f"Found {len(data)} devices")
        else:
            print("❌ GET devices endpoint failed")
            
    except Exception as e:
        print(f"❌ Error testing GET devices: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test POST /api/devices/bulk
    print("📡 Testing POST /api/devices/bulk")
    test_devices = [
        {
            "ip": "192.168.1.100",
            "mac": "aa:bb:cc:dd:ee:ff",
            "hostname": "Test Device",
            "type": "laptop"
        }
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/devices/bulk?routerId={ROUTER_ID}",
            json={"devices": test_devices},
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ POST bulk devices endpoint working")
        else:
            print("❌ POST bulk devices endpoint failed")
            
    except Exception as e:
        print(f"❌ Error testing POST bulk devices: {e}")

    print("\n" + "="*50 + "\n")
    
    # Test POST /api/devices/validate
    print("📡 Testing POST /api/devices/validate")
    test_device_identifiers = [
        "192.168.1.100",  # IP address
        "550e8400-e29b-41d4-a716-446655440000"  # Example UUID
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/devices/validate?routerId={ROUTER_ID}",
            json={"devices": test_device_identifiers},
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ POST validate devices endpoint working")
            data = response.json()
            print(f"Valid devices: {data.get('data', {}).get('total_valid', 0)}")
            print(f"Invalid devices: {data.get('data', {}).get('total_invalid', 0)}")
        else:
            print("❌ POST validate devices endpoint failed")
            
    except Exception as e:
        print(f"❌ Error testing POST validate devices: {e}")

if __name__ == "__main__":
    test_devices_endpoint()
