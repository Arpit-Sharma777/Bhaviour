from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
from datetime import datetime
import redis
import time

# ---------------- Redis Connection ----------------
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# ---------------- Load Models ----------------
xgb_fraud = joblib.load("xgb_fraud.pkl")
iso_model = joblib.load("iso_model.pkl")
scaler = joblib.load("scaler.pkl")

app = FastAPI(title="Fraud Detection API")

# ---------------- Request Schema ----------------
class TransactionRequest(BaseModel):
    user_id: str
    transaction_id: str
    amount: float
    location_country: str
    transaction_time: datetime

# ---------------- Redis Helpers ----------------
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

# ---------------- Prediction Endpoint ----------------
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

    return {
        "user_id": txn.user_id,
        "transaction_id": txn.transaction_id,
        "action": action,
        "reason": ", ".join(reasons),
        "risk_score": risk_score,
        "anomaly_score": anomaly_score
    }
