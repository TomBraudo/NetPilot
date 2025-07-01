#!/usr/bin/env python3
"""
Test script to validate IP-only functionality for whitelist and blacklist
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.device_rule_service import _validate_ip_address

def test_ip_validation():
    """Test IP validation function"""
    print("Testing IP validation...")
    
    # Valid IP addresses
    valid_ips = [
        "192.168.1.1",
        "10.0.0.1", 
        "172.16.0.1",
        "8.8.8.8",
        "127.0.0.1",
        "255.255.255.255",
        "0.0.0.0"
    ]
    
    # Invalid IP addresses and MAC addresses
    invalid_inputs = [
        "192.168.1.256",  # Invalid IP (octet > 255)
        "192.168.1",      # Incomplete IP
        "192.168.1.1.1",  # Too many octets
        "aa:bb:cc:dd:ee:ff",  # MAC address
        "AA:BB:CC:DD:EE:FF",  # MAC address uppercase
        "aa-bb-cc-dd-ee-ff",  # MAC address with dashes
        "aabbccddeeff",       # MAC address without separators
        "not.an.ip.address",  # Invalid format
        "256.256.256.256",    # All octets invalid
        "",                   # Empty string
        None,                 # None value
        "192.168.1.1/24",     # CIDR notation
        "192.168.1.1:8080",   # IP with port
    ]
    
    print("\nTesting valid IP addresses:")
    for ip in valid_ips:
        result = _validate_ip_address(ip)
        print(f"  {ip}: {'✓' if result else '✗'}")
        if not result:
            print(f"    ERROR: {ip} should be valid!")
    
    print("\nTesting invalid inputs:")
    for invalid_input in invalid_inputs:
        result = _validate_ip_address(invalid_input) if invalid_input is not None else None
        print(f"  {invalid_input}: {'✗' if not result else '✓'}")
        if result:
            print(f"    ERROR: {invalid_input} should be invalid!")
    
    print("\nIP validation test completed.")

if __name__ == "__main__":
    test_ip_validation()
