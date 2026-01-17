#!/usr/bin/env python3
"""Quick test of save/reload functionality"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "your-secure-admin-token"
headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

print("\n" + "="*60)
print("TEST 1: Get initial config")
print("="*60)
r = requests.get(f"{BASE_URL}/api/v1/config")
response = r.json()
config1 = response.get('config', response)  # Extract nested config
print(f"Initial velocity_threshold: {config1.get('velocity_threshold')}")
print(f"Initial high_risk_threshold: {config1.get('high_risk_threshold')}")

print("\n" + "="*60)
print("TEST 2: Save new thresholds")
print("="*60)
update_data = {
    "velocity_threshold": 8,
    "high_risk_threshold": 0.92,
    "flag_risk_threshold": 0.72,
    "amount_spike_multiplier": 3.8,
    "baseline_amount": 2000.0,
    "anomaly_score_threshold": 0.78
}
print(f"Saving: velocity={update_data['velocity_threshold']}, high_risk={update_data['high_risk_threshold']}")
r = requests.post(f"{BASE_URL}/api/admin/config", json=update_data, headers=headers)
print(f"Response status: {r.status_code}")
if r.status_code == 200:
    print("✅ Save successful")
else:
    print(f"❌ Save failed: {r.text}")

time.sleep(0.5)

print("\n" + "="*60)
print("TEST 3: Verify values persisted")
print("="*60)
r = requests.get(f"{BASE_URL}/api/v1/config")
response = r.json()
config2 = response.get('config', response)  # Extract nested config
print(f"After save velocity_threshold: {config2.get('velocity_threshold')}")
print(f"After save high_risk_threshold: {config2.get('high_risk_threshold')}")

if (config2.get('velocity_threshold') == 8 and config2.get('high_risk_threshold') == 0.92):
    print("✅ Values persisted correctly!")
else:
    print("❌ Values NOT persisted")

print("\n" + "="*60)
print("TEST 4: Save features")
print("="*60)
features_data = {
    "enabled_checks": {
        "velocity": True,
        "geo_location": False,
        "amount_spike": True,
        "midnight": False,
        "ml_risk_score": True,
        "anomaly_detection": False
    }
}
print(f"Saving features: {features_data}")
r = requests.post(f"{BASE_URL}/api/admin/config", json=features_data, headers=headers)
print(f"Response status: {r.status_code}")
if r.status_code == 200:
    print("✅ Features save successful")
else:
    print(f"❌ Features save failed: {r.text}")

time.sleep(0.5)

print("\n" + "="*60)
print("TEST 5: Verify features persisted")
print("="*60)
r = requests.get(f"{BASE_URL}/api/v1/config")
response = r.json()
config3 = response.get('config', response)  # Extract nested config
if 'enabled_checks' in config3:
    print(f"enabled_checks: {config3['enabled_checks']}")
    if config3['enabled_checks'].get('velocity') and not config3['enabled_checks'].get('geo_location'):
        print("✅ Features persisted correctly!")
    else:
        print("❌ Features NOT persisted correctly")
else:
    print("⚠️  enabled_checks not in config")

print("\n" + "="*60)
print("ALL TESTS COMPLETE")
print("="*60)
