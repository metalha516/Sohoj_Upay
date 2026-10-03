# Security Policy — Sohoj Financial Coach

Sohoj takes data protection and platform security seriously. Because our application handles personal financial transactions, balances, and AI-driven coaching insights, we adhere strictly to industry standards, OWASP ASVS Level 2, and Bangladesh Bank data privacy guidelines.

---

## Supported Versions

Only the latest active minor release receives critical security and dependency patches.

| Version | Supported | Status |
|---|---|---|
| `1.0.x` | ✅ Yes | Current Stable Release |
| `< 1.0.0` | ❌ No | Deprecated Synthetic Alpha/Beta |

---

## Reporting a Security Vulnerability

If you discover a security vulnerability in Sohoj, **please do NOT open a public GitHub issue**.

Instead, please report vulnerabilities privately through one of the following channels:

- **Security Team Email:** [security@sohoj.app](mailto:security@sohoj.app)
- **RFC 9116 Security Contact:** `/.well-known/security.txt`
- **PGP Encryption Key:** Available upon request or via keyserver for sensitive payloads.

### What to Include in Your Report
To help us triage and resolve the issue quickly, please provide:
1. Description of the vulnerability (e.g. Broken Object Level Authorization, SSRF, injection vector).
2. Step-by-step reproduction instructions or proof-of-concept (POC) request payload.
3. Affected components, endpoints, or dependency versions.
4. Assessment of real-world impact on user financial confidentiality or ledger integrity.

---

## Response & Disclosure Timeline

- **Initial Acknowledgment:** Within **24 hours** of receipt.
- **Triage & Severity Assessment:** Within **48 hours**.
- **Fix & Patch Deployment:**
  - **Critical / High:** Deployed within **7 calendar days**.
  - **Medium / Low:** Deployed within standard 30-day release cycle.
- **Coordinated Disclosure:** We adhere to a 90-day coordinated disclosure policy, allowing adequate remediation time before public details are released.

---

## Security Architecture Principles

1. **Defense in Depth:**
   - Multi-layer defense: Edge TLS reverse proxy, non-root containers, dropped Linux capabilities (`cap_drop: [ALL]`), and read-only container root filesystems.
2. **Row-Level Security (RLS):**
   - PostgreSQL RLS enforces hard isolation by tenant `user_id` even if an application SQL query omits a filter.
3. **Cryptographic Standards:**
   - Argon2id (`m=64MB, t=3, p=1`) for passwords.
   - Pinned JWT access tokens (15-minute lifetime) with SHA-256 hashed refresh tokens.
4. **AI Safety & Grounding:**
   - Deterministic numeric-grounding validator ensures zero hallucinated figures in coaching advice.
   - Read-only database tools with strict row caps (≤ 50) and per-turn query budgets (≤ 6).
   - Knowledge base isolation: user transaction data never enters RAG chunk embeddings.
5. **Operational Kill Switches:**
   - Instant administrative shutdown flags for AI features (`AI_ENABLED`), authentication (`LOGIN_ENABLED`, `REGISTRATION_ENABLED`), and forecasting (`FORECAST_ENABLED`).
