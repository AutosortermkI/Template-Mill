"""Token bucket rate limiter for API calls and scraping."""

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class RateLimiter:
    """Token bucket rate limiter.

    Args:
        rate: Number of tokens added per second.
        max_tokens: Maximum bucket capacity.
    """

    rate: float
    max_tokens: float
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)

    def __post_init__(self) -> None:
        self._tokens = self.max_tokens
        self._last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.max_tokens, self._tokens + elapsed * self.rate)
        self._last_refill = now

    async def acquire(self, tokens: float = 1.0) -> None:
        """Wait until the requested number of tokens are available."""
        while True:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return
            wait_time = (tokens - self._tokens) / self.rate
            await asyncio.sleep(wait_time)

    def try_acquire(self, tokens: float = 1.0) -> bool:
        """Try to acquire tokens without waiting. Returns True if successful."""
        self._refill()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False
