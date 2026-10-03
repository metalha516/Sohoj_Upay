# Few-Shot: Growth Simulation

**User:** "If I invest ৳5,000 monthly at 8% annual return for 5 years, how much will I have?"
**Assistant Tool Call:** `calculate_future_value(principal=0.0, monthly_contribution=5000.0, annual_rate_percent=8.0, years=5.0, compounding_per_year=12, rate_type="assumed")`
**Tool Result:**
```json
{
  "future_value": 367384.28,
  "total_contributed": 300000.0,
  "total_growth": 67384.28,
  "assumptions": {
    "rate_type": "assumed",
    "annual_rate": 0.08,
    "compounding_per_year": 12
  },
  "disclaimer_code": "PROJECTION_NOT_GUARANTEED"
}
```
**Assistant Response:**
"If you contribute ৳5,000 monthly for 5 years at an assumed 8.0% annual interest rate compounded monthly, your estimated future value will be **৳367,384.28**.

- **Total principal contributed:** ৳300,000.00
- **Total compound growth:** ৳67,384.28
- **Estimated final balance:** ৳367,384.28

*Note: This calculation is based on an assumed annual interest rate of 8.0% compounded monthly. Projections are illustrative and not guaranteed.*"
