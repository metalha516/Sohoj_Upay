# Few-Shot: Goal Planning

**User:** "How much do I need to save each month to reach ৳120,000 in 12 months?"
**Assistant Tool Call:** `calculate_goal_plan(target_amount=120000.0, current_savings=0.0, time_horizon_months=12, annual_rate_percent=0.0)`
**Tool Result:**
```json
{
  "target_amount": 120000.0,
  "current_savings": 0.0,
  "required_monthly_saving": 10000.0,
  "time_horizon_months": 12,
  "historical_3m_savings": 14500.0,
  "feasibility": "on_track",
  "eta_months": 12
}
```
**Assistant Response:**
"To reach your goal of ৳120,000 in 12 months, you need to save **৳10,000 per month**.

- **Target Amount:** ৳120,000
- **Time Horizon:** 12 months
- **Required Monthly Saving:** ৳10,000
- **Your 3-Month Average Savings:** ৳14,500

Your historical savings pace indicates this goal is well within reach! You are currently saving an average of ৳14,500 monthly, which exceeds the required ৳10,000 threshold."
