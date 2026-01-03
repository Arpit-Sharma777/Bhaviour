# 🚨 Real-Time Fraud Detection System (Hybrid ML)

This project is a **real-time fraud detection system** built using a **hybrid architecture** combining **rule-based logic**, **supervised machine learning**, and **unsupervised anomaly detection**.  
It is designed to simulate **bank/fintech-grade transaction monitoring**, not a toy or interview-only project.

---

## 🧠 What This System Does

For every incoming transaction, the system **instantly decides**:

- ✅ **ALLOW** – normal transaction  
- ⚠️ **FLAG** – suspicious, requires human verification  
- ❌ **BLOCK** – confirmed fraud risk  

### Fraud patterns detected:
- Transaction velocity fraud (multiple txns in short time)
- Geo-location change fraud
- Sudden amount spike fraud
- Midnight/unusual-time transactions
- Known fraud patterns (supervised ML)
- Unknown/new fraud patterns (unsupervised ML)

---

## 🏗️ System Architecture

# 🚨 Real-Time Fraud Detection System (Hybrid ML)

This project is a **real-time fraud detection system** built using a **hybrid architecture** combining **rule-based logic**, **supervised machine learning**, and **unsupervised anomaly detection**.  
It is designed to simulate **bank/fintech-grade transaction monitoring**, not a toy or interview-only project.

---

## 🧠 What This System Does

For every incoming transaction, the system **instantly decides**:

- ✅ **ALLOW** – normal transaction  
- ⚠️ **FLAG** – suspicious, requires human verification  
- ❌ **BLOCK** – confirmed fraud risk  

### Fraud patterns detected:
- Transaction velocity fraud (multiple txns in short time)
- Geo-location change fraud
- Sudden amount spike fraud
- Midnight/unusual-time transactions
- Known fraud patterns (supervised ML)
- Unknown/new fraud patterns (unsupervised ML)

---

## 🏗️ System Architecture

Client / Banking App
|
v
FastAPI (/predict)
|
v
Redis (10-minute sliding window per user)
|
v
Feature Engineering
|
v
Hybrid Decision Engine
├─ Rule Engine (velocity, geo, amount, time)
├─ XGBoost (fraud probability)
└─ Isolation Forest (anomaly score)
|
v
Final Decision → ALLOW / FLAG / BLOCK


---

## ⚙️ Tech Stack

- Python 3.11
- FastAPI
- Uvicorn (multi-worker)
- Redis (real-time state & velocity tracking)
- XGBoost (supervised fraud model)
- Isolation Forest (unsupervised anomaly detection)
- Scikit-learn
- Pandas
- Joblib
- Locust (load testing)

---

## 📂 Project Structure


---

## ⚙️ Tech Stack

- Python 3.11
- FastAPI
- Uvicorn (multi-worker)
- Redis (real-time state & velocity tracking)
- XGBoost (supervised fraud model)
- Isolation Forest (unsupervised anomaly detection)
- Scikit-learn
- Pandas
- Joblib
- Locust (load testing)

---

## 📂 Project Structure

Bhaviour/
│
├── fraud_api.py # FastAPI application
├── xgb_fraud.pkl # Supervised ML model
├── iso_model.pkl # Unsupervised anomaly model
├── scaler.pkl # Feature scaler
├── requirements.txt
├── README.md
├── .gitignore


---

## 🚀 How to Run the System

### 1️⃣ Start Redis
```bash
redis-server

2️⃣ Activate Virtual Environment
.venv\Scripts\activate   # Windows

3️⃣ Start FastAPI (multi-worker)
uvicorn fraud_api:app --workers 4 --host 127.0.0.1 --port 8000

API documentation:
http://127.0.0.1:8000/docs

📡 API Endpoint
POST /predict
Request Example

{
  "user_id": "USR_10001",
  "transaction_id": "TXN_001",
  "amount": 7000,
  "location_country": "Germany",
  "transaction_time": "2025-01-18T12:30:00"
}

Response Example:
{
  "user_id": "USR_10001",
  "transaction_id": "TXN_001",
  "action": "BLOCK",
  "reason": "High transaction velocity",
  "risk_score": 0.92,
  "anomaly_score": 0.04
}

🧪 Load Testing (Locust)

Run Locust:
http://localhost:8089

