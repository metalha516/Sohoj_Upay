# Few-Shot: General Knowledge & RAG Retrieval

**User:** "What is the 50/30/20 rule and how does it work?"
**Assistant Tool Call:** `search_knowledge(query="50/30/20 budgeting rule explained", top_k=2)`
**Tool Result:**
```json
[
  {
    "title": "50/30/20 Budgeting Rule Explained",
    "topic": "budgeting",
    "content": "The 50/30/20 rule divides after-tax income into: 50% for Needs (housing, groceries, utilities, commute), 30% for Wants (dining out, entertainment, shopping), and 20% for Savings and Future Security (emergency funds, deposits, debt paydown)."
  }
]
```
**Assistant Response:**
"The **50/30/20 rule** is a widely recognized personal budgeting framework that divides your monthly after-tax income into three functional categories:

1. **50% for Needs:** Essential non-negotiable expenses required for basic living, such as rent, utility bills, groceries, and daily commute costs.
2. **30% for Wants:** Discretionary lifestyle spending that enhances quality of life, such as dining out, hobbies, shopping, and entertainment.
3. **20% for Savings & Debt Reduction:** Dedicated to building financial security, including emergency fund contributions, deposit pension schemes (DPS), and accelerated debt paydown.

If you live in a high-cost urban area, you can adapt the proportions (such as 60/20/20) until your monthly income expands."
