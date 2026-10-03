---
title: "How Your Data is Protected and How AI Consent Works"
topic: "app_faq"
language: "en"
version: "1.0"
---

# Data Privacy and AI Consent in Sohoj

Sohoj is built with strict privacy controls to keep your personal financial information secure and isolated.

## Row-Level Security and Tenant Isolation
- Your transactions, account balances, and savings goals are protected by database-level Row-Level Security (RLS).
- No other user can view, query, or access your financial records.

## Explicit AI Consent Policy
- Generating AI-driven insights or conversing with the financial assistant requires your explicit opt-in consent (`consent_ai`).
- When enabled, only aggregated figures and relevant context are shared with the assistant.
- Sensitive identifiers like your name, email, and phone number are never included in analytical payloads.
- You can revoke AI consent at any time in your profile settings.
