# Few-Shot: Affordability Evaluation

**User:** "Can I afford to buy a ৳25,000 smartphone this month?"
**Assistant Tool Call:** `check_affordability(item_cost=25000.0, category="shopping", is_recurring=false)`
**Tool Result:**
```json
{
  "item_cost": 25000.0,
  "current_month_surplus": 32000.0,
  "trailing_3m_avg_surplus": 28000.0,
  "remaining_buffer": 7000.0,
  "verdict": "stretch",
  "rationale": "Purchase absorbs 78% of this month's unallocated surplus, leaving a tight ৳7,000 cushion."
}
```
**Assistant Response:**
"Based on your current month's cash flow, purchasing a ৳25,000 smartphone is possible, but it represents a **stretch** on your budget.

- **Current monthly surplus:** ৳32,000
- **Cost of smartphone:** ৳25,000
- **Remaining buffer after purchase:** ৳7,000

While you have sufficient funds to cover the purchase without going negative, it will absorb 78% of your available surplus for the month, leaving you with a modest ৳7,000 buffer for unexpected expenses. If possible, consider splitting the cost across two months or waiting until your next salary cycle to preserve a healthier emergency cushion."
