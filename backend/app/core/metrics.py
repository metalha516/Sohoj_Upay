"""Prometheus metrics definitions and helper utilities for Sohoj."""

from __future__ import annotations

import time
from typing import Callable
from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# ==================== HTTP & API METRICS ====================

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ==================== DATABASE METRICS ====================

DB_POOL_SIZE = Gauge(
    "db_pool_size",
    "Configured maximum database connection pool size",
)

DB_CONNECTIONS_IN_USE = Gauge(
    "db_connections_in_use",
    "Current active database connections checked out from the pool",
)

# ==================== OUTBOX & QUEUE METRICS ====================

OUTBOX_EVENTS_PENDING = Gauge(
    "outbox_events_pending",
    "Number of pending outbox events awaiting asynchronous processing",
)

OUTBOX_LAG_SECONDS = Gauge(
    "outbox_lag_seconds",
    "Time delta in seconds since the oldest pending outbox event was created",
)

OUTBOX_EVENTS_PROCESSED_TOTAL = Counter(
    "outbox_events_processed_total",
    "Total outbox events processed by the asynchronous worker",
    ["status"],
)

# ==================== ML & DRIFT METRICS ====================

ML_INFERENCE_DURATION_SECONDS = Histogram(
    "ml_inference_duration_seconds",
    "Machine learning model inference execution latency in seconds",
    ["model_name"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)

ML_DRIFT_PSI_SCORE = Gauge(
    "ml_drift_psi_score",
    "Population Stability Index (PSI) tracking distribution drift",
    ["feature_name"],
)

ML_DRIFT_KS_STATISTIC = Gauge(
    "ml_drift_ks_statistic",
    "Kolmogorov-Smirnov (KS) two-sample drift statistic",
    ["feature_name"],
)

ML_FORECAST_MAPE = Gauge(
    "ml_forecast_mape",
    "Mean Absolute Percentage Error for financial forecast predictions",
    ["metric"],
)

ANOMALY_EVENTS_TOTAL = Counter(
    "anomaly_events_total",
    "Total financial anomaly alerts processed",
    ["status"],  # "detected", "confirmed", "dismissed"
)

# ==================== LLM & AI METRICS ====================

LLM_REQUEST_DURATION_SECONDS = Histogram(
    "llm_request_duration_seconds",
    "Latency of LLM requests in seconds",
    ["provider", "model"],
    buckets=[0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0, 20.0],
)

LLM_TOKENS_TOTAL = Counter(
    "llm_tokens_total",
    "Cumulative token consumption by the conversational AI coach",
    ["direction", "model"],  # direction: "in" (prompt), "out" (completion)
)

LLM_TOOL_CALLS_TOTAL = Counter(
    "llm_tool_calls_total",
    "Total tool calls invoked by the GenAI financial orchestrator",
    ["tool_name", "status"],  # status: "success", "error"
)

LLM_VALIDATOR_REJECTIONS_TOTAL = Counter(
    "llm_validator_rejections_total",
    "Total conversational turns rejected by AI safety validators",
    ["validator_type"],  # "injection", "boundary", "grounding"
)

RAG_RETRIEVAL_HIT_RATE = Gauge(
    "rag_retrieval_hit_rate",
    "Retrieval benchmark hit rate over the curated financial literacy corpus",
    ["metric"],  # "hit_at_1", "hit_at_4"
)

# ==================== SECURITY METRICS (§13.3) ====================

AUTH_LOGIN_FAILURES_TOTAL = Counter(
    "auth_login_failures_total",
    "Total failed login attempts",
)

AUTH_REFRESH_TOKEN_REUSE_TOTAL = Counter(
    "auth_refresh_token_reuse_total",
    "Total detected refresh token reuse attacks triggering family revocation",
)

RATE_LIMIT_EXCEEDED_TOTAL = Counter(
    "rate_limit_exceeded_total",
    "Total requests rejected by rate limiting controllers",
    ["limiter"],
)


def get_prometheus_metrics() -> Response:
    """Generate Prometheus exposition text format response."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


async def prometheus_metrics_middleware(request: Request, call_next: Callable) -> Response:
    """FastAPI middleware tracking request durations, counts, and status codes."""
    if request.url.path == "/metrics" or request.url.path.startswith("/health"):
        return await call_next(request)

    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        status_code = 500
        raise
    finally:
        latency = time.perf_counter() - start_time
        # Normalize endpoint path to avoid cardinality explosion
        path = request.scope.get("root_path", "") + request.url.path
        # Collapse UUID and numerical IDs in path
        parts = [
            ":id" if (len(p) == 36 and "-" in p) or p.isdigit() else p
            for p in path.split("/")
        ]
        endpoint = "/".join(parts) or "/"

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(status_code),
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(latency)
