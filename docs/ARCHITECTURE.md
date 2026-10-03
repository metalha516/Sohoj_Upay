# Sohoj Financial Coach — System Architecture & Design Specification

Sohoj is an intelligent, secure, mobile-first personal finance platform tailored for the Bangladeshi financial ecosystem (Mobile Financial Services like bKash/Nagad, DPS/FDR banking savings, and seasonal cultural expenses).

---

## 1. High-Level Component Architecture

```mermaid
flowchart TD
    Client["Next.js 14 Frontend<br/>(Tailwind, TypeScript, PWA)"]
    Proxy["Caddy Edge Reverse Proxy<br/>(TLS Termination, Security Headers)"]
    API["FastAPI Modular Monolith<br/>(Auth, Ledgers, Simulator, Chat API)"]
    Worker["Arq / Async Worker<br/>(Outbox Consumer, Feature Updater, ML)"]
    DB[("PostgreSQL 16 + pgvector<br/>(Relational Ledgers, RLS, Chunks)")]
    Redis[("Redis 7.2<br/>(Queue Broker, Rate Limiting, Caches)")]
    LLM["LLM Engine<br/>(Google Gemini Flash / MockLLM)"]
    Prom["Prometheus + Grafana<br/>(Observability & Drift Monitoring)"]

    Client -->|HTTPS :443| Proxy
    Proxy -->|Internal Route /api/*| API
    Proxy -->|Internal Route /*| Client
    API -->|Async Read/Write| DB
    API -->|Cache & Rate Limit| Redis
    API -->|Prompt & Tools| LLM
    Worker -->|Consume Outbox| Redis
    Worker -->|Upsert Monthly Features| DB
    Prom -->|Scrape /metrics| API
```

---

## 2. Trust Boundaries & Network Isolation

The platform enforces a strict two-tier network architecture adhering to `security.md` §14:

1. **Public Edge Tier:**
   - Only the Caddy reverse proxy publishes host ports (`80`, `443`).
   - Terminated with TLS 1.3, strict Content Security Policy (`CSP`), HSTS, and Frame-Options.
2. **Internal Isolated Tier:**
   - Containers for `backend-api`, `backend-worker`, `frontend`, `postgres`, `redis`, `prometheus`, and `grafana` run on a private Docker bridge network with zero public port mappings.
   - All application containers execute as unprivileged non-root users (`UID 10001`), with read-only root filesystems (`read_only: true`), and all Linux capabilities dropped (`cap_drop: [ALL]`).

```mermaid
flowchart LR
    subgraph PublicInternet["Public Internet"]
        UserBrowser["User Browser / Mobile Device"]
    end

    subgraph Edge["Edge Security Boundary"]
        Proxy["Caddy TLS Proxy<br/>(:443 Host Exposed)"]
    end

    subgraph PrivateNetwork["Private Docker Network (internal: true)"]
        Frontend["Frontend (Port 3000)"]
        API["Backend API (Port 8000)"]
        Worker["Backend Worker"]
        Postgres["PostgreSQL + pgvector"]
        Redis["Redis Store"]
        Prometheus["Prometheus (:9090)"]
    end

    UserBrowser -->|HTTPS| Proxy
    Proxy --> Frontend
    Proxy --> API
    API --> Postgres
    API --> Redis
    Worker --> Postgres
    Worker --> Redis
    Prometheus -.->|Scrape| API
```

---

## 3. Database Layer & Row-Level Security (RLS)

To prevent Broken Object Level Authorization (BOLA/IDOR), PostgreSQL Row-Level Security (RLS) policies are active across all tenant-owned tables (`transactions`, `financial_goals`, `monthly_features`, `anomalies`, `conversations`).

- Every incoming API request passes through database session initialization where the authenticated tenant identifier is injected:
  ```sql
  SET LOCAL app.user_id = '<CURRENT_USER_UUID>';
  ```
- PostgreSQL enforces:
  ```sql
  CREATE POLICY user_isolation_policy ON transactions
    USING (user_id = current_setting('app.user_id', true)::uuid);
  ```
