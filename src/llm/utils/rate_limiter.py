from time import time
from threading import Lock

class RateLimiter:
    def __init__(self, rate_limit_per_minute: int):
        self.rate_limit_per_minute = rate_limit_per_minute
        self.allowance = rate_limit_per_minute
        self.last_check = time()
        self.lock = Lock()

    def _refill(self):
        current_time = time()
        elapsed = current_time - self.last_check
        self.allowance += elapsed * (self.rate_limit_per_minute / 60)
        if self.allowance > self.rate_limit_per_minute:
            self.allowance = self.rate_limit_per_minute
        self.last_check = current_time

    def acquire(self):
        with self.lock:
            self._refill()
            if self.allowance < 1:
                return False
            self.allowance -= 1
            return True

    def wait(self):
        while not self.acquire():
            time.sleep(1)