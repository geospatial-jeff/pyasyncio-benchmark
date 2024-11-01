import asyncio
from functools import wraps


def semaphore(n):
    """Decorates a coroutine with a semaphore."""
    semaphore = asyncio.Semaphore(n)

    def _semaphore(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            async with semaphore:
                return await f(*args, **kwargs)

        return wrapper

    return _semaphore
