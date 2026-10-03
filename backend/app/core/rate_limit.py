"""Rate limiting and account lockout protection with Redis and in-memory fallback.

Adheres strictly to security.md §3 & §5:
- Per-account and per-IP login failure tracking with exponential backoff / lockout.
- Sliding window / fixed window rate limiting per route.
- Graceful in-memory fallback when Redis is unreachable or during unit testing.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger("app.security.rate_limit")


class InMemoryStore:
    """In-memory sliding window store with automatic expiry cleanup."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lockouts: dict[str, float] = {}

    def is_locked(self, key: str) -> tuple[bool, int]:
        now = time.time()
        lock_until = self._lockouts.get(key, 0.0)
        if lock_until > now:
            return True, int(lock_until - now)
        if key in self._lockouts:
            del self._lockouts[key]
        return False, 0

    def set_lockout(self, key: str, duration_seconds: int) -> None:
        self._lockouts[key] = time.time() + duration_seconds

    def clear_lockout(self, key: str) -> None:
        self._lockouts.pop(key, None)

    def record_hit(self, key: str, window_seconds: int) -> int:
        now = time.time()
        cutoff = now - window_seconds
        # Retain only timestamps within the window
        valid_hits = [t for t in self._hits[key] if t > cutoff]
        valid_hits.append(now)
        self._hits[key] = valid_hits
        return len(valid_hits)

    def clear_hits(self, key: str) -> None:
        self._hits.pop(key, None)

    def reset_all(self) -> None:
        self._hits.clear()
        self._lockouts.clear()


# Global in-memory fallback store
_in_memory_store = InMemoryStore()


class RateLimiter:
    """Sliding-window rate limiter utilizing Redis with transparent in-memory fallback."""

    def __init__(self, redis_client: Any = None) -> None:
        self.redis_client = redis_client

    async def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int, int]:
        """Check if request is allowed under rate limit.

        Returns:
            tuple of (is_allowed: bool, current_count: int, retry_after_seconds: int)
        """
        if self.redis_client:
            try:
                now = time.time()
                pipeline = self.redis_client.pipeline()
                pipeline.zremrangebyscore(key, 0, now - window_seconds)
                pipeline.zadd(key, {str(now): now})
                pipeline.zcard(key)
                pipeline.expire(key, window_seconds)
                results = await pipeline.execute()
                current_count = int(results[2])
                if current_count > max_requests:
                    return False, current_count, window_seconds
                return True, current_count, 0
            except Exception as exc:
                logger.warning("Redis rate limit query failed; falling back to memory: %s", exc)

        # In-memory sliding window fallback
        count = _in_memory_store.record_hit(key, window_seconds)
        if count > max_requests:
            return False, count, window_seconds
        return True, count, 0

    def reset(self) -> None:
        """Reset in-memory storage (for testing)."""
        _in_memory_store.reset_all()


class LockoutManager:
    """Manages consecutive authentication failures and temporary account lockouts."""

    def __init__(self, redis_client: Any = None) -> None:
        self.redis_client = redis_client

    async def check_lockout(self, identifier: str) -> tuple[bool, int]:
        """Check if user or IP identifier is currently locked out.

        Returns:
            tuple of (is_locked: bool, retry_after_seconds: int)
        """
        key = f"lockout:{identifier.lower().strip()}"
        if self.redis_client:
            try:
                ttl = await self.redis_client.ttl(key)
                if ttl and ttl > 0:
                    return True, int(ttl)
                return False, 0
            except Exception as exc:
                logger.warning("Redis lockout check failed; falling back to memory: %s", exc)

        return _in_memory_store.is_locked(key)

    async def record_failure(self, identifier: str) -> tuple[int, bool]:
        """Record an authentication failure. Lock out if threshold exceeded.

        Returns:
            tuple of (current_failures: int, is_locked_now: bool)
        """
        settings = get_settings()
        clean_id = identifier.lower().strip()
        fail_key = f"login_failures:{clean_id}"
        lock_key = f"lockout:{clean_id}"

        if self.redis_client:
            try:
                failures = await self.redis_client.incr(fail_key)
                if failures == 1:
                    await self.redis_client.expire(fail_key, settings.lockout_duration_seconds)
                if failures >= settings.max_login_attempts:
                    await self.redis_client.setex(
                        lock_key, settings.lockout_duration_seconds, "locked"
                    )
                    return failures, True
                return failures, False
            except Exception as exc:
                logger.warning("Redis failure record failed; falling back to memory: %s", exc)

        failures = _in_memory_store.record_hit(fail_key, settings.lockout_duration_seconds)
        if failures >= settings.max_login_attempts:
            _in_memory_store.set_lockout(lock_key, settings.lockout_duration_seconds)
            return failures, True
        return failures, False

    async def reset_failures(self, identifier: str) -> None:
        """Reset failed attempt counters upon successful authentication."""
        clean_id = identifier.lower().strip()
        fail_key = f"login_failures:{clean_id}"
        lock_key = f"lockout:{clean_id}"

        if self.redis_client:
            try:
                await self.redis_client.delete(fail_key, lock_key)
                return
            except Exception as exc:
                logger.warning("Redis failure reset failed: %s", exc)

        _in_memory_store.clear_hits(fail_key)
        _in_memory_store.clear_lockout(lock_key)

    def reset_all(self) -> None:
        """Reset all in-memory lockouts and hits (for testing)."""
        _in_memory_store.reset_all()


# Singleton instances
rate_limiter = RateLimiter()
lockout_manager = LockoutManager()
