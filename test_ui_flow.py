#!/usr/bin/env python3
"""
Comprehensive UI flow test - simulates real user interactions
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "your-secure-admin-token"
headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

def test_get_config():
    """Test 1: Get current configuration (what UI loads on page load)"""
    print("\n" + "="*60)
    print("TEST 1: GET /api/v1/config (Page Load)")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/config")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ PASS: Can load configuration")
            return response.json()
        else:
            print("❌ FAIL: Could not load configuration")
            return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

def test_get_stats():
    """Test 2: Get stats (dashboard numbers)"""
    print("\n" + "="*60)
    print("TEST 2: GET /api/v1/stats (Dashboard Stats)")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/stats")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ PASS: Can load statistics")
            return response.json()
        else:
            print("❌ FAIL: Could not load statistics")
            return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

def test_save_thresholds():
    """Test 3: Save thresholds (what saveThresholds() does)"""
    print("\n" + "="*60)
    print("TEST 3: POST /api/admin/config (Save Thresholds)")
    print("="*60)
    
    update_data = {
        "velocity_threshold": 7,
        "high_risk_threshold": 0.90,
        "flag_risk_threshold": 0.70,
        "amount_spike_multiplier": 3.5,
        "baseline_amount": 1500.0,
        "anomaly_score_threshold": 0.75
    }
    
    print(f"Sending: {json.dumps(update_data, indent=2)}")
    print(f"Headers: {json.dumps({k: v for k, v in headers.items() if k != 'Content-Type'}, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/config",
            json=update_data,
            headers=headers
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ PASS: Thresholds saved successfully")
            return True
        else:
            print(f"❌ FAIL: Status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_save_features():
    """Test 4: Save feature toggles (what saveFeatures() does)"""
    print("\n" + "="*60)
    print("TEST 4: POST /api/admin/config (Save Features)")
    print("="*60)
    
    update_data = {
        "enabled_checks": {
            "velocity": True,
            "geo_location": True,
            "amount_spike": False,
            "midnight": True,
            "ml_risk_score": True,
            "anomaly_detection": True
        }
    }
    
    print(f"Sending: {json.dumps(update_data, indent=2)}")
    print(f"Headers: {json.dumps({k: v for k, v in headers.items() if k != 'Content-Type'}, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/config",
            json=update_data,
            headers=headers
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ PASS: Features saved successfully")
            return True
        else:
            print(f"❌ FAIL: Status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_get_audit_logs():
    """Test 5: Get audit logs (what admin sees in logs tab)"""
    print("\n" + "="*60)
    print("TEST 5: GET /api/admin/logs (Audit Logs)")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/logs",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total logs: {len(data)}")
            print(f"First 3 logs: {json.dumps(data[:3], indent=2)}")
            print("✅ PASS: Can retrieve audit logs")
            return True
        else:
            print(f"❌ FAIL: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_admin_dashboard():
    """Test 6: Get admin dashboard (what /api/admin/dashboard returns)"""
    print("\n" + "="*60)
    print("TEST 6: GET /api/admin/dashboard (Admin Dashboard)")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ PASS: Can retrieve admin dashboard data")
            return True
        else:
            print(f"❌ FAIL: Status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_verify_threshold_persistence():
    """Test 7: Verify thresholds were actually saved"""
    print("\n" + "="*60)
    print("TEST 7: Verify Threshold Persistence")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/config")
        config = response.json()
        
        print(f"Current config: {json.dumps(config, indent=2)}")
        
        # Check if we saved the values correctly
        if (config.get('velocity_threshold') == 7 and
            config.get('high_risk_threshold') == 0.90 and
            config.get('flag_risk_threshold') == 0.70 and
            config.get('amount_spike_multiplier') == 3.5):
            print("✅ PASS: Thresholds persisted correctly")
            return True
        else:
            print("⚠️  WARNING: Some threshold values don't match what we saved")
            print(f"  velocity_threshold: {config.get('velocity_threshold')} (expected 7)")
            print(f"  high_risk_threshold: {config.get('high_risk_threshold')} (expected 0.90)")
            print(f"  flag_risk_threshold: {config.get('flag_risk_threshold')} (expected 0.70)")
            print(f"  amount_spike_multiplier: {config.get('amount_spike_multiplier')} (expected 3.5)")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def run_all_tests():
    """Run complete test suite"""
    print("\n" + "█"*60)
    print("█ COMPREHENSIVE UI FLOW TEST SUITE")
    print("█"*60)
    
    results = []
    
    # Test sequence (mimics user interaction flow)
    results.append(("GET Config (Page Load)", test_get_config() is not None))
    results.append(("GET Stats (Dashboard)", test_get_stats() is not None))
    time.sleep(0.5)
    results.append(("POST Save Thresholds", test_save_thresholds()))
    time.sleep(0.5)
    results.append(("POST Save Features", test_save_features()))
    time.sleep(0.5)
    results.append(("GET Audit Logs", test_get_audit_logs()))
    time.sleep(0.5)
    results.append(("GET Admin Dashboard", test_admin_dashboard()))
    time.sleep(0.5)
    results.append(("Verify Persistence", test_verify_threshold_persistence()))
    
    # Summary
    print("\n" + "█"*60)
    print("█ TEST SUMMARY")
    print("█"*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'█'*60}")
    print(f"█ TOTAL: {passed}/{total} tests passed")
    print(f"█{'█'*58}")
    
    if passed == total:
        print("█ 🎉 ALL TESTS PASSED! UI should be working correctly!")
    else:
        print(f"█ ⚠️  {total - passed} test(s) failed. Check errors above.")
    
    print("█"*60 + "\n")

if __name__ == "__main__":
    run_all_tests()
