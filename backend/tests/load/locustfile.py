"""Locust load test — Medical Reports API

Usage:
    pip install locust
    locust -f tests/load/locustfile.py --host=https://medical-reports-api.railway.app

Dev mode:
    locust -f tests/load/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between


class MedicalReportsUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.access_token = None
        self.login()

    def login(self):
        with self.client.post(
            "/auth/login",
            json={"email": "loadtest@clinic.com", "password": "loadtest123"},
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data["access_token"]
            elif resp.status_code == 401:
                self.register()

    def register(self):
        with self.client.post(
            "/auth/register",
            json={
                "email": "loadtest@clinic.com",
                "password": "loadtest123",
                "role": "doctor",
                "full_name": "Load Test Doctor",
                "crm": "99999-SP",
            },
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                data = resp.json()
                self.login()

    @task(5)
    def health_check(self):
        self.client.get("/health", name="GET /health")

    @task(3)
    def health_db(self):
        self.client.get("/health/db", name="GET /health/db")

    @task(3)
    def health_cache(self):
        self.client.get("/health/cache", name="GET /health/cache")

    @task(2)
    def health_agents(self):
        self.client.get("/health/agents", name="GET /health/agents")

    @task(2)
    def list_patients(self):
        if not self.access_token:
            return
        self.client.get(
            "/patients",
            headers={"Authorization": f"Bearer {self.access_token}"},
            name="GET /patients",
        )

    @task(1)
    def audit_logs(self):
        if not self.access_token:
            return
        self.client.get(
            "/audit/logs?limit=10",
            headers={"Authorization": f"Bearer {self.access_token}"},
            name="GET /audit/logs",
        )

    @task(1)
    def privacy_policy(self):
        self.client.get("/privacy", name="GET /privacy")