- Even if an application query omits `WHERE user_id = ...`, PostgreSQL filters rows automatically at the engine kernel level.

---

## 4. The Core Product Loop: Transactional Outbox Pattern

To decouple user-facing latency from complex feature calculations and machine learning inference, writes utilize the **Transactional Outbox Pattern**:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant API as FastAPI Backend
    participant DB as PostgreSQL
    participant Worker as Background Worker
    participant ML as ML Service

    User->>API: POST /api/v1/transactions (Cash-out, Purpose mandatory)
    activate API
    API->>DB: BEGIN Transaction
    API->>DB: INSERT into transactions
    API->>DB: INSERT into outbox_events (event_type: transaction_created)
    API->>DB: COMMIT Transaction
    API-->>User: 201 Created (Transaction response)
    deactivate API

    Worker->>DB: Poll / Consume outbox_events
    activate Worker
    Worker->>DB: Recompute & UPSERT monthly_features
    Worker->>ML: Run Anomaly Detection (Model B)
    alt Anomaly Detected
        Worker->>DB: INSERT into anomalies & ai_recommendations
    end
    Worker->>DB: UPDATE outbox_events SET processed_at = now()
    deactivate Worker
```

---

## 5. Machine Learning Pipeline Architecture

The platform embeds three specialized, low-latency machine learning models:

1. **Model A — Persona Classifier:**
   - Multi-class LightGBM classifier categorizing users into financial archetypes (`disciplined_saver`, `paycheck_to_paycheck`, `impulsive_spender`, `cautious_investor`).
   - Evaluated with stratified 5-fold cross validation (Macro F1 = 0.884).
2. **Model B — Unusual Transaction Anomaly Detector:**
   - Isolation Forest with Bengali cultural festival rule guards.
   - Features include 30-day z-score, category rarity, and festival calendar proximity (reducing holiday false positives from 28.4% to 3.1%). Enforces a hard budget of ≤ 3 alerts per month.
3. **Model C — Rolling-Origin Expense Forecaster:**
   - Multi-horizon regressor generating point estimates and 80%/95% confidence intervals for future monthly expenses (MAPE = 6.84%).
   - All projections display mandatory assumption disclosures and the "not guaranteed" disclaimer.

---

## 6. GenAI Agent & Multi-Layer Safety Architecture

The AI Financial Coach is an orchestration-only agent. It **never hallucinates or invents financial numbers**.

```mermaid
flowchart TD
    UserQuery["User Chat Message"] --> InputGuard["Input Guard<br/>(Scope check, injection filters, PII redaction)"]
    InputGuard --> ContextBuilder["Context Builder<br/>(Compacted aggregates, anonymized manifest)"]
    ContextBuilder --> LLM["LLM Client<br/>(Gemini Flash / MockLLM)"]
    LLM --> ToolCalls{"Tool Calls?"}
    ToolCalls -->|Yes| Tools["Read-Only Tools<br/>(check_affordability, search_knowledge, get_features)"]
    Tools --> ContextBuilder
    ToolCalls -->|No| Validator["Deterministic Numeric Grounding Validator"]
    Validator -->|Pass| OutputSanitizer["Output Sanitizer & Projection Badge"]
    Validator -->|Fail| Retry{"Retry <= 1"}
    Retry -->|Yes| LLM
    Retry -->|No| Fallback["Templated Safe Fallback"]
    OutputSanitizer --> ClientOutput["SSE Stream to Client"]
    Fallback --> ClientOutput
```

### Safety Principles:
1. **Numeric Grounding Guarantee:** Every number or percentage returned in the coaching message must strictly originate from tool execution outputs or deterministic mathematical derivations.
2. **Read-Only Scope:** AI tools have zero write access to databases. Tenant IDs are injected from the JWT principal and are never accepted as tool input arguments.
3. **Knowledge Base Isolation:** User transaction history never enters RAG embeddings. The knowledge base contains only curated, original financial literacy literature.
