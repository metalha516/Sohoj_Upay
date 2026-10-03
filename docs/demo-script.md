# Sohoj Financial Coach — End-to-End Demo & Presentation Script

This script provides an executive, step-by-step presentation walkthrough showcasing Sohoj's core features, intelligent ML pipeline, and safe conversational AI coach.

---

## Preparation & Prerequisites
1. Ensure the stack is running:
   ```bash
   # Backend
   cd backend && python -m uvicorn app.main:app --port 8000
   # Frontend
   cd frontend && npm run dev
   ```
2. Navigate to: `http://localhost:3000`

---

## Step 1: Account Creation & Explicit Consent Gate
- **Action:**
  1. Open `/register`.
  2. Register a new user (e.g. `Anik Rahman`, `anik@example.com`, `Password123456!`).
  3. Observe the **Data Processing & AI Consent Gate** checkbox.
- **Narrative Points to Highlight:**
  - Strict compliance with Bangladesh Bank National Financial Inclusion Strategy (NFIS) and ICT Act.
  - Explicit user opt-in required before financial data is fed into automated classification or AI personalization.
  - Immediate generation of 15-minute access token and secure HttpOnly refresh cookie.

---

## Step 2: The Core Product Loop — Recording a Cash-Out
- **Action:**
  1. Navigate to `/transactions`.
  2. Click **Record Transaction** → Select **Cash Out (MFS / ATM)**.
  3. Enter Amount: `৳4,500.00`, Merchant: `Shwapno Superstore`.
  4. Notice the **Mandatory Purpose Flow** (`CashOutPurposeModal`): Select `Necessity` → Subcategory: `Groceries`.
  5. Click Submit.
- **Narrative Points to Highlight:**
  - In Bangladesh, unclassified MFS cash-outs cause financial blindness. Sohoj enforces structured categorization at the moment of recording.
  - The API performs transactional outbox persistence: the transaction and outbox event are saved in a single database transaction.

---

## Step 3: Real-Time Dashboard & Financial Metrics
- **Action:**
  1. Click on `/dashboard`.
  2. Observe updated balance, monthly outflow, necessity vs discretionary split, and savings rate.
- **Narrative Points to Highlight:**
  - Aggregations read directly from pre-computed `monthly_features` tables.
  - Sub-50ms response times guaranteed under high concurrency.
  - Formatted using standard Bengali currency notation (`৳` and `Intl.NumberFormat('en-BD')`).

---

## Step 4: Machine Learning — Persona & Anomaly Detection
- **Action:**
  1. Navigate to `/behavior`.
  2. Review the **Behavioral Persona Card** (e.g., *Disciplined Saver* with confidence rating and top factor attribution bars).
  3. Observe the **Anomalous Outflow Card**: An alert appears for a high-value spike with an explainability note.
  4. Point out the festival guard logic: holiday spending during Eid or Puja automatically adapts alert thresholds to eliminate false alarms.
  5. Click **Confirm** or **Dismiss** on the anomaly card to trigger the real-time feedback loop.

---

## Step 5: Goal Planning & Wealth Simulator
- **Action:**
  1. Navigate to `/goals`.
  2. Create a goal: `Emergency Reserve` — Target: `৳100,000`, Target Date: `December 2027`.
  3. Navigate to `/simulator`.
  4. Adjust monthly savings slider (`৳5,000`) and expected annual return (`8.0%`).
- **Narrative Points to Highlight:**
  - Calculation calls the server-side Financial Engine (`/api/v1/simulate/growth`) — no duplicated financial math in JavaScript.
  - Mandatory **"Assumed Rate: 8.0%"** badge and **"Projections are estimates and not guaranteed"** disclaimer are always visible.

---

## Step 6: Conversational AI Financial Coach
- **Action:**
  1. Navigate to `/coach`.
  2. If first visit, observe the AI Coach Consent Gate.
  3. Submit the inquiry:
     > *"Can I afford to buy a pair of headphones for ৳5,000 this month?"*
  4. Watch Server-Sent Events (SSE) stream the response in real time.
  5. Notice the **Tool Status Chips** (`Checking affordability...`, `Reading monthly features...`).
  6. Inspect the Coach's answer:
     - Exact BDT amounts cited in the answer match the user's actual ledger surplus.
     - Includes deep-link action button: `[View Goals]`.
     - Displays prompt version and feedback buttons (Helpful / Not Helpful).
- **Narrative Points to Highlight:**
  - **Zero Numeric Hallucination:** The deterministic numeric-grounding validator ensures every number cited in the message is strictly grounded in tool output.
  - **Tenant Boundary:** The agent cannot query other users' ledgers; tenant ID is injected strictly from the verified JWT.
