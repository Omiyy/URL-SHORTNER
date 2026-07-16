import random
import string
from locust import FastHttpUser, task, TaskSet, between

def generate_random_url():
    domain = random.choice(["example.com", "test.org", "demo.net", "sample.io"])
    path = "".join(random.choices(string.ascii_letters, k=10))
    return f"https://{domain}/{path}"

class HighThroughputRedirection(TaskSet):
    """
    Isolates the GET cache-hit route for precise latency measurement.
    """
    
    @task
    def redirect_cache_hit(self):
        # Only request the real short_code generated during on_start
        if self.user.shared_short_code:
            self.client.get(
                f"/{self.user.shared_short_code}",
                name="GET /<short_code> (Cache Hit)"
            )
            
    # Completely removed/commented out any POST @tasks or other GET tasks
    # to eliminate 404s and strictly isolate cache performance.
    # @task
    # def create_short_url(self):
    #     self.client.post("/api/shorten", ...)

class FastURLUser(FastHttpUser):
    wait_time = between(0.1, 0.5)
    
    # Only run the cache hit task set
    tasks = {HighThroughputRedirection: 1}

    def on_start(self):
        """
        Sends a single POST request to generate a real short link,
        saving it to a class variable to avoid 404 errors during the test.
        """
        self.shared_short_code = None
        
        response = self.client.post(
            "/api/shorten",
            json={"url": generate_random_url()}
        )
        
        if response.status_code == 201:
            self.shared_short_code = response.json()["short_code"]
        else:
            print(f"Failed to create URL during setup! Status: {response.status_code}")
