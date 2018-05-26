import threading
import time
import logging
from functools import wraps


def rate_limited(max_per_second):
    """
    Decorator that make functions not be called faster than
    """
    lock = threading.Lock()
    min_interval = 1.0 / float( max_per_second )

    def decorate(func):
        last_time_called = [0.0]

        @wraps( func )
        def rate_limited_function(*args, **kwargs):
            lock.acquire()
            elapsed = time.clock() - last_time_called[0]
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                logging.warning('throttled')
                time.sleep( left_to_wait )

            lock.release()

            ret = func( *args, **kwargs )
            last_time_called[0] = time.clock()
            return ret

        return rate_limited_function

    return decorate
