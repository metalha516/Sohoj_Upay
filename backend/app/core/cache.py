"""Caching utility supporting Redis with seamless in-memory fallback per security.md §3."""

from __future__ import annotations

import fnmatch
import json
import logging
import time
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger("app.core.cache")


class CacheManager:
    """Multi-tier cache manager with Redis primary and in-memory TTL fallback."""

    def __init__(self) -> None:
        self._in_memory: dict[str, tuple[str, float]] = {}  # key -> (serialized_value, expire_at)
        self._redis_client: Any = None
        self._redis_disabled: bool = False

    async def _get_redis(self) -> Any:
        if self._redis_disabled:
            return None
        if self._redis_client is not None:
            return self._redis_client

        settings = get_settings()
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(  # type: ignore[no-untyped-call]
                settings.redis_url,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
                decode_responses=True,
            )
            # Test ping
            await client.ping()
            self._redis_client = client
            return self._redis_client
        except Exception:
            self._redis_client = None
            self._redis_disabled = True
            return None

    async def get(self, key: str) -> Any | None:
        """Retrieve cached value if present and not expired."""
        redis = await self._get_redis()
        if redis:
            try:
                raw = await redis.get(key)
                if raw is not None:
                    return json.loads(raw)
            except Exception:
                self._redis_disabled = True

        # Fallback to in-memory store
        now = time.time()
        entry = self._in_memory.get(key)
        if entry:
            val_str, expire_at = entry
            if expire_at > now:
                return json.loads(val_str)
            del self._in_memory[key]

        return None

    async def set(self, key: str, value: Any, ttl: int = 60) -> None:
        """Store value with TTL in seconds (default 60s)."""
        val_str = json.dumps(value, default=str)
        redis = await self._get_redis()
        if redis:
            try:
                await redis.set(key, val_str, ex=ttl)
                return
            except Exception:
                self._redis_disabled = True

        # In-memory store
        self._in_memory[key] = (val_str, time.time() + ttl)

    async def delete(self, key: str) -> None:
        """Invalidate a specific cache key."""
        redis = await self._get_redis()
        if redis:
            try:
                await redis.delete(key)
            except Exception:
                self._redis_disabled = True

        self._in_memory.pop(key, None)

    async def delete_pattern(self, pattern: str) -> None:
        """Invalidate all keys matching the glob pattern (e.g. 'dashboard:{user_id}:*')."""
        redis = await self._get_redis()
        if redis:
            try:
                keys = await redis.keys(pattern)
                if keys:
                    await redis.delete(*keys)
            except Exception:
                self._redis_disabled = True

        # In-memory glob match
        matched_keys = [k for k in self._in_memory if fnmatch.fnmatch(k, pattern)]
        for k in matched_keys:
            del self._in_memory[k]

    def clear_in_memory(self) -> None:
        """Clear local in-memory storage (useful during unit testing)."""
        self._in_memory.clear()
        self._redis_client = None
        self._redis_disabled = False


cache_manager = CacheManager()
