"""
Load test for POST /generate against the real running app (loadtest/run_server.py),
with only the paid Segmind call mocked. Real Supabase session/job/frame/task
read-writes happen for real on every simulated request.

Run: locust -f loadtest/locustfile.py --host http://127.0.0.1:8125 --headless -u 50 -r 10 -t 30s
"""
import json
from pathlib import Path

from locust import HttpUser, task, between

SEED = json.loads((Path(__file__).parent / "seed_data.json").read_text())


class GenerateUser(HttpUser):
    wait_time = between(0.1, 0.3)

    @task
    def generate(self):
        self.client.post(
            "/generate",
            json={"job_id": SEED["job_id"], "frame_id": SEED["frame_id"]},
            headers={"X-Session-Token": SEED["session_token"]},
        )
