# Sohoj Technical Stack & Architecture Constraints

When generating code, designing APIs, or building UI components for Sohoj, you **MUST** strictly adhere to the following architecture and stack decisions.

---

## 1. Frontend Architecture
* **Framework:** Next.js 14.2+ (App Router, TypeScript, React 18/19)
* **Styling Engine:** Tailwind CSS with custom navy & Upay yellow extensions
* **Component Primitives:** shadcn/ui (Radix UI primitives)
* **Icons:** Lucide React (`lucide-react`)
* **Data Visualizations:** Recharts with responsive containers and tailored SVG tooltips
* **Data Fetching & State:** TanStack React Query + React Hook Form + Zod

## 2. Backend & ML Architecture
* **API Framework:** FastAPI (Python 3.12+, async endpoints)
* **Database & ORM:** SQLite for local demo (`sohoj_demo.db`), PostgreSQL / SQLModel for production
* **Machine Learning Suite:**
  - LightGBM (Persona / Archetype Classification)
  - Isolation Forest (Festival-aware Anomaly Detection)
  - Rolling-origin regression forecaster (Expenses projection)
  - SHAP (Explainable AI features)
* **LLM & Grounding:** Google Gemini Flash (`gemini-flash-latest`) via SSE streaming with strict numeric grounding verification (zero hallucination tolerance)

## 3. Implementation Rules
* **MFS Standards:** Always format transactions with proper MFS brand identifiers (Upay, bKash, Nagad, Rocket) and mandatory Cash-Out purpose classification.
* **Currency Formatting:** Display currency with the Bengali Taka symbol `৳` and comma-separated thousands (e.g. `৳35,166.11`).
* **Clean Code:** No raw inline CSS, no Bootstrap, no jQuery. Keep styles collocated with components via Tailwind.
