#!/usr/bin/env python3
"""Simple test script to verify admin API endpoints"""

import requests
import json
import time

API_BASE = "http://localhost:8000"
ADMIN_TOKEN = "your-secure-admin-token"

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 60)
print("Testing Admin API Endpoints")
print("=" * 60)

# Test 1: Get current config
print("\n1. Testing GET /api/v1/config (no auth required)")
try:
    response = requests.get(f"{API_BASE}/api/v1/config")
    print(f"   Status: {response.status_code}")
    print(f"   Current config: {json.dumps(response.json(), indent=2)[:200]}...")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Update config
print("\n2. Testing POST /api/admin/config (with auth)")
try:
    payload = {
        "velocity_threshold": 5,
        "high_risk_threshold": 0.85
    }
    print(f"   Sending: {payload}")
    response = requests.post(
        f"{API_BASE}/api/admin/config",
        headers=headers,
        json=payload
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Response: {json.dumps(response.json(), indent=2)[:300]}...")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Get admin logs
print("\n3. Testing GET /api/admin/logs (with auth)")
try:
    response = requests.get(
        f"{API_BASE}/api/admin/logs",
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Logs count: {data.get('count', 0)}")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Get anomaly patterns
print("\n4. Testing GET /api/admin/anomaly-patterns (with auth)")
try:
    response = requests.get(
        f"{API_BASE}/api/admin/anomaly-patterns",
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Patterns count: {data.get('count', 0)}")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
