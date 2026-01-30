#!/usr/bin/env python
"""
Health check for fraud detection system
"""
import requests
import sqlite3
import sys

print("Checking system health...")
print()

# 1. Check Server
try:
    response = requests.get('http://localhost:8000/health', timeout=2)
    if response.status_code == 200:
        data = response.json()
        print('✅ Server: Running')
        print(f'   Version: {data.get("version")}')
        print(f'   Redis: {"✅" if data.get("redis_connected") else "❌"}')
    else:
        print('❌ Server: Not responding correctly')
except Exception as e:
    print(f'❌ Server: Not running (Error: {str(e)})')

print()

# 2. Check Database
try:
    conn = sqlite3.connect('fraud_logs.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM transactions')
    count = c.fetchone()[0]
    print(f'✅ Database: {count} transactions')
    
    c.execute('SELECT user_id, COUNT(*) FROM transactions GROUP BY user_id')
    print('   Users:')
    for user, txn_count in c.fetchall():
        print(f'     - {user}: {txn_count} transactions')
    conn.close()
except Exception as e:
    print(f'❌ Database: Error - {str(e)}')

print()

# 3. Check Redis
try:
    import redis
    r = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
    r.ping()
    print('✅ Redis: Connected')
except Exception as e:
    print(f'❌ Redis: Not connected - {str(e)}')

print()
print("=" * 50)
print('✅ Health check complete!')
print("=" * 50)
