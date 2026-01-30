#!/usr/bin/env python
"""
Check schema and fix transactions table
"""
import sqlite3

DB_NAME = "fraud_logs.db"

try:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check schema
    c.execute("PRAGMA table_info(transactions)")
    cols = c.fetchall()
    print("Current schema:")
    for col in cols:
        print(f"  {col[1]}: {col[2]}")
    
    # Add missing columns if needed
    try:
        c.execute("ALTER TABLE transactions ADD COLUMN anomaly_score REAL")
        print("✅ Added anomaly_score column")
    except:
        print("  anomaly_score column already exists")
    
    try:
        c.execute("ALTER TABLE transactions ADD COLUMN risk_score REAL")
        print("✅ Added risk_score column")
    except:
        print("  risk_score column already exists")
    
    try:
        c.execute("ALTER TABLE transactions ADD COLUMN action TEXT")
        print("✅ Added action column")
    except:
        print("  action column already exists")
    
    try:
        c.execute("ALTER TABLE transactions ADD COLUMN reasons TEXT")
        print("✅ Added reasons column")
    except:
        print("  reasons column already exists")
    
    conn.commit()
    
    # Update NULL values
    c.execute('UPDATE transactions SET anomaly_score = 0.0 WHERE anomaly_score IS NULL')
    c.execute('UPDATE transactions SET risk_score = 0.0 WHERE risk_score IS NULL')
    c.execute("UPDATE transactions SET action = 'ALLOW' WHERE action IS NULL OR action = ''")
    c.execute("UPDATE transactions SET reasons = '' WHERE reasons IS NULL")
    
    conn.commit()
    
    # Check results
    c.execute('SELECT COUNT(*) FROM transactions')
    total = c.fetchone()[0]
    
    c.execute('SELECT user_id, COUNT(*) FROM transactions GROUP BY user_id')
    by_user = c.fetchall()
    
    print(f"\n✅ Fixed transactions!")
    print(f"   Total transactions: {total}")
    for user, count in by_user:
        print(f"   {user}: {count} transactions")
    
    conn.close()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
