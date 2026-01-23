"""Retry decorator with exponential backoff."""

import asyncio
import functools
from typing import Callable, Tuple, Type
import structlog

from app.services.scraper.exceptions import (
    NetworkError,
    BrowserError,
    RateLimitError,
)

logger = structlog.get_logger()

# Exceptions that should trigger a retry
TRANSIENT_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    NetworkError,
    BrowserError,
    asyncio.TimeoutError,
    ConnectionError,
    TimeoutError,
)


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = TRANSIENT_EXCEPTIONS,
):
    """
    Decorator for automatic retry with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds (1s)
        max_delay: Maximum delay between retries (30s)
        exponential_base: Base for exponential backoff (2.0 = 1s → 2s → 4s → 8s)
        retryable_exceptions: Tuple of exceptions that should trigger retry

    Example:
        @with_retry(max_attempts=3)
        async def fetch_data():
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)

                    if attempt > 1:
                        logger.info(
                            "retry_succeeded",
                            function=func.__name__,
                            attempt=attempt,
                        )

                    return result

                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            "retry_exhausted",
                            function=func.__name__,
                            attempts=max_attempts,
                            error=str(e),
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )

                    logger.warning(
                        "retry_attempt",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay=delay,
                        error=str(e),
                    )

                    await asyncio.sleep(delay)

                except RateLimitError as e:
                    # Rate limit errors should use the retry_after value
                    last_exception = e

                    if attempt == max_attempts:
                        raise

                    delay = min(e.retry_after, max_delay)
                    logger.warning(
                        "retry_rate_limited",
                        function=func.__name__,
                        attempt=attempt,
                        retry_after=e.retry_after,
                    )

                    await asyncio.sleep(delay)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def retry_on_network_error(func: Callable):
    """Shortcut decorator for network error retries."""
    return with_retry(
        max_attempts=3,
        base_delay=1.0,
        retryable_exceptions=(NetworkError, asyncio.TimeoutError, ConnectionError),
    )(func)
