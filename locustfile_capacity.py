"""
Capacity test: find how many concurrent users / requests per second the
redirect endpoint can sustain before latency or errors get bad.

- Registers ONE user and creates a pool of short codes up front, so bcrypt
  (slow login/register) doesn't dominate the test.
- Users hit /{short_code} with no wait time, so RPS is limited by the
  server, not by think time.
- No auto-ramp shape here -- open http://localhost:8089, enter your own
  user count / spawn rate, and press Start manually.

Run:
    locust -f locustfile_capacity.py --host http://localhost:8000 --processes 8

Then open http://localhost:8089 in your browser and click Start.
"""
import random
import uuid

import requests
from locust import FastHttpUser, constant, events, task

CODES = []
POOL_SIZE = 2000


@events.test_start.add_listener
def create_code_pool(environment, **kwargs):
    base = environment.host
    user_name = f"capacity_{uuid.uuid4().hex[:8]}"
    password = "Capacity_pw_123"
    requests.post(f"{base}/api/auth/register", json={"user_name": user_name, "password": password})
    token = requests.post(
        f"{base}/api/auth/login", json={"user_name": user_name, "password": password}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    for i in range(POOL_SIZE):
        r = requests.post(
            f"{base}/api/urls",
            json={"original_url": f"https://example.com/capacity/{i}"},
            headers=headers,
        )
        CODES.append(r.json()["short_code"])
    print(f"Created {len(CODES)} short codes for the capacity test")


class RedirectUser(FastHttpUser):
    wait_time = constant(0)

    @task
    def redirect(self):
        if not CODES:
            return
        code = random.choice(CODES)
        with self.client.get(
            f"/{code}",
            name="/{short_code} [redirect]",
            allow_redirects=False,
            catch_response=True,
        ) as response:
            if response.status_code == 302:
                response.success()
            else:
                response.failure(f"status {response.status_code}")