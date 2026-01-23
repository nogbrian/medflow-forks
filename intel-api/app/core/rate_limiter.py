"""Rate limiter with random delays and exponential backoff."""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional
import structlog

logger = structlog.get_logger()


class RateLimiter:
    """
    Rate limiter for Instagram requests.

    Features:
    - Random delay between requests (2-5 seconds by default)
    - Exponential backoff on rate limit detection
    - Jitter to appear more human-like
    """

    def __init__(
        self,
        min_delay: float = 2.0,
        max_delay: float = 5.0,
        backoff_base: float = 2.0,
        max_backoff: float = 300.0,  # 5 minutes max
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.backoff_base = backoff_base
        self.max_backoff = max_backoff
        self._consecutive_errors = 0
        self._last_request_time: Optional[datetime] = None
        self._blocked_until: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        """Wait before making the next request."""
        async with self._lock:
            now = datetime.utcnow()

            # Check if we're in a backoff period
            if self._blocked_until and now < self._blocked_until:
                wait_seconds = (self._blocked_until - now).total_seconds()
                logger.warning("rate_limiter_blocked", wait_seconds=wait_seconds)
                await asyncio.sleep(wait_seconds)

            # Calculate delay since last request
            if self._last_request_time:
                elapsed = (now - self._last_request_time).total_seconds()
                min_wait = self._get_delay_with_jitter()

                if elapsed < min_wait:
                    await asyncio.sleep(min_wait - elapsed)

            self._last_request_time = datetime.utcnow()

    def _get_delay_with_jitter(self) -> float:
        """Get a random delay with jitter."""
        base_delay = random.uniform(self.min_delay, self.max_delay)
        # Add small jitter (±10%)
        jitter = base_delay * random.uniform(-0.1, 0.1)
        return base_delay + jitter

    def report_success(self) -> None:
        """Report a successful request, resetting backoff."""
        self._consecutive_errors = 0
        self._blocked_until = None
        logger.debug("rate_limiter_success")

    def report_rate_limit(self, retry_after: Optional[int] = None) -> None:
        """
        Report a rate limit error, triggering exponential backoff.

        Args:
            retry_after: Optional number of seconds from Instagram's Retry-After header
        """
        self._consecutive_errors += 1

        if retry_after:
            backoff_seconds = retry_after
        else:
            # Exponential backoff: 2^n seconds, capped at max_backoff
            backoff_seconds = min(
                self.backoff_base ** self._consecutive_errors,
                self.max_backoff
            )

        # Add jitter (±20%)
        jitter = backoff_seconds * random.uniform(-0.2, 0.2)
        backoff_seconds = backoff_seconds + jitter

        self._blocked_until = datetime.utcnow() + timedelta(seconds=backoff_seconds)

        logger.warning(
            "rate_limiter_backoff",
            consecutive_errors=self._consecutive_errors,
            backoff_seconds=backoff_seconds,
        )

    @property
    def is_blocked(self) -> bool:
        """Check if currently in backoff period."""
        if self._blocked_until is None:
            return False
        return datetime.utcnow() < self._blocked_until

    @property
    def seconds_until_unblocked(self) -> float:
        """Get seconds until backoff period ends."""
        if not self._blocked_until:
            return 0.0
        remaining = (self._blocked_until - datetime.utcnow()).total_seconds()
        return max(0.0, remaining)


# Global rate limiter instance
rate_limiter = RateLimiter()
