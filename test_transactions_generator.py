#!/usr/bin/env python
"""
Generate test transactions for fraud detection system
"""
import requests
from datetime import datetime
import time
import sys

API = 'http://localhost:8000'

transactions = [
    {'amount': 500, 'country': 'USA', 'desc': 'Small purchase'},
    {'amount': 1000, 'country': 'India', 'desc': 'Transfer'},
    {'amount': 750, 'country': 'Germany', 'desc': 'Payment'},
    {'amount': 2000, 'country': 'USA', 'desc': 'Large purchase'},
    {'amount': 1500, 'country': 'USA', 'desc': 'Regular payment'},
]

print("=" * 50)
print("Generating Test Transactions")
print("=" * 50)
print()

for i, txn in enumerate(transactions, 1):
    body = {
        'user_id': 'USR_10001',
        'transaction_id': f'TXN_BATCH_{i}_{int(time.time())}',
        'amount': txn['amount'],
        'location_country': txn['country'],
        'transaction_time': datetime.now().isoformat()
    }
    
    try:
        print(f"[{i}/5] Sending transaction: ${txn['amount']} to {txn['country']}...", end=" ")
        response = requests.post(
            f'{API}/predict',
            json=body,
            timeout=5
        )
        result = response.json()
        action = result.get('data', {}).get('action', 'ERROR')
        risk_score = result.get('data', {}).get('risk_score', 0)
        print(f"✓ {action} (Risk: {risk_score:.2f})")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        print()
        print("ERROR: Could not connect to API server!")
        print("Make sure start-server.bat is running on port 8000")
        print()
        sys.exit(1)
    
    time.sleep(0.5)

print()
print("=" * 50)
print("✅ Test transactions complete!")
print("=" * 50)
print()
print("View profile at:")
print("  http://localhost:8000/customer-profile")
print()
print("Enter: USR_10001")
print()
