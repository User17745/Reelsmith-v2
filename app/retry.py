import time


def retry_with_backoff(fn, retries=3, base_delay=1.0, exceptions=(Exception,)):
    for attempt in range(retries):
        try:
            return fn()
        except exceptions:
            if attempt == retries - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))
