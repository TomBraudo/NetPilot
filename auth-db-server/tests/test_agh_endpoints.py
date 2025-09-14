#!/usr/bin/env python3
"""
Test script for AGH API endpoints (/api/agh)

This script validates that the AGH endpoints are wired correctly by making
HTTP requests against a running backend2 server in development mode.

Run the server first in dev mode:
  python server.py -d 00000000-0000-0000-0000-000000000001

Then run this script:
  python backend2/test_agh_endpoints.py
"""

import requests
import json
import sys
import os


def test_agh_endpoints():
    base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:5000")
    router_id = os.getenv("TEST_ROUTER_ID", "11111111-1111-1111-1111-111111111111")

    print("\n🧪 Testing AGH API Endpoints")
    print("=" * 60)

    tests = [
        {
            "desc": "List categories",
            "method": "GET",
            "url": f"{base_url}/api/agh/categories?routerId={router_id}",
        },
        {
            "desc": "Create category",
            "method": "POST",
            "url": f"{base_url}/api/agh/categories",
            "json": {"routerId": router_id, "category": "test-category", "domains": ["example.com", "test.local"]},
        },
        {
            "desc": "Get category domains",
            "method": "GET",
            "url": f"{base_url}/api/agh/categories/test-category/domains?routerId={router_id}",
        },
        {
            "desc": "Replace category domains",
            "method": "PUT",
            "url": f"{base_url}/api/agh/categories/test-category/domains",
            "json": {"routerId": router_id, "domains": ["newdomain.com", "another.net"]},
        },
        {
            "desc": "Get device effective rules by IP",
            "method": "GET",
            "url": f"{base_url}/api/agh/device/rules?routerId={router_id}&ip=192.168.1.100",
        },
        {
            "desc": "Bulk get devices rules",
            "method": "POST",
            "url": f"{base_url}/api/agh/devices/rules",
            "json": {"routerId": router_id, "devices": [{"ip": "192.168.1.101"}, {"mac": "AA:BB:CC:DD:EE:FF"}]},
        },
        {
            "desc": "Set device rules",
            "method": "POST",
            "url": f"{base_url}/api/agh/device/rules",
            "json": {"routerId": router_id, "device": {"ip": "192.168.1.102"}, "categories": ["test-category"]},
        },
        {
            "desc": "Set devices rules (bulk)",
            "method": "POST",
            "url": f"{base_url}/api/agh/devices/rules/set",
            "json": {"routerId": router_id, "devices": [{"ip": "192.168.1.103"}], "categories": ["test-category"]},
        },
        {
            "desc": "Clear device rules",
            "method": "DELETE",
            "url": f"{base_url}/api/agh/device/rules",
            "json": {"routerId": router_id, "device": {"ip": "192.168.1.102"}},
        },
        {
            "desc": "Clear devices rules (bulk)",
            "method": "DELETE",
            "url": f"{base_url}/api/agh/devices/rules",
            "json": {"routerId": router_id, "devices": [{"ip": "192.168.1.103"}]},
        },
    ]

    session = requests.Session()
    headers = {"Content-Type": "application/json"}

    for t in tests:
        print(f"\n📡 {t['desc']}")
        print(f"   {t['method']} {t['url']}")
        try:
            if t["method"] == "GET":
                resp = session.get(t["url"], headers=headers, timeout=15)
            elif t["method"] == "POST":
                resp = session.post(t["url"], headers=headers, json=t.get("json", {}), timeout=15)
            elif t["method"] == "PUT":
                resp = session.put(t["url"], headers=headers, json=t.get("json", {}), timeout=15)
            elif t["method"] == "DELETE":
                resp = session.delete(t["url"], headers=headers, json=t.get("json", {}), timeout=15)
            else:
                print("   ❌ Unsupported method")
                continue

            print(f"   Status: {resp.status_code}")
            try:
                data = resp.json()
                keys = list(data.keys()) if isinstance(data, dict) else []
                print(f"   JSON keys: {keys}")
                # Show a short snippet of data
                print(f"   Body: {json.dumps(data, indent=2)[:300]}...")
            except Exception:
                print(f"   Body: {resp.text[:200]}...")
        except requests.exceptions.ConnectionError:
            print("   🔌 Connection Error: Is the server running in dev mode?")
        except Exception as e:
            print(f"   💥 Error: {e}")

    print("\n" + "=" * 60)
    print("🏁 AGH endpoint test completed")


if __name__ == "__main__":
    test_agh_endpoints()


