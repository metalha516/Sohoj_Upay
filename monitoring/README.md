# Monitoring & Observability

Prometheus metrics collection and Grafana visualization dashboards.

## Principles
- Only the reverse proxy is exposed externally; Prometheus and Grafana operate on internal networks or behind VPN/authentication.
- Dashboards track system latencies, error rates, financial transaction throughput, and security alert events (e.g. failed logins, refresh token anomalies).
- Provisioning directory holds automated Grafana datasources and dashboard definitions.
