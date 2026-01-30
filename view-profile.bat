@echo off
REM ============================================
REM View Customer Profile Data
REM ============================================

echo ========================================
echo  Customer Profile Data Viewer
echo ========================================
echo.

cd /d c:\PROJECTS\ANAMOLY\Bhaviour

call venv\Scripts\activate.bat

set /p USER_ID="Enter User ID (default: USR_10001): "
if "%USER_ID%"=="" set USER_ID=USR_10001

echo.
echo Getting profile for %USER_ID%...
echo.

python -c "
import requests
import json

API = 'http://localhost:8000'
USER_ID = '%USER_ID%'

try:
    response = requests.get(
        f'{API}/api/customer-profile/{USER_ID}',
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if data['status'] == 'success':
            profile = data['data']['profile']
            
            print('========================================')
            print('CUSTOMER PROFILE')
            print('========================================')
            print()
            print('OVERVIEW')
            print('  User ID:              ' + str(profile.get('user_id')))
            print('  Total Transactions:   ' + str(profile.get('total_transactions')))
            print('  Risk Level:           ' + str(profile.get('risk_level')))
            print('  Account Age (days):   ' + str(profile.get('account_age_days')))
            print()
            print('AMOUNTS')
            print('  Average:              ${:.2f}'.format(profile.get('avg_amount', 0)))
            print('  Median:               ${:.2f}'.format(profile.get('median_amount', 0)))
            print('  Max:                  ${:.2f}'.format(profile.get('max_amount', 0)))
            print('  Total Spent:          ${:.2f}'.format(profile.get('total_spent', 0)))
            print()
            print('RISK METRICS')
            print('  Avg Risk Score:       {:.3f}'.format(profile.get('avg_risk_score', 0)))
            print('  Allowed:              ' + str(profile.get('allowed_count')))
            print('  Flagged:              ' + str(profile.get('flagged_count')))
            print('  Blocked:              ' + str(profile.get('blocked_count')))
            print()
            print('GEOGRAPHIC')
            print('  Countries:            ' + str(profile.get('unique_countries')))
            print('  Most Common:          ' + str(profile.get('most_common_country')))
            print()
            print('TIMING')
            print('  Midnight Txns:        ' + str(profile.get('midnight_txn_count')))
            print('  Peak Hour:            ' + str(profile.get('peak_hour')) + ':00')
            print()
            
            patterns = data['data'].get('patterns', [])
            if patterns:
                print('DETECTED PATTERNS')
                for p in patterns:
                    print('  • ' + p['pattern'] + ': ' + p['description'])
            else:
                print('PATTERNS: None detected (good sign!)')
            
            print()
            print('========================================')
        else:
            print('ERROR: ' + data.get('message'))
    else:
        print('ERROR: API returned status ' + str(response.status_code))
except Exception as e:
    print('ERROR: ' + str(e))
    print()
    print('Make sure:')
    print('  1. Server is running (start-server.bat)')
    print('  2. Transactions exist for this user')
    print('  3. User ID is correct')

"

echo.
pause
