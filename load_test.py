from locust import HttpUser, task, between
import random
from datetime import datetime
import json

class FraudLoadTest(HttpUser):
    wait_time = between(0.1, 1)   # delay between requests (simulate real users)

    @task
    def send_transaction(self):
        # random test user (simulate many users)
        user = random.choice(["USR_10001", "USR_10002", "USR_10003", "USR_10004"])
        
        payload = {
            "user_id": user,
            "transaction_id": f"TXN_{random.randint(10000,99999)}",
            "amount": random.randint(100, 50000),  # random transaction amount
            "location_country": random.choice(["India", "Germany", "USA", "UK"]),
            "transaction_time": datetime.now().isoformat()
        }

        self.client.post("/predict", json=payload)
