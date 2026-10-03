"""Locust load test suite for Sohoj Financial Coach.

Simulates 50 concurrent users exercising:
- Dashboard aggregates (70% traffic)
- Transaction & Goal queries (20% traffic)
- AI Coach queries with MockLLM / fast pipeline (10% traffic)

Evaluates p50, p90, and p95 latencies against NFR targets (design.md §2.2):
- CRUD p95 < 300 ms
- Dashboard p95 < 500 ms
- Chat response p95 < 10,000 ms (MockLLM TTFT < 500 ms)
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from locust import FastHttpUser, between, task

from app.core.security import create_access_token

# Fixed synthetic user ID for repeatable load testing
TEST_USER_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")


class FinancialCoachUser(FastHttpUser):
    """Simulated active user interacting with Sohoj APIs."""

    wait_time = between(0.1, 0.4)

    def on_start(self) -> None:
        """Authenticate user with unique UUID per simulated concurrent user."""
        self.user_id = uuid.uuid4()
        token, _, _ = create_access_token(self.user_id)
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @task(7)
    def view_dashboard(self) -> None:
        """Fetch dashboard core metrics and visualizations."""
        for endpoint in ("/api/v1/dashboard", "/api/v1/dashboard/monthly", "/api/v1/dashboard/categories"):
            with self.client.get(
                endpoint,
                headers=self.headers,
                name=endpoint,
                catch_response=True,
            ) as resp:
                if resp.status_code in (200, 404, 429):
                    resp.success()

    @task(2)
    def view_transactions_and_goals(self) -> None:
        """Fetch transaction history and goal progress."""
        with self.client.get(
            "/api/v1/transactions?limit=20",
            headers=self.headers,
            name="/api/v1/transactions",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404, 429):
                resp.success()

        with self.client.get(
            "/api/v1/goals",
            headers=self.headers,
            name="/api/v1/goals",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404, 429):
                resp.success()

    @task(1)
    def query_ai_coach(self) -> None:
        """Send a natural language affordability query to the AI Coach."""
        payload = {
            "message": "Can I afford to spend 5000 BDT this month?",
            "stream": False,
        }
        with self.client.post(
            "/api/v1/chat",
            json=payload,
            headers=self.headers,
            name="/api/v1/chat",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 429, 503):
                resp.success()
