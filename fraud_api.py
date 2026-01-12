from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import joblib
import pandas as pd
from datetime import datetime
import redis
import time
import sqlite3

# ---------------- CONFIG ----------------
# Ensure Redis is running: redis-server
r = redis.Redis(host="localhost", port=6379, decode_responses=True)
DB_NAME = "fraud_logs.db"

# ---------------- Load Models ----------------
try:
    xgb_fraud = joblib.load("xgb_fraud.pkl")
    iso_model = joblib.load("iso_model.pkl")
    scaler = joblib.load("scaler.pkl")
except Exception as e:
    print(f"❌ MODEL LOADING ERROR: {e}")
    xgb_fraud = None 
    iso_model = None
    scaler = None
# ---------------- FastAPI Init ----------------
app = FastAPI(title="Fraud Detection API")


# ---------------- DATABASE INIT ----------------
def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        
        # --- WAL MODE ADDED HERE ---
        conn.execute("PRAGMA journal_mode=WAL;")
        
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT, transaction_id TEXT, amount REAL, country TEXT,
                timestamp TEXT, action TEXT, risk_score REAL, reasons TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully (WAL Mode Enabled).")
    except Exception as e:
        print(f"❌ DB INIT ERROR: {e}")

init_db()

def log_transaction(data, result):
    # This try block was likely broken in your file
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        c = conn.cursor()
        
        # Prepare the SQL query
        query = '''
            INSERT INTO transactions 
            (user_id, transaction_id, amount, country, timestamp, action, risk_score, reasons)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        # Prepare the values
        values = (
            data['user_id'], 
            data['transaction_id'], 
            data['amount'], 
            data['location_country'], 
            data['transaction_time'], 
            result['action'], 
            result['risk_score'], 
            result['reason']
        )

        c.execute(query, values)
        conn.commit()
        conn.close()
        print(f"📝 DB WRITE SUCCESS: {data['transaction_id']} - {result['action']}")
        
    except Exception as e:
        print(f"❌ DB ERROR: {e}")

# Initialize DB on startup
init_db()

# ---------------- Request Schema ----------------
class TransactionRequest(BaseModel):
    user_id: str
    transaction_id: str
    amount: float
    location_country: str
    transaction_time: datetime

# ---------------- LOGIC ----------------
WINDOW_SECONDS = 600  # 10 minutes

def update_velocity(user_id: str, amount: float):
    now = int(time.time())

    txn_key = f"txn:{user_id}"
    amt_key = f"amt:{user_id}"

    r.zadd(txn_key, {now: now})
    r.zadd(amt_key, {amount: now})

    cutoff = now - WINDOW_SECONDS
    r.zremrangebyscore(txn_key, 0, cutoff)
    r.zremrangebyscore(amt_key, 0, cutoff)

    r.expire(txn_key, WINDOW_SECONDS)
    r.expire(amt_key, WINDOW_SECONDS)

    txn_count = r.zcard(txn_key)
    amt_sum = sum(map(float, r.zrange(amt_key, 0, -1)))

    return txn_count, amt_sum

def get_and_update_country(user_id: str, country: str):
    key = f"last_country:{user_id}"
    last_country = r.get(key) or country
    r.setex(key, WINDOW_SECONDS, country)
    return last_country

# ---------------- Feature Builder ----------------
def build_features(txn, txn_count, amt_sum, last_country):

    user_avg_amount = 1500  # baseline
    amount_vs_avg = txn.amount / max(user_avg_amount, 1)

    X = pd.DataFrame([{
        "amount": txn.amount,
        "amount_vs_avg": min(amount_vs_avg, 20),
        "time_diff_sec": 0,
        "txn_count_10min": txn_count,
        "amt_sum_10min": amt_sum,
        "is_midnight_txn": int(txn.transaction_time.hour <= 4),
        "is_new_country": int(txn.location_country != last_country)
    }])

    return X


# ---------------- API ENDPOINTS ----------------

# 1. SERVE USER UI (The Payment Page)
@app.get("/", response_class=HTMLResponse)
def user_ui():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# 2. SERVE ADMIN UI (The Dashboard)
@app.get("/admin", response_class=HTMLResponse)
def admin_ui():
    with open("admin.html", "r", encoding="utf-8") as f:
        return f.read()

# 3. HISTORY API (For Admin UI data)
@app.get("/api/history")
def get_history():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 50")
        rows = c.fetchall()
        conn.close()
        # Removed verbose print here to keep it cleaner as requested
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ FETCH ERROR: {e}")
        return []
# ---------------- Prediction Endpoint ----------------
# 4. PREDICTION API (The Brain)
@app.post("/predict")
def predict(txn: TransactionRequest):

    txn_count, amt_sum = update_velocity(txn.user_id, txn.amount)
    last_country = get_and_update_country(txn.user_id, txn.location_country)

    X = build_features(txn, txn_count, amt_sum, last_country)

    risk_score = float(xgb_fraud.predict_proba(X)[0][1])
    anomaly_score = float(
        -iso_model.decision_function(scaler.transform(X))[0]
    )

    reasons = []

    # ---------------- BLOCK RULES ----------------
    if txn_count >= 3:
        action = "BLOCK"
        reasons.append("High transaction velocity (≥3 in 10 minutes)")

    elif risk_score > 0.9 and X["amount_vs_avg"].iloc[0] >= 3:
        action = "BLOCK"
        reasons.append("High fraud risk with sudden amount spike")

    # ---------------- FLAG RULES ----------------
    else:
        if X["is_new_country"].iloc[0] == 1:
            reasons.append("Transaction from a new country")

        if X["amount_vs_avg"].iloc[0] >= 3:
            reasons.append("Sudden large amount compared to user history")

        if X["is_midnight_txn"].iloc[0] == 1:
            reasons.append("Transaction during unusual hours (midnight)")

        if anomaly_score > 0.03:
            reasons.append("Unusual behavior detected by anomaly model")

        if risk_score > 0.8:
            reasons.append("Matches known fraud patterns")

        if reasons:
            action = "FLAG"
        else:
            action = "ALLOW"
            reasons.append("Normal transaction behavior")

    result = {
        "user_id": txn.user_id, "transaction_id": txn.transaction_id,
        "action": action, "reason": ", ".join(reasons),
        "risk_score": round(risk_score, 2), "anomaly_score": round(anomaly_score, 2)
    }
    
    log_transaction(txn.dict(), result)
    return result