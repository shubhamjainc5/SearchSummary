
import time
from utils.logging_handler import Logger
from functools import wraps


def timed(func):
    """This decorator prints the execution time for the decorated function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        Logger.debug("{} ran in {}s".format(func.__name__, round(end - start, 2)))
        return result

    return wrapper
