"""Circuit breaker, daily token budgeting, and graceful degradation for LLM operations."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime

from app.core.cache import cache_manager

logger = logging.getLogger(__name__)

DEFAULT_DAILY_TOKEN_BUDGET = 50_000
CIRCUIT_FAILURE_THRESHOLD = 3
CIRCUIT_RECOVERY_TIMEOUT_SECONDS = 30.0

GRACEFUL_FALLBACK_TEXT = (
    "Our AI coaching assistant is temporarily unavailable. "
    "Your dashboard, transactions, and financial simulators remain fully operational. "
    "Please check your Shohoj Upay dashboard for your latest financial insights."
)


class DailyTokenBudgetExceededError(Exception):
    """Raised when a user reaches their daily allocated token budget."""

    def __init__(
        self,
        message: str = (
            "You have reached your daily AI coaching token limit. "
            "Your quota will reset tomorrow at midnight UTC."
        ),
    ) -> None:
        super().__init__(message)
        self.message = message


class CircuitBreakerOpenError(Exception):
    """Raised when the LLM provider circuit breaker is OPEN due to consecutive outages."""

    def __init__(self, message: str = GRACEFUL_FALLBACK_TEXT) -> None:
        super().__init__(message)
        self.message = message


class TokenBudgetManager:
    """Tracks and enforces per-user daily token allocations via cache with in-memory fallback."""

    def __init__(self, daily_budget: int = DEFAULT_DAILY_TOKEN_BUDGET) -> None:
        self.daily_budget = daily_budget
        self._memory_store: dict[str, int] = {}

    def _get_key(self, user_id: uuid.UUID) -> str:
        today_str = datetime.now(UTC).date().isoformat()
        return f"budget:tokens:{user_id}:{today_str}"

    async def get_usage(self, user_id: uuid.UUID) -> int:
        """Get total tokens consumed today by this user."""
        key = self._get_key(user_id)
        cached = await cache_manager.get(key)
        if cached is not None:
            try:
                return int(cached)
            except (ValueError, TypeError):
                pass
        return self._memory_store.get(key, 0)

    async def check_budget(self, user_id: uuid.UUID, estimated_tokens: int = 500) -> None:
        """Verify user is within budget. Raises DailyTokenBudgetExceededError if over limit."""
        current = await self.get_usage(user_id)
        if current + estimated_tokens > self.daily_budget:
            logger.warning(
                "Daily token budget exceeded for user %s: current %d + est %d > limit %d",
                user_id,
                current,
                estimated_tokens,
                self.daily_budget,
            )
            raise DailyTokenBudgetExceededError()

    async def record_usage(self, user_id: uuid.UUID, tokens: int) -> int:
        """Record consumed tokens and return new total."""
        key = self._get_key(user_id)
        current = await self.get_usage(user_id)
        new_total = current + max(0, tokens)
        self._memory_store[key] = new_total
        # Store in cache with 25-hour TTL to span midnight boundaries safely
        await cache_manager.set(key, new_total, ttl=90_000)
        return new_total


class LLMCircuitBreaker:
    """Three-state circuit breaker (CLOSED, OPEN, HALF_OPEN) safeguarding against downstream LLM outages."""

    def __init__(
        self,
        failure_threshold: int = CIRCUIT_FAILURE_THRESHOLD,
        recovery_timeout: float = CIRCUIT_RECOVERY_TIMEOUT_SECONDS,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count: int = 0
        self.last_failure_time: float = 0.0

    def can_execute(self) -> bool:
        """Check whether execution is permitted."""
        now = time.monotonic()
        if self.state == "OPEN":
            if now - self.last_failure_time >= self.recovery_timeout:
                logger.info("Circuit breaker entering HALF_OPEN probe state.")
                self.state = "HALF_OPEN"
                return True
            return False
        return True

    def record_success(self) -> None:
        """Record successful call, closing the circuit."""
        if self.state != "CLOSED":
            logger.info("Circuit breaker recovered: transitioning to CLOSED.")
        self.state = "CLOSED"
        self.failure_count = 0

    def record_failure(self, error: Exception | None = None) -> None:
        """Record failure, potentially tripping the circuit to OPEN."""
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        logger.warning(
            "Circuit breaker failure %d/%d: %s",
            self.failure_count,
            self.failure_threshold,
            error,
        )
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(
                "Circuit breaker tripped OPEN. All calls will be short-circuited for %.1f seconds.",
                self.recovery_timeout,
            )


default_circuit_breaker = LLMCircuitBreaker()
default_token_budget_manager = TokenBudgetManager()
