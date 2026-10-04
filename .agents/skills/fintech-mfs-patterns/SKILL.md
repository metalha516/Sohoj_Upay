---
name: fintech-mfs-patterns
description: >-
  Provides runbooks and UX guidelines for Bangladesh Mobile Financial Services (MFS) user interactions, including Upay, bKash, Nagad, and Rocket transaction flows. Use this skill when building or auditing financial transaction ledgers, cash-out purpose capture modals, tariff optimization calculators, 50/30/20 budget allocations, and deterministic compound wealth simulators.
---

# Fintech & MFS UX Interaction Patterns

This skill codifies financial logic, user experience flows, and mathematical algorithms specific to Bangladesh's Mobile Financial Services (MFS) landscape.

---

## 1. MFS Tariff Structure & Optimization

### Official Tariff Benchmarks (Bangladesh Bank PSD Aligned)

| Channel / Provider | Fee Structure | Effective Rate | Value Proposition |
| :--- | :--- | :--- | :--- |
| **Upay UCB ATM** | ৳8 per ৳1,000 | **0.80%** | Lowest cash-out cost in Bangladesh |
| **Upay Agent** | ৳14 per ৳1,000 | **1.40%** | Industry-leading agent withdrawal rate |
| **Upay App / POS** | ৳14 per ৳1,000 | **1.40%** | In-app QR code withdrawal |
| **Competitor Average** | ৳18.50 per ৳1,000 | **1.85%** | Standard bKash/Nagad agent tariff |

### Tariff Calculation Math
```typescript
export function calculateTariffSavings(amount: number, channel: 'agent' | 'atm' | 'app') {
  const competitorRate = 0.0185; // 1.85%
  const upayRate = channel === 'atm' ? 0.008 : 0.014; // 0.8% or 1.4%
  
  const competitorFee = amount * competitorRate;
  const upayFee = amount * upayRate;
  const savingsPerWithdrawal = Math.max(0, competitorFee - upayFee);
  
  // Assuming 4 cash-outs per month
  const annualSavings = savingsPerWithdrawal * 4 * 12;
  
  return {
    upayFee,
    competitorFee,
    savingsPerWithdrawal,
    annualSavings,
    effectiveRate: (upayRate * 100).toFixed(1) + '%',
  };
}
```

---

## 2. Mandatory Cash-Out Purpose Capture Flow

In Bangladesh, cash-out transactions obscure the actual spending category because the transaction ledger only shows an MFS agent cash withdrawal. 

### Best Practices:
1. **Never allow unclassified cash-outs**: Always present a purpose classification step.
2. **Four Core Purpose Categories**:
   - `necessity`: House rent, groceries, medicines, school fees, utilities.
   - `savings_goal`: Bank DPS, FDR deposit, emergency buffer contribution.
   - `discretionary`: Dining out, shopping, entertainment, travel.
   - `other`: Family remittance, loan repayment, emergency assistance.
3. **Optimistic UI Invalidation**: Immediately update net balance, outflow ratio bar, and anomaly scores upon submission.

---

## 3. Deterministic Compound Wealth Simulator

Never allow generative AI to guess compound numbers. All compound interest calculations must be mathematically exact.

### Exact Continuous & Monthly Formulas
```typescript
export function computeCompoundWealth(
  initialDeposit: number,
  monthlySaving: number,
  annualRatePercent: number,
  years: number
) {
  const monthlyRate = annualRatePercent / 100 / 12;
  const totalMonths = years * 12;
  const totalContributed = initialDeposit + monthlySaving * totalMonths;

  let futureValue = initialDeposit * Math.pow(1 + monthlyRate, totalMonths);
  if (monthlyRate > 0) {
    futureValue += monthlySaving * ((Math.pow(1 + monthlyRate, totalMonths) - 1) / monthlyRate);
  } else {
    futureValue += monthlySaving * totalMonths;
  }

  const interestEarned = Math.max(0, futureValue - totalContributed);
  // Rule of 72 doubling estimate
  const doublingYears = annualRatePercent > 0 ? (72 / annualRatePercent).toFixed(1) : 'N/A';

  return {
    futureValue,
    totalContributed,
    interestEarned,
    doublingYears,
  };
}
```

---

## 4. Privacy & Data Minimization (Zero PII)
- **Zero Raw SMS Ingestion**: Never store SMS bodies, SIM carrier tokens, or OTP codes.
- **HMAC-SHA256 Pseudonymization**: All account identifiers and phone numbers must be hashed before storage or machine learning ingestion.
