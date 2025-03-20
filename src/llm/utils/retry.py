import time
import logging


def retry_with_exponential_backoff(
    func,
    max_attempts=5,
    initial_delay=1,
    backoff_factor=2,
    max_delay=None,
    exceptions=(Exception,)
):
    """
    Retry a function with [exponential backoff].

    Args:
        func (callable): The function to retry.
        max_attempts (int): Maximum number of retry attempts.
        initial_delay (float): Initial delay between retries in seconds.
        backoff_factor (float): Factor by which the delay increases after each attempt.
        max_delay (float): Maximum delay between retries in seconds.
        exceptions (tuple): Tuple of exception types to catch and retry.
    """
    logger = logging.getLogger(__name__)
    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            if attempt < max_attempts - 1:
                delay = initial_delay * (backoff_factor ** attempt)
                if max_delay:
                    delay = min(delay, max_delay)
                logger.warning(f"Retry attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_attempts} retry attempts failed.")
                raise e

def retry_on_exception(
    max_attempts=5,
    initial_delay=1,
    backoff_factor=2,
    max_delay=None,
    exceptions=(Exception,)
):
    """
    Decorator to retry a function with exponential backoff on specified exceptions.

    Args:
        max_attempts (int): Maximum number of retry attempts.
        initial_delay (float): Initial delay between retries in seconds.
        backoff_factor (float): Factor by which the delay increases after each attempt.
        max_delay (float): Maximum delay between retries in seconds.
        exceptions (tuple): Tuple of exception types to catch and retry.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            return retry_with_exponential_backoff(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                backoff_factor=backoff_factor,
                max_delay=max_delay,
                exceptions=exceptions
            )
        return wrapper
    return decorator