import asyncio
import time
import logging
from functools import wraps
from typing import Callable, Any, Coroutine, Optional
from .config import config

logger = logging.getLogger(__name__)

def retry_with_backoff(max_retries: Optional[int] = None, delay: Optional[float] = None):
    """Retry decorator supporting sync and async functions with optional exponential backoff."""
    def decorator(func: Callable):
        async def async_inner(*args, **kwargs):
            retries = max_retries or config.max_retries
            base_delay = delay or config.retry_delay
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:  # pragma: no cover - broad catch for reliability
                    if attempt == retries - 1:
                        logger.error(f"{func.__name__} failed after {retries} attempts: {e}")
                        raise
                    wait = base_delay * (2 ** attempt if config.exponential_backoff else 1)
                    logger.warning(f"{func.__name__} attempt {attempt+1} failed: {e}; retrying in {wait}s")
                    await asyncio.sleep(wait)
        def sync_inner(*args, **kwargs):
            retries = max_retries or config.max_retries
            base_delay = delay or config.retry_delay
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:  # pragma: no cover
                    if attempt == retries - 1:
                        logger.error(f"{func.__name__} failed after {retries} attempts: {e}")
                        raise
                    wait = base_delay * (2 ** attempt if config.exponential_backoff else 1)
                    logger.warning(f"{func.__name__} attempt {attempt+1} failed: {e}; retrying in {wait}s")
                    time.sleep(wait)
        if asyncio.iscoroutinefunction(func):
            return wraps(func)(async_inner)
        return wraps(func)(sync_inner)
    return decorator
