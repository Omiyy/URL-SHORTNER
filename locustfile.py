import random
import string
import uuid

from locust import HttpUser, task, between


def random_suffix(n=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


class URLShortenerUser(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self):
        """Runs once per simulated user: register + log in, then store the
        access token so every subsequent request carries it automatically."""
        self.user_name = f"loadtest_{uuid.uuid4().hex[:10]}"
        self.password = "LoadTest_pw_123"
        self.my_codes = []  # short_codes this user has created

        # Register
        reg_resp = self.client.post(
            "/api/auth/register",
            json={"user_name": self.user_name, "password": self.password},
            name="/api/auth/register",
        )
        if reg_resp.status_code != 201:
            print(f"Register failed: {reg_resp.status_code} {reg_resp.text}")
            return

        # Login
        login_resp = self.client.post(
            "/api/auth/login",
            json={"user_name": self.user_name, "password": self.password},
            name="/api/auth/login",
        )
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            if token:
                self.client.headers.update({"Authorization": f"Bearer {token}"})
        else:
            print(f"Login failed: {login_resp.status_code} {login_resp.text}")

    @task(3)
    def create_short_url(self):
        long_url = f"https://example.com/page/{random.randint(1, 1_000_000)}"
        payload = {"original_url": long_url}  # let backend auto-generate short_code
        with self.client.post(
            "/api/urls", json=payload, name="/api/urls [create]", catch_response=True
        ) as response:
            if response.status_code == 201:
                code = response.json().get("short_code")
                if code:
                    self.my_codes.append(code)
                response.success()
            else:
                response.failure(f"create failed: {response.status_code} {response.text}")

    @task(10)
    def redirect(self):
        if not self.my_codes:
            return
        code = random.choice(self.my_codes)
        # Don't follow the redirect -- we just want to measure the redirect
        # endpoint itself, and we expect a 302, not a 200.
        with self.client.get(
            f"/{code}",
            name="/{short_code} [redirect]",
            allow_redirects=False,
            catch_response=True,
        ) as response:
            if response.status_code == 302:
                response.success()
            else:
                response.failure(f"redirect failed: {response.status_code}")

    @task(2)
    def list_urls(self):
        self.client.get("/api/urls", name="/api/urls [list]")

    @task(1)
    def get_stats(self):
        if not self.my_codes:
            return
        code = random.choice(self.my_codes)
        self.client.get(f"/api/urls/{code}/stats", name="/api/urls/[code]/stats")

    @task(1)
    def delete_url(self):
        if not self.my_codes:
            return
        code = self.my_codes.pop()
        with self.client.delete(
            f"/api/urls/{code}", name="/api/urls/[code] [delete]", catch_response=True
        ) as response:
            if response.status_code == 204:
                response.success()
            else:
                response.failure(f"delete failed: {response.status_code}")