from time import time, sleep
from threading import Lock

class RateLimiter:
    def __init__(self, rate_limit_per_minute: int):
        """
        Args:
            rate_limit_per_minute (int): Maximum number of requests allowed per minute.
        """
        self.rate_limit_per_minute = rate_limit_per_minute
        self.allowance = rate_limit_per_minute
        self.last_check = time()
        self.lock = Lock()

    def _refill(self):
        """
        Refill the allowance based on the elapsed time since the last check.
        """
        current_time = time()
        elapsed = current_time - self.last_check
        refill_amount = elapsed * (self.rate_limit_per_minute / 60)
        self.allowance = min(self.allowance + refill_amount, self.rate_limit_per_minute)
        self.last_check = current_time

    def acquire(self) -> bool:
        """
        Attempt to acquire permission to proceed with a request.

        Returns:
            bool: True if the request is allowed, False otherwise.
        """
        with self.lock:
            self._refill()
            if self.allowance >= 1:
                self.allowance -= 1
                return True
            return False

    def wait(self):
        """
        Block until a request is allowed.
        """
        while not self.acquire():
            sleep(0.1)