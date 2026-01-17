from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
from datetime import datetime
import redis
import time
import sqlite3
import json
from typing import Optional, Dict, Any

# ---------------- CONFIG ----------------
# Ensure Redis is running: redis-server
r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
DB_NAME = "fraud_logs.db"
CONFIG_KEY = "fraud_config"

# Default Configuration (Parameterized)
DEFAULT_CONFIG = {
    "velocity_threshold": 3,
    "velocity_window": 600,
    "high_risk_threshold": 0.9,
    "flag_risk_threshold": 0.8,
    "amount_spike_multiplier": 3,
    "anomaly_score_threshold": 0.03,
    "baseline_amount": 1500,
    "midnight_hours": [0, 1, 2, 3, 4],
    "enabled_checks": {
        "velocity": True,
        "geo_location": True,
        "amount_spike": True,
        "midnight": True,
        "ml_risk_score": True,
        "anomaly_detection": True
    }
}

# Load Models ----------------
try:
    xgb_fraud = joblib.load("xgb_fraud.pkl")
    iso_model = joblib.load("iso_model.pkl")
    scaler = joblib.load("scaler.pkl")
except Exception as e:
    print(f"❌ MODEL LOADING ERROR: {e}")
    xgb_fraud = None 
    iso_model = None
    scaler = None
# FastAPI Init ----------------
app = FastAPI(title="Fraud Detection API", version="2.0")

# Enable CORS for third-party integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize configuration on startup
def load_config():
    config_str = r.get(CONFIG_KEY)
    if config_str:
        return json.loads(config_str)
    else:
        r.set(CONFIG_KEY, json.dumps(DEFAULT_CONFIG))
        return DEFAULT_CONFIG

CURRENT_CONFIG = load_config()


# ---------------- DATABASE INIT ----------------
def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        
        # --- WAL MODE ADDED HERE ---
        conn.execute("PRAGMA journal_mode=WAL;")
        
        c = conn.cursor()
        
        # Transactions table (Enhanced with more fields)
        c.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT, transaction_id TEXT, amount REAL, country TEXT,
                merchant_name TEXT, merchant_category TEXT,
                device_type TEXT, ip_address TEXT, card_type TEXT,
                transaction_type TEXT, is_recurring INTEGER, is_international INTEGER,
                device_fingerprint TEXT, customer_age INTEGER, account_age_days INTEGER,
                previous_txn_24h INTEGER, avg_txn_amount REAL,
                timestamp TEXT, action TEXT, risk_score REAL, 
                anomaly_score REAL, reasons TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Admin audit log table
        c.execute('''
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_action TEXT, details TEXT, 
                changed_config TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Anomaly patterns table
        c.execute('''
            CREATE TABLE IF NOT EXISTS anomaly_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT UNIQUE, pattern_type TEXT,
                description TEXT, enabled INTEGER DEFAULT 1,
                threshold_value REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully (WAL Mode Enabled).")
    except Exception as e:
        print(f"❌ DB INIT ERROR: {e}")

init_db()

def log_admin_action(action: str, details: str, config_change: Optional[Dict] = None):
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        c = conn.cursor()
        config_json = json.dumps(config_change) if config_change else None
        c.execute('''
            INSERT INTO admin_logs (admin_action, details, changed_config)
            VALUES (?, ?, ?)
        ''', (action, details, config_json))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ ADMIN LOG ERROR: {e}")

def log_transaction(data, result):
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        c = conn.cursor()
        
        query = '''
            INSERT INTO transactions 
            (user_id, transaction_id, amount, country, merchant_name, merchant_category, 
             device_type, ip_address, card_type, transaction_type, is_recurring, is_international,
             device_fingerprint, customer_age, account_age_days, previous_txn_24h, avg_txn_amount,
             timestamp, action, risk_score, anomaly_score, reasons)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        values = (
            data.get('user_id'), 
            data.get('transaction_id'), 
            data.get('amount'), 
            data.get('country', data.get('location_country')), 
            data.get('merchant_name'),
            data.get('merchant_category'),
            data.get('device_type'),
            data.get('ip_address'),
            data.get('card_type'),
            data.get('transaction_type'),
            data.get('is_recurring', False),
            data.get('is_international', False),
            data.get('device_fingerprint'),
            data.get('customer_age'),
            data.get('account_age_days'),
            data.get('previous_txn_24h'),
            data.get('avg_txn_amount'),
            data.get('timestamp', data.get('transaction_time')), 
            result['action'], 
            result['risk_score'], 
            result.get('anomaly_score', 0),
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

# Request Schemas ----------------
class TransactionRequest(BaseModel):
    # Required fields
    user_id: str
    transaction_id: str
    amount: float
    country: str
    
    # Optional enrichment fields
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    device_type: Optional[str] = None  # mobile, web, atm, pos
    ip_address: Optional[str] = None
    card_type: Optional[str] = None  # credit, debit
    transaction_type: Optional[str] = None  # purchase, withdrawal, transfer
    is_recurring: Optional[bool] = False
    is_international: Optional[bool] = False
    device_fingerprint: Optional[str] = None
    customer_age: Optional[int] = None
    account_age_days: Optional[int] = None
    previous_txn_24h: Optional[int] = None
    avg_txn_amount: Optional[float] = None
    timestamp: Optional[datetime] = None

class ConfigUpdate(BaseModel):
    velocity_threshold: Optional[int] = None
    velocity_window: Optional[int] = None
    high_risk_threshold: Optional[float] = None
    flag_risk_threshold: Optional[float] = None
    amount_spike_multiplier: Optional[float] = None
    anomaly_score_threshold: Optional[float] = None
    baseline_amount: Optional[float] = None
    enabled_checks: Optional[Dict[str, bool]] = None

class AnomalyPattern(BaseModel):
    pattern_name: str
    pattern_type: str
    description: str
    threshold_value: float

class AdminStats(BaseModel):
    total_transactions: int
    allowed: int
    flagged: int
    blocked: int

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
def build_features(txn, txn_count, amt_sum, last_country, txn_time=None):
    if txn_time is None:
        txn_time = datetime.now()

    user_avg_amount = 1500  # baseline
    amount_vs_avg = txn.amount / max(user_avg_amount, 1)

    X = pd.DataFrame([{
        "amount": txn.amount,
        "amount_vs_avg": min(amount_vs_avg, 20),
        "time_diff_sec": 0,
        "txn_count_10min": txn_count,
        "amt_sum_10min": amt_sum,
        "is_midnight_txn": int(txn_time.hour <= 4) if isinstance(txn_time, datetime) else 0,
        "is_new_country": int(txn.country != last_country)
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

# 2.5. SERVE ADMIN CONFIG UI (The Configuration Panel)
@app.get("/admin-config", response_class=HTMLResponse)
def admin_config_ui():
    with open("admin-config.html", "r", encoding="utf-8") as f:
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
# 4. PREDICTION API (The Brain) - Internal use
@app.post("/predict")
def predict(txn: TransactionRequest):
    global CURRENT_CONFIG
    
    txn_count, amt_sum = update_velocity(txn.user_id, txn.amount)
    last_country = get_and_update_country(txn.user_id, txn.country)

    # Handle timestamp - use provided or generate current
    txn_time = txn.timestamp if txn.timestamp else datetime.now()
    X = build_features(txn, txn_count, amt_sum, last_country, txn_time)

    risk_score = float(xgb_fraud.predict_proba(X)[0][1]) if xgb_fraud else 0
    anomaly_score = float(-iso_model.decision_function(scaler.transform(X))[0]) if iso_model and scaler else 0

    reasons = []
    action = "ALLOW"

    cfg = CURRENT_CONFIG

    # Velocity Check
    if cfg["enabled_checks"]["velocity"] and txn_count >= cfg["velocity_threshold"]:
        action = "BLOCK"
        reasons.append(f"High transaction velocity (≥{cfg['velocity_threshold']} in {cfg['velocity_window']}s)")

    # High Risk + Amount Spike
    elif cfg["enabled_checks"]["ml_risk_score"] and cfg["enabled_checks"]["amount_spike"] and \
         risk_score > cfg["high_risk_threshold"] and X["amount_vs_avg"].iloc[0] >= cfg["amount_spike_multiplier"]:
        action = "BLOCK"
        reasons.append("High fraud risk with sudden amount spike")

    # Flagging Rules
    else:
        if cfg["enabled_checks"]["geo_location"] and X["is_new_country"].iloc[0] == 1:
            reasons.append("Transaction from a new country")

        if cfg["enabled_checks"]["amount_spike"] and X["amount_vs_avg"].iloc[0] >= cfg["amount_spike_multiplier"]:
            reasons.append(f"Sudden large amount (${txn.amount}) compared to baseline")

        if cfg["enabled_checks"]["midnight"] and X["is_midnight_txn"].iloc[0] == 1:
            reasons.append("Transaction during unusual hours (midnight)")

        if cfg["enabled_checks"]["anomaly_detection"] and anomaly_score > cfg["anomaly_score_threshold"]:
            reasons.append("Unusual behavior detected by anomaly model")

        if cfg["enabled_checks"]["ml_risk_score"] and risk_score > cfg["flag_risk_threshold"]:
            reasons.append("Matches known fraud patterns")

        if reasons:
            action = "FLAG"
        else:
            action = "ALLOW"
            reasons.append("Normal transaction behavior")

    result = {
        "user_id": txn.user_id, "transaction_id": txn.transaction_id,
        "action": action, "reason": ", ".join(reasons),
        "risk_score": round(risk_score, 2), "anomaly_score": round(anomaly_score, 2),
        "velocity_count": txn_count, "velocity_sum": round(amt_sum, 2)
    }
    
    log_transaction(txn.dict(), result)
    return result


# ================ PUBLIC API (Third-Party Integration) ================

# 5. Third-Party Prediction API - Enhanced Response
@app.post("/api/v1/predict")
async def predict_v1(txn: TransactionRequest):
    """
    Public API for third-party fraud detection integration.
    Returns detailed fraud analysis with all risk indicators.
    """
    result = predict(txn)
    return {
        "status": "success",
        "data": result,
        "timestamp": datetime.now().isoformat()
    }

# 6. Third-Party Batch Prediction API
@app.post("/api/v1/predict/batch")
async def predict_batch(transactions: list[TransactionRequest]):
    """
    Batch prediction API for multiple transactions.
    """
    results = []
    for txn in transactions:
        result = predict(txn)
        results.append(result)
    return {
        "status": "success",
        "count": len(results),
        "data": results,
        "timestamp": datetime.now().isoformat()
    }

# 7. Get Current Configuration
@app.get("/api/v1/config")
async def get_config():
    """Get current fraud detection configuration."""
    return {
        "status": "success",
        "config": CURRENT_CONFIG,
        "timestamp": datetime.now().isoformat()
    }

# 8. Get Transaction History with Filters
@app.get("/api/v1/transactions")
async def get_transactions_api(
    limit: int = Query(50, le=500),
    action: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    Get transaction history with optional filters.
    Query Parameters:
    - limit: Number of records (max 500)
    - action: Filter by action (ALLOW, FLAG, BLOCK)
    - user_id: Filter by user
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        return {
            "status": "success",
            "count": len(rows),
            "data": [dict(row) for row in rows],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 9. Get Statistics
@app.get("/api/v1/stats")
async def get_stats(days: int = Query(1, ge=1, le=30)):
    """Get fraud detection statistics."""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Get stats
        c.execute(f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN action='ALLOW' THEN 1 ELSE 0 END) as allowed,
                SUM(CASE WHEN action='FLAG' THEN 1 ELSE 0 END) as flagged,
                SUM(CASE WHEN action='BLOCK' THEN 1 ELSE 0 END) as blocked,
                AVG(risk_score) as avg_risk_score,
                MAX(risk_score) as max_risk_score
            FROM transactions 
            WHERE datetime(created_at) >= datetime('now', '-{days} days')
        """)
        
        stats = c.fetchone()
        conn.close()
        
        return {
            "status": "success",
            "period_days": days,
            "stats": {
                "total_transactions": stats[0] or 0,
                "allowed": stats[1] or 0,
                "flagged": stats[2] or 0,
                "blocked": stats[3] or 0,
                "average_risk_score": round(stats[4] or 0, 2),
                "max_risk_score": round(stats[5] or 0, 2)
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ================ ADMIN API ================

# 10. Update Configuration (Admin Only)
@app.post("/api/admin/config")
async def update_config(config_update: ConfigUpdate, authorization: str = Header(None)):
    """Update fraud detection configuration."""
    global CURRENT_CONFIG
    
    # Extract token from Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    admin_token = authorization.replace("Bearer ", "")
    
    # Simple token validation (implement proper auth in production)
    if admin_token != "your-secure-admin-token":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    old_config = CURRENT_CONFIG.copy()
    
    # Update only provided fields
    for field, value in config_update.dict(exclude_unset=True).items():
        if field == "enabled_checks" and value:
            CURRENT_CONFIG["enabled_checks"].update(value)
        elif value is not None:
            CURRENT_CONFIG[field] = value
    
    # Persist to Redis
    r.set(CONFIG_KEY, json.dumps(CURRENT_CONFIG))
    
    # Log admin action
    log_admin_action("CONFIG_UPDATE", "Updated fraud detection configuration", old_config)
    
    return {
        "status": "success",
        "message": "Configuration updated",
        "old_config": old_config,
        "new_config": CURRENT_CONFIG,
        "timestamp": datetime.now().isoformat()
    }

# 11. Get Admin Logs
@app.get("/api/admin/logs")
async def get_admin_logs(limit: int = Query(50, le=500), authorization: str = Header(None)):
    """Get admin action logs."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    admin_token = authorization.replace("Bearer ", "")
    
    if admin_token != "your-secure-admin-token":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM admin_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        
        return {
            "status": "success",
            "count": len(rows),
            "data": [dict(row) for row in rows],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 12. Add Custom Anomaly Pattern (Admin)
@app.post("/api/admin/anomaly-pattern")
async def add_anomaly_pattern(pattern: AnomalyPattern, authorization: str = Header(None)):
    """Add custom anomaly detection pattern."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    admin_token = authorization.replace("Bearer ", "")
    
    if admin_token != "your-secure-admin-token":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT INTO anomaly_patterns (pattern_name, pattern_type, description, threshold_value)
            VALUES (?, ?, ?, ?)
        ''', (pattern.pattern_name, pattern.pattern_type, pattern.description, pattern.threshold_value))
        conn.commit()
        conn.close()
        
        log_admin_action("ADD_PATTERN", f"Added anomaly pattern: {pattern.pattern_name}")
        
        return {
            "status": "success",
            "message": f"Pattern '{pattern.pattern_name}' added successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 13. Get All Anomaly Patterns (Admin)
@app.get("/api/admin/anomaly-patterns")
async def get_anomaly_patterns(authorization: str = Header(None)):
    """Get all custom anomaly patterns."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    admin_token = authorization.replace("Bearer ", "")
    
    if admin_token != "your-secure-admin-token":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM anomaly_patterns WHERE enabled = 1")
        rows = c.fetchall()
        conn.close()
        
        return {
            "status": "success",
            "count": len(rows),
            "data": [dict(row) for row in rows],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 14. Admin Dashboard Stats
@app.get("/api/admin/dashboard")
async def admin_dashboard(authorization: str = Header(None)):
    """Get comprehensive admin dashboard data."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    admin_token = authorization.replace("Bearer ", "")
    
    if admin_token != "your-secure-admin-token":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Summary stats
        c.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN action='ALLOW' THEN 1 ELSE 0 END) as allowed,
                SUM(CASE WHEN action='FLAG' THEN 1 ELSE 0 END) as flagged,
                SUM(CASE WHEN action='BLOCK' THEN 1 ELSE 0 END) as blocked
            FROM transactions
        """)
        stats = c.fetchone()
        
        # Recent transactions
        c.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 20")
        recent = c.fetchall()
        
        # High-risk transactions
        c.execute("SELECT * FROM transactions WHERE risk_score > 0.7 ORDER BY risk_score DESC LIMIT 10")
        high_risk = c.fetchall()
        
        conn.close()
        
        return {
            "status": "success",
            "summary": {
                "total": stats[0],
                "allowed": stats[1],
                "flagged": stats[2],
                "blocked": stats[3],
                "fraud_rate": round((stats[2] + stats[3]) / max(stats[0], 1) * 100, 2)
            },
            "recent_transactions": [dict(zip([description[0] for description in c.description], row)) for row in recent] if recent else [],
            "high_risk_transactions": [dict(zip([description[0] for description in c.description], row)) for row in high_risk] if high_risk else [],
            "current_config": CURRENT_CONFIG,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 15. Health Check Endpoint
@app.get("/health")
async def health_check():
    """Check API health status."""
    return {
        "status": "healthy",
        "service": "Fraud Detection API",
        "version": "2.0",
        "redis_connected": r.ping(),
        "timestamp": datetime.now().isoformat()
    }
