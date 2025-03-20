def retry_with_exponential_backoff(func, max_attempts=5, initial_delay=1, backoff_factor=2):
    import time

    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt < max_attempts - 1:
                delay = initial_delay * (backoff_factor ** attempt)
                time.sleep(delay)
            else:
                raise e

def retry_on_exception(max_attempts=5, initial_delay=1, backoff_factor=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return retry_with_exponential_backoff(lambda: func(*args, **kwargs), max_attempts, initial_delay, backoff_factor)
        return wrapper
    return decorator