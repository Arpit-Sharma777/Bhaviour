#!/usr/bin/env python
import requests
import json

try:
    response = requests.get('http://localhost:8000/api/customer-profile/USR_10001')
    data = response.json()
    
    if data.get('status') == 'success':
        profile = data['data']['profile']
        print("✅ Customer Profile Retrieved Successfully!")
        print(f"\nUser: {profile['user_id']}")
        print(f"Total Transactions: {profile['total_transactions']}")
        print(f"Account Age: {profile['account_age_days']} days")
        print(f"Risk Level: {profile['risk_level']}")
        print(f"Avg Risk Score: {profile['avg_risk_score']:.2f}")
        print(f"Avg Amount: ${profile['avg_amount']:.2f}")
        print(f"Total Spent: ${profile['total_spent']:.2f}")
        print(f"\nActions:")
        print(f"  Allowed: {profile['allowed_count']}")
        print(f"  Flagged: {profile['flagged_count']}")
        print(f"  Blocked: {profile['blocked_count']}")
        print(f"\nLocation:")
        print(f"  Countries: {profile['unique_countries']}")
        print(f"  Most Common: {profile['most_common_country']}")
    else:
        print(f"❌ Error: {data.get('message')}")
        
except Exception as e:
    print(f"❌ Connection Error: {e}")
