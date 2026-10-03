# Sohoj Financial Coach — Production Operations Runbook

This operational runbook provides production support engineers, site reliability engineers (SREs), and on-call responders with step-by-step procedures for managing Sohoj in staging and production environments.

---

## 1. System Health & Incident Triage

### Health Checks
- **Public Edge Health:** `GET https://<domain>/healthz` (200 OK from Caddy)
- **API Internal Health:** `GET http://backend-api:8000/health` (returns JSON status, version, database connection)
- **Frontend Health:** `GET http://frontend:3000/` (200 OK)
- **PostgreSQL Health:** `pg_isready -U financial_app -d financial_coach`
- **Redis Health:** `redis-cli ping` (returns `PONG`)

### Critical Alert Runbooks
| Alert Name | Severity | Trigger Condition | Immediate Action |
|---|---|---|---|
| `APIHigh5xxErrorRate` | Critical | HTTP 5xx rate > 2% for 5 min | Check `backend-api` container logs for unhandled exceptions or database connection pool exhaustion. |
| `OutboxProcessingLag` | Warning | Outbox pending events > 100 for 5 min | Inspect `backend-worker` container. Verify Redis queue connectivity. Check for stuck ML inference tasks. |
| `MLFeatureDriftWarning` | Warning | Feature PSI > 0.20 | Run drift analysis report (`python -m app.worker.drift_job`). Evaluate if economic seasonality (Eid/Puja) shifted distributions or if retraining is required. |
| `LLMHighRejectionRate` | Critical | Numeric validator rejection rate > 5% | Inspect recent prompt version changes. Verify mock or upstream LLM provider API compatibility. If necessary, activate `AI_ENABLED=false` kill switch. |

---

## 2. Emergency Kill Switches

When unexpected downstream failures, zero-day vulnerabilities, or external provider outages occur, operators can immediately disable affected subsystems without deploying code.

### Supported Feature Flags (`.env` or Docker environment)
- `AI_ENABLED`: Set to `false` to disable `/api/v1/chat` and coach endpoints (returns HTTP 503 Service Unavailable with friendly fallback).
- `FORECAST_ENABLED`: Set to `false` to disable `/api/v1/forecast/*` and forward-looking projections.
- `REGISTRATION_ENABLED`: Set to `false` to halt new account creations during spam or bot attacks.
- `LOGIN_ENABLED`: Set to `false` during emergency maintenance or forensic investigations.

### Immediate Global Session Invalidation
If a high-impact security breach or credential leak is detected, revoke all outstanding refresh tokens globally:
```bash
curl -X POST https://<domain>/api/v1/admin/revoke-tokens \
  -H "X-Admin-Key: <ADMIN_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"scope": "global"}'
```
This terminates all active sessions, forcing all users to re-authenticate.

---

## 3. Database Backup & Disaster Recovery

### Scheduled Daily Backups
The platform runs automated backups via `scripts/backup_db.py`:
```bash
# Execute snapshot
python scripts/backup_db.py --output-dir /var/backups/sohoj
```
This generates:
- `sohoj_backup_<timestamp>.json.gz`: Gzipped, serialized table snapshot.
- `sohoj_backup_<timestamp>.json.gz.sha256`: Cryptographic SHA-256 integrity checksum.

### Disaster Recovery Restoration Drill
To restore the platform to a pristine database instance:
```bash
# Verify checksum and restore
python scripts/restore_db.py /var/backups/sohoj/sohoj_backup_<timestamp>.json.gz
```
The restoration script automatically:
1. Re-computes and matches the SHA-256 digest.
2. Recreates relational schemas.
3. Inserts tables in topological dependency order.
4. Performs an automated row-by-row count comparison to guarantee 100% data fidelity.

---

## 4. Secret & Credential Rotation Procedures

### Rotating JWT Secret Key (`SECRET_KEY`)
1. Generate a new cryptographically secure 256-bit key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
2. Update `SECRET_KEY` in production secrets manager (or Docker secret).
3. Gracefully restart `backend-api` container (`docker compose restart backend-api`).
4. Users with old tokens will receive HTTP 401 and automatically exchange their refresh token for a newly signed access token.

### Rotating PostgreSQL Credentials
1. Update database user password in PostgreSQL:
   ```sql
   ALTER USER financial_app WITH PASSWORD '<NEW_PASSWORD>';
   ```
2. Update `POSTGRES_PASSWORD` and `DATABASE_URL` in environment secrets.
3. Restart `backend-api` and `backend-worker`.

### Rotating Upstream LLM Provider API Key
1. Update `GEMINI_API_KEY` (or `OPENAI_API_KEY`) in environment config.
2. Restart `backend-api`. Test single-query completion via `curl -X POST ... /api/v1/chat`.

---

## 5. Drift Monitoring & Nightly Batch Maintenance

The drift monitoring and feature re-aggregation job runs nightly via `app.worker.drift_job`:
```bash
python -m app.worker.drift_job
```
- Compares trailing 30-day feature distributions against training baseline distributions.
- Emits Prometheus gauges `ml_drift_psi_score` and `ml_drift_ks_statistic`.
- Re-evaluates forecast accuracy (`ml_forecast_mape`) once real-world transaction actuals have settled for the month.
