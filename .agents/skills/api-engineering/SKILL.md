---
name: api-engineering
description: Standards and patterns for robust API connection management, dynamic base URL resolution, zero-hardcoding environment configuration, and RFC 7807 contract enforcement. Trigger when auditing or refactoring API clients, CORS, middleware, and backend endpoints.
---

# API Engineering & Client Normalization Skill

This skill governs standard practices for resilient frontend-to-backend API communication, eliminating hardcoded URLs, enforcing environment-driven configuration, and ensuring type-safe contract alignment.

## Core Directives

### 1. Dynamic API Base URL Resolution (Zero Hardcoded Hosts)
- **Frontend Client (`api-client.ts`):**
  - Never hardcode `http://localhost:8000` or `http://127.0.0.1:8000` directly in fetch calls.
  - Dynamically resolve the API base:
    1. `process.env.NEXT_PUBLIC_API_BASE_URL` (e.g. `/api/v1` for proxy/rewrite setups).
    2. Fallback to `/api/v1` relative path in browser contexts.
    3. Respect server-side runtime `BACKEND_URL` or `INTERNAL_API_URL` during SSR.
- **Next.js Rewrites (`next.config.mjs`):**
  - Drive destination via `process.env.BACKEND_URL || "http://127.0.0.1:8000"`.
- **Edge Middleware (`middleware.ts`):**
  - Dynamically inject connect-src based on `isDev` and configured backend endpoints.

### 2. Request & Response Normalization
- Enforce strict typing via OpenAPI/Pydantic schemas.
- Provide bidirectional normalization for legacy/variant enum values (e.g. `payment` $\leftrightarrow$ `expense`, `send_money` $\leftrightarrow$ `transfer`).
- Handle RFC 7807 Problem Details uniformly across all endpoints.

### 3. Session & Auth Token Management
- Access tokens stored securely in memory with automatic silent refresh via HttpOnly refresh cookie.
- Automatic retry on 401 Unauthorized after refreshing token.
- Seamless redirect handling for unauthenticated requests to protected routes.
