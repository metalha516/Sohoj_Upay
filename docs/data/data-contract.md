# Domain Definitions, Data Contract & Persona Specification

**Document Version:** 1.0.0  
**Status:** Approved Specification  
**Applies to:** Backend Financial Engine, Schema DDL, ML Feature Pipeline, Synthetic Generator, Conversational Coach  
**Timezone Reference:** `Asia/Dhaka` (UTC+6)  
**Currency Standard:** BDT (৳), precision `NUMERIC(14,2)`  

---

## 1. Core Financial Metric Definitions

This section resolves all ambiguities from `design.md` §4.3. Every formula is pure, deterministic, and implemented with `Decimal` arithmetic.

### 1.1 Temporal Standard & Month Boundaries
All monthly aggregations, trends, and statement reporting operate under the **`Asia/Dhaka`** timezone (UTC+6, without Daylight Saving Time adjustments).
- **Month Start:** `YYYY-MM-01 00:00:00.000000+06:00`
- **Month End:** `YYYY-MM-LastDay 23:59:59.999999+06:00`
- **Late-Arriving Transactions:** Any transaction timestamped within the Dhaka calendar month belongs strictly to that calendar month's feature window, regardless of system ingestion lag.

---

### 1.2 Mathematical Formulations

#### 1. Inflow & Income
- **Inbound Transactions ($\text{Inflows}$):** Any credit to the user's MFS wallet (Salary, Remittance, Business Revenue, P2P Received, Self Cash-In).
- **Monthly Income ($\text{Income}_M$):**
  $$\text{Income}_M = \sum_{t \in M, \text{is\_income}(t) = \text{true}} \text{amount}(t)$$
  *Crucial Rule:* A user depositing physical paper cash into their own wallet at an MFS agent (`category = cash_in_self`) is an **asset conversion** (physical cash $\to$ electronic money), **NOT** new income. `cash_in_self` increases wallet balance but is strictly excluded from `Income_M`.

#### 2. Expense ($\text{Expense}_M$)
Outflows consumed for living, lifestyle, services, or obligations:
$$\text{Expense}_M = \sum_{t \in M, \text{is\_expense}(t) = \text{true}} (\text{amount}(t) + \text{fee}(t))$$
Where a transaction $t$ is an expense if:
- It is a direct digital outflow (Merchant Payment, Utility Pay Bill, Mobile Recharge, P2P Send Money for family/living support) OR
- It is an MFS Agent `cash_out` where `purpose` $\in \{\text{necessity}, \text{discretionary}, \text{other}\}$ OR
- It is an MFS transaction fee (`category = mfs_fee`).
*Exception:* A `cash_out` with `purpose = savings_goal` is **NOT** an expense; it is classified as `Savings`.

#### 3. Savings ($\text{Savings}_M$)
Intentional allocation toward future financial security or contracted goals:
$$\text{Savings}_M = \sum_{t \in M, \text{purpose}(t) = \text{savings\_goal}} \text{amount}(t)$$
Includes:
- MFS in-app DPS installments (e.g. IDLC, Dhaka Bank, MTB monthly schemes).
- Emergency fund allocations or transfers to designated external savings accounts.
- `cash_out` operations where the user explicitly tags `purpose = savings_goal` (e.g., cash withdrawn to deposit into an offline NGO Samity or physical bank savings counter).
*Non-Negotiable Rule:* Unspent money remaining in the wallet at month's end is **NEVER** automatically credited as savings.

#### 4. Unallocated Surplus ($\text{Surplus}_M$)
The net cash flow margin remaining after expenses and explicit savings:
$$\text{Surplus}_M = \text{Income}_M - \text{Expense}_M - \text{Savings}_M$$
- **Positive Surplus:** Unallocated idle liquidity in the wallet available for emergency reserves or new goals.
- **Negative Surplus (Deficit):** The user overspent their current month's income, drawing down prior accumulated wallet balances or external cash-ins.

#### 5. Savings Rate ($\text{SR}_M$)
The proportion of earned income dedicated to explicit savings:
$$\text{SR}_M = \begin{cases} 
\left(\frac{\text{Savings}_M}{\text{Income}_M}\right) \times 100 & \text{if } \text{Income}_M > 0 \\
\text{null} & \text{if } \text{Income}_M \le 0 
\end{cases}$$
Rounded to 2 decimal places using `ROUND_HALF_UP`. If $\text{Income}_M = 0$, the UI displays `--` with indicator `NO_INCOME`.

#### 6. Running Balance ($\text{Balance}_T$)
The deterministic wallet balance at point in time $T$:
$$\text{Balance}_T = \text{Balance}_0 + \sum_{t \le T} \text{Inflow}(t) - \sum_{t \le T} \text{Outflow}(t) - \sum_{t \le T} \text{Fee}(t)$$
Reconciled asynchronously against ledger entries; must never drop below ৳0.00.

#### 7. Treatment of Transfers & MFS Fees
| Transaction Type | Context / Sub-category | Classified As | Impact on Income | Impact on Expense | Impact on Savings | Impact on Balance |
|---|---|---|---|---|---|---|
| **P2P Send Money** | Family Support / Village | Outflow | No | Yes (+ fee) | No | Decreases |
| **P2P Send Money** | Own Bank / DPS Deposit | Outflow | No | No | Yes | Decreases |
| **P2P Received** | Salary / Freelance / Gift | Inflow | Yes | No | No | Increases |
| **P2P Received** | Internal Self-Transfer | Inflow | No | No | No | Increases |
| **Cash-In** | Agent deposit to own wallet | Inflow | No | No | No | Increases |
| **Cash-Out** | House rent / offline bazaar | Outflow | No | Yes (+ fee) | No | Decreases |
| **Cash-Out** | Physical DPS / Samity deposit | Outflow | No | No (+ fee only) | Yes | Decreases |
| **Cash-Out Fee** | Official Tariff (1.49%-1.85%) | Outflow | No | Yes | No | Decreases |

---

### 1.3 Worked Numeric Examples

#### Example 1: Salaried Corporate Executive (Disciplined Saver)
- **Starting Balance (2026-04-01):** ৳12,000.00
- **Transactions in April 2026:**
  1. `2026-04-01 10:00`: Inflow Salary = ৳65,000.00 (Fee = ৳0.00)
  2. `2026-04-02 11:30`: Outflow DPS Installment (`purpose = savings_goal`) = ৳10,000.00 (Fee = ৳0.00)
  3. `2026-04-03 14:00`: Outflow Emergency Reserve (`purpose = savings_goal`) = ৳5,000.00 (Fee = ৳0.00)
  4. `2026-04-05 18:00`: Outflow House Rent (`purpose = necessity`, `cash_out`) = ৳20,000.00 (Fee 1.85% = ৳370.00)
  5. `2026-04-10 12:00`: Outflow Electricity + Internet (`purpose = necessity`, Pay Bill) = ৳3,200.00 (Fee = ৳0.00)
  6. `2026-04-15 16:30`: Outflow Superstore Groceries (`purpose = necessity`, Merchant Pay) = ৳8,500.00 (Fee = ৳0.00)
  7. `2026-04-22 20:00`: Outflow Restaurant Dining (`purpose = discretionary`, Merchant Pay) = ৳3,400.00 (Fee = ৳0.00)
  8. `2026-04-28 15:00`: Outflow Mobile Recharge (`purpose = necessity`) = ৳500.00 (Fee = ৳0.00)
- **Derived Metrics:**
  - $\text{Income} = ৳65,000.00$
  - $\text{Expense} = ৳20,000 + ৳370 + ৳3,200 + ৳8,500 + ৳3,400 + ৳500 = ৳35,970.00$
  - $\text{Savings} = ৳10,000 + ৳5,000 = ৳15,000.00$
  - $\text{Savings Rate} = \frac{15,000}{65,000} \times 100 = \mathbf{23.08\%}$
  - $\text{Unallocated Surplus} = 65,000 - 35,970 - 15,000 = \mathbf{+৳14,030.00}$
  - $\text{Ending Balance} = 12,000 + 65,000 - (35,970 + 15,000) = \mathbf{৳26,030.00}$

---

#### Example 2: Garment Worker (Tight Budget with Offline Cash-Out)
- **Starting Balance (2026-04-01):** ৳450.00
- **Transactions in April 2026:**
  1. `2026-04-07 09:30`: Inflow Factory Salary = ৳16,500.00 (Fee = ৳0.00)
  2. `2026-04-07 17:00`: Cash-Out for Rent & Bazaar (`purpose = necessity`, Priyo agent 1.49%) = ৳12,000.00 (Fee = ৳178.80)
  3. `2026-04-08 11:00`: P2P Send Money to Parents in Village (`purpose = necessity`) = ৳3,000.00 (Fee = ৳5.00)
  4. `2026-04-12 18:30`: Mobile Recharge (`purpose = necessity`) = ৳200.00 (Fee = ৳0.00)
  5. `2026-04-18 20:00`: Medical / Pharmacy Purchase (`purpose = necessity`) = ৳650.00 (Fee = ৳0.00)
  6. `2026-04-25 14:00`: Cash-Out for Offline Samity Savings (`purpose = savings_goal`) = ৳500.00 (Fee 1.49% = ৳7.45)
- **Derived Metrics:**
  - $\text{Income} = ৳16,500.00$
  - $\text{Expense} = ৳12,000 + ৳178.80 + ৳3,000 + ৳5.00 + ৳200 + ৳650 + ৳7.45\text{ (savings cash-out fee)} = ৳16,041.25$
  - $\text{Savings} = ৳500.00$
  - $\text{Savings Rate} = \frac{500}{16,500} \times 100 = \mathbf{3.03\%}$
  - $\text{Unallocated Surplus} = 16,500 - 16,041.25 - 500 = \mathbf{-৳41.25}$ (Deficit covered by opening balance)
  - $\text{Ending Balance} = 450 + 16,500 - 16,041.25 - 500 = \mathbf{৳408.75}$

---

#### Example 3: Tech Freelancer (Volatile Earner with Lumpy Inflows)
- **Starting Balance (2026-04-01):** ৳34,000.00
- **Transactions in April 2026:**
  1. `2026-04-04 15:00`: Inflow Client Payment Milestone 1 = ৳42,000.00
  2. `2026-04-10 12:00`: Outflow Coworking & Internet (`purpose = necessity`) = ৳6,500.00
  3. `2026-04-14 18:00`: Outflow Electronics Shopping (`purpose = discretionary`) = ৳14,500.00
  4. `2026-04-20 02:30`: Inflow Client Payment Milestone 2 = ৳38,000.00
  5. `2026-04-21 11:00`: Outflow Bank DPS Deposit (`purpose = savings_goal`) = ৳20,000.00
  6. `2026-04-25 19:30`: Outflow Food Delivery & Hangouts (`purpose = discretionary`) = ৳5,800.00
  7. `2026-04-28 16:00`: Cash-Out for Family Expenses (`purpose = necessity`) = ৳15,000.00 (Fee 1.85% = ৳277.50)
- **Derived Metrics:**
  - $\text{Income} = ৳42,000 + ৳38,000 = ৳80,000.00$
  - $\text{Expense} = ৳6,500 + ৳14,500 + ৳5,800 + ৳15,000 + ৳277.50 = ৳42,077.50$
  - $\text{Savings} = ৳20,000.00$
  - $\text{Savings Rate} = \frac{20,000}{80,000} \times 100 = \mathbf{25.00\%}$
  - $\text{Unallocated Surplus} = 80,000 - 42,077.50 - 20,000 = \mathbf{+৳17,922.50}$
  - $\text{Ending Balance} = 34,000 + 80,000 - 42,077.50 - 20,000 = \mathbf{৳51,922.50}$

---

#### Example 4: Student (Family Allowance with Zero Direct Earnings)
- **Starting Balance (2026-04-01):** ৳1,200.00
- **Transactions in April 2026:**
  1. `2026-04-02 10:00`: Inflow Allowance from Parents (`family_support_received`) = ৳9,000.00 (Counted as Inbound Income)
  2. `2026-04-05 14:00`: Outflow University Mess Rent (`purpose = necessity`) = ৳4,000.00
  3. `2026-04-09 17:00`: Outflow Mobile Data Recharge (`purpose = necessity`) = ৳350.00
  4. `2026-04-15 19:00`: Outflow Fast Food & Hangouts (`purpose = discretionary`) = ৳2,200.00
  5. `2026-04-20 16:00`: Outflow Books & Photocopy (`purpose = necessity`) = ৳800.00
  6. `2026-04-26 12:00`: Inflow Wallet Load at Agent (`cash_in_self`) = ৳2,000.00 (Asset conversion, **NOT** income)
  7. `2026-04-27 21:00`: Outflow Movie & Snacks (`purpose = discretionary`) = ৳1,100.00
- **Derived Metrics:**
  - $\text{Income} = ৳9,000.00$ (`cash_in_self` of ৳2,000 is excluded)
  - $\text{Expense} = ৳4,000 + ৳350 + ৳2,200 + ৳800 + ৳1,100 = ৳8,450.00$
  - $\text{Savings} = ৳0.00$
  - $\text{Savings Rate} = \frac{0}{9,000} \times 100 = \mathbf{0.00\%}$
  - $\text{Unallocated Surplus} = 9,000 - 8,450 - 0 = \mathbf{+৳550.00}$
  - $\text{Ending Balance} = 1,200 + (9,000 + 2,000) - 8,450 = \mathbf{৳3,750.00}$

---

#### Example 5: Cash-Dominant Micro-Merchant
- **Starting Balance (2026-04-01):** ৳2,500.00
- **Transactions in April 2026:**
  1. `2026-04-01 → 2026-04-30`: Aggregate Inflow Customer QR Merchant Payments = ৳45,000.00
  2. `2026-04-01 → 2026-04-30`: 12 Agent Cash-Outs to buy physical wholesale inventory (`purpose = necessity`) = ৳38,000.00 (Fees @ 1.49% = ৳566.20)
  3. `2026-04-10 11:00`: Electricity Bill Payment (`purpose = necessity`) = ৳1,800.00
  4. `2026-04-20 15:00`: Mobile Airtime (`purpose = necessity`) = ৳400.00
  5. `2026-04-25 18:00`: Microfinance Loan Installment (`purpose = necessity`) = ৳3,000.00
- **Derived Metrics:**
  - $\text{Income} = ৳45,000.00$
  - $\text{Expense} = ৳38,000 + ৳566.20 + ৳1,800 + ৳400 + ৳3,000 = ৳43,766.20$
  - $\text{Savings} = ৳0.00$
  - $\text{Savings Rate} = \mathbf{0.00\%}$
  - $\text{Unallocated Surplus} = 45,000 - 43,766.20 = \mathbf{+৳1,233.80}$
  - $\text{Ending Balance} = 2,500 + 45,000 - 43,766.20 = \mathbf{৳3,733.80}$

---

## 2. Transaction Taxonomy & Purpose Mapping

The system enforces a 2-level hierarchy: 4 **Purposes** at the root, partitioned into 25 **Categories**.

```
Purposes
├── necessity (Essential living, healthcare, shelter, loan installments, fees)
├── savings_goal (Explicit DPS, emergency reserve, contracted goal deposits)
├── discretionary (Lifestyle retail, dining, recreation, non-essential travel)
└── other (Wallet loads, uncategorized peer transfers, donations)
```

### Complete Category Tree & Operational Parameters

| Category Code | Display Name | Bangla Name | Flow | Default Purpose | Is Income? | Typical BDT Range | Frequency |
|---|---|---|---|---|---|---|---|
| `salary` | Salary | বেতন | Inflow | other | Yes | 10,000 – 150,000 | Monthly |
| `freelance_income` | Freelance & Gig Earnings | ফ্রিল্যান্সিং আয় | Inflow | other | Yes | 5,000 – 80,000 | Sporadic |
| `remittance_received` | Foreign/Domestic Remittance | রেমিট্যান্স প্রাপ্তি | Inflow | other | Yes | 15,000 – 60,000 | Monthly |
| `business_revenue` | Merchant / Shop Revenue | ব্যবসা আয় | Inflow | other | Yes | 500 – 25,000 | Daily |
| `family_support_received` | Family Support Received | সহায়তা গ্রহণ | Inflow | other | Yes | 2,000 – 15,000 | Monthly |
| `cash_in_self` | Self Cash-In (Wallet Load) | ক্যাশ-ইন | Inflow | other | **No** | 500 – 20,000 | Sporadic |
| `groceries` | Groceries & Raw Bazaar | কাঁচাবাজার ও মুদি | Outflow | necessity | No | 200 – 5,000 | Weekly |
| `rent` | House & Mess Rent | বাড়ি ভাড়া | Outflow | necessity | No | 3,000 – 35,000 | Monthly |
| `utilities` | Utilities (Power/Gas/Water/ISP)| ইউটিলিটি বিল | Outflow | necessity | No | 300 – 4,500 | Monthly |
| `mobile_recharge` | Mobile Airtime & Data | মোবাইল রিচার্জ | Outflow | necessity | No | 20 – 500 | Weekly |
| `transport` | Commute & Rides | যাতায়াত খরচ | Outflow | necessity | No | 30 – 800 | Daily |
| `education_fees` | Tuition & Educational Fees | শিক্ষা ও টিউশন ফি | Outflow | necessity | No | 500 – 15,000 | Monthly |
| `medical` | Healthcare & Medicine | চিকিৎসা ও ঔষধ | Outflow | necessity | No | 100 – 6,000 | Sporadic |
| `family_support_send` | Send Money to Family | পরিবারকে সহায়তা | Outflow | necessity | No | 1,000 – 20,000 | Monthly |
| `loan_repayment` | Microfinance/Loan Installment | ঋণের কিস্তি | Outflow | necessity | No | 500 – 8,000 | Weekly |
| `mfs_fee` | MFS Tariffs & Convenience Fees | এমএফএস চার্জ | Outflow | necessity | No | 5 – 500 | Per Txn |
| `shopping` | Apparel & Lifestyle Retail | কেনাকাটা | Outflow | discretionary | No | 300 – 8,000 | Sporadic |
| `dining` | Dining Out & Food Delivery | রেস্তোরাঁ ও খাবার | Outflow | discretionary | No | 100 – 2,500 | Weekly |
| `entertainment` | Recreation & Subscriptions | বিনোদন | Outflow | discretionary | No | 150 – 2,000 | Monthly |
| `travel` | Leisure Travel & Holidays | ভ্রমণ ও অবকাশ | Outflow | discretionary | No | 1,000 – 15,000 | Sporadic |
| `festival_eid` | Eid & Holiday Festivities | ঈদ ও উৎসব খরচ | Outflow | discretionary | No | 1,000 – 25,000 | Seasonal |
| `donation_zakat` | Charity & Zakat | দান ও যাকাত | Outflow | other | No | 100 – 10,000 | Sporadic |
| `dps_savings_deposit` | MFS / Bank DPS Installment | ডিপিএস সঞ্চয় | Outflow | savings_goal | No | 500 – 10,000 | Monthly |
| `emergency_fund_deposit`| Emergency Reserve Allocation | জরুরি তহবিল | Outflow | savings_goal | No | 500 – 10,000 | Monthly |
| `other_expense` | Miscellaneous Outflow | অন্যান্য খরচ | Outflow | other | No | 50 – 3,000 | Sporadic |

---

## 3. Behavioral Persona Specifications

Target population distribution across $N \ge 600$ users:
- **6 Fixed Archetypes:** $15.0\%$ each ($= 90.0\%$)
- **1 Mixed / Drifting Group:** $10.0\%$ ($= 100.0\%$)

```
Population Distribution
├── Consistent Saver           (15%)
├── Balanced Spender           (15%)
├── Tight Budgeter             (15%)
├── Discretionary Spender      (15%)
├── Volatile Earner            (15%)
├── Cash-Dominant Transactor   (15%)
└── Mixed / Drifting           (10%)
```

### Detailed Persona Parameters

| Persona Code | Name | Target Share | Monthly Income Band (BDT) | Income Regularity | Savings Rate (Mean ± SD) | Spend Mix (Nec / Disc / Sav / Oth) | Cash-out Freq & Volume | Expense Variance | Active Goals & Adherence |
|---|---|---|---|---|---|---|---|---|---|
| `consistent_saver` | Consistent Saver | 15% | 25k – 120k (Median: 45k) | Regular Monthly | 28% ± 6% | 60% / 10% / 28% / 2% | 2.5/mo (25% vol) | Low | 2.2 goals (90% adh) |
| `balanced_spender` | Balanced Spender | 15% | 20k – 90k (Median: 38k) | Regular Monthly | 15% ± 4% | 65% / 18% / 15% / 2% | 4.0/mo (40% vol) | Moderate | 1.5 goals (75% adh) |
| `tight_budgeter` | Tight Budgeter | 15% | 10k – 28k (Median: 18k) | Regular Monthly | 3% ± 2% | 88% / 7% / 3% / 2% | 6.0/mo (65% vol) | Low | 0.5 goals (40% adh) |
| `discretionary_spender` | Discretionary Spender | 15% | 28k – 130k (Median: 50k) | Regular Monthly | 6% ± 4% | 54% / 38% / 6% / 2% | 5.0/mo (45% vol) | High | 1.0 goals (45% adh) |
| `volatile_earner` | Volatile Earner | 15% | 12k – 110k (Median: 36k) | Lumpy Milestone | 16% ± 12% | 64% / 18% / 16% / 2% | 7.0/mo (60% vol) | Extreme | 1.2 goals (55% adh) |
| `cash_dominant_transactor`| Cash-Dominant Transactor | 15% | 12k – 50k (Median: 24k) | Regular Monthly | 7% ± 5% | 78% / 13% / 7% / 2% | 10.0/mo (82% vol) | Moderate | 0.6 goals (50% adh) |
| `mixed_drifting` | Mixed / Drifting | 10% | 18k – 85k (Median: 35k) | Bi-Weekly | 12% ± 9% | 68% / 18% / 12% / 2% | 5.5/mo (55% vol) | High | 1.1 goals (60% adh) |

---

## 4. Occupation & Segment Model

To reflect real Bangladeshi socioeconomic reality, users are generated through 8 occupational segments, mapping into behavioral personas via a **many-to-many probabilistic matrix**.

### 4.1 Income Percentiles by Segment (BDT)

| Occupation Code | Segment Name | Bangla Title | Min | P10 | P25 | Median | P75 | P90 | Max |
|---|---|---|---|---|---|---|---|---|---|
| `garment_worker` | RMG Garment Worker | পোশাক শ্রমিক | 12,500 | 13,500 | 15,000 | 18,500 | 23,000 | 27,000 | 32,000 |
| `student` | Tertiary Student | শিক্ষার্থী | 4,000 | 6,000 | 8,500 | 12,500 | 18,000 | 22,000 | 28,000 |
| `private_sector_employee` | Private Corporate / SME | বেসরকারি চাকুরিজীবী | 22,000 | 28,000 | 36,000 | 52,000 | 78,000 | 105,000 | 150,000 |
| `government_employee` | Public Sector Civil Servant | সরকারি চাকুরিজীবী | 20,000 | 25,000 | 32,000 | 46,000 | 68,000 | 88,000 | 125,000 |
| `freelancer_gig_worker` | Digital Freelancer | ডিজিটাল ফ্রিল্যান্সার | 15,000 | 22,000 | 32,000 | 55,000 | 85,000 | 120,000 | 175,000 |
| `small_shopkeeper_merchant`| Retail Micro-Merchant | ক্ষুদ্র ব্যবসায়ী | 14,000 | 18,000 | 24,000 | 34,000 | 48,000 | 65,000 | 95,000 |
| `ride_share_driver` | Rider / Auto Driver | রাইডার ও চালক | 15,000 | 18,000 | 23,000 | 31,000 | 42,000 | 52,000 | 65,000 |
| `homemaker_remittance_recipient`| Remittance Household Head| রেমিট্যান্স গৃহস্থালী | 16,000 | 20,000 | 27,000 | 38,000 | 54,000 | 72,000 | 95,000 |

### 4.2 Occupation $\to$ Persona Transition Matrix

| Occupation | `consistent_saver` | `balanced_spender` | `tight_budgeter` | `discretionary_spender` | `volatile_earner` | `cash_dominant` | `mixed_drifting` | Sum |
|---|---|---|---|---|---|---|---|---|
| RMG Garment Worker | 10% | 0% | 50% | 0% | 0% | 35% | 5% | **100%** |
| Student | 10% | 15% | 35% | 30% | 0% | 0% | 10% | **100%** |
| Private Corporate | 30% | 35% | 0% | 20% | 0% | 5% | 10% | **100%** |
| Government Employee | 45% | 35% | 10% | 0% | 0% | 0% | 10% | **100%** |
| Digital Freelancer | 15% | 0% | 0% | 20% | 55% | 0% | 10% | **100%** |
| Retail Micro-Merchant | 10% | 25% | 20% | 0% | 0% | 40% | 5% | **100%** |
| Ride-Sharing Driver | 0% | 0% | 15% | 0% | 40% | 35% | 10% | **100%** |
| Remittance Recipient | 20% | 30% | 10% | 0% | 0% | 35% | 5% | **100%** |

---

## 5. Ground-Truth Data Contract (`synthetic_ground_truth`)

To prevent data leakage into ML models, synthetic generator labels and simulated shocks are stored strictly in dedicated tables/files. **ML training features must NEVER load or join on these ground-truth artifacts.**

### 5.1 Schema: `synthetic_user_ground_truth`
```sql
CREATE TABLE synthetic_user_ground_truth (
    user_id                  UUID PRIMARY KEY,
    true_persona             TEXT NOT NULL,
    true_occupation          TEXT NOT NULL,
    baseline_income_bdt      NUMERIC(14,2) NOT NULL,
    target_savings_rate      NUMERIC(5,4) NOT NULL,
    is_drifting              BOOLEAN NOT NULL DEFAULT false,
    drift_target_persona     TEXT,
    drift_start_month        INTEGER,                  -- e.g. Month 7
    generator_seed           BIGINT NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
```

### 5.2 Schema: `synthetic_transaction_ground_truth`
```sql
CREATE TABLE synthetic_transaction_ground_truth (
    transaction_id           UUID PRIMARY KEY,
    user_id                  UUID NOT NULL,
    is_injected_anomaly      BOOLEAN NOT NULL DEFAULT false,
    anomaly_type             TEXT,                     -- sudden_spend_spike | unusual_time | atypical_category | rapid_velocity_burst
    anomaly_multiplier       NUMERIC(6,2),             -- e.g. 4.5x baseline
    life_event_code          TEXT,                     -- medical_emergency | festival_eid | wedding_ceremony | income_loss_shock
    counterfactual_amount    NUMERIC(14,2),            -- What the amount would have been without shock
    created_at               TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
```

---

## 6. Realism Validation Metrics (Phase 5 Quality Gates)

When synthetic data generation completes in Phase 4, Phase 5 will automatically verify these statistical bounds against the generated corpus:

1. **Volume & Coverage:**
   - Total Users: $N \ge 600$ (minimum 500).
   - Time Span: Exactly 12 calendar months (`2025-10-01` to `2026-09-30`).
   - Transaction Count: $\ge 100,000$ transactions (projected 180,000 – 350,000).
2. **Anomaly Target Rate:**
   - Injected transaction anomalies must account for **$2.0\% \text{ to } 3.0\%$** of total transactions.
3. **Cash-Out Rounding Realism:**
   - Over $80\%$ of physical agent cash-out amounts must terminate in round notes (`% 500 == 0` or `% 1000 == 0`), matching physical ATM/Agent liquidity dynamics.
4. **Eid Seasonality Spikes:**
   - Population aggregate discretionary and remittance spend must show a statistically significant bump ($\ge 1.4\times$ above trailing 3-month baseline) during Eid-ul-Fitr (March/April 2026) and Eid-ul-Adha (June 2026).
5. **Income-Expense Coherence:**
   - Zero negative wallet balances across any timestamp.
   - Aggregate savings rate across the population sits within $10.0\% \text{ to } 18.0\%$.

---

## 7. Assumptions & Real-World Calibration Notes

The following empirical assumptions are configured in `data/synthetic/config/` and documented for formal review:

1. **RMG Garment Minimum Wage:**
   - Baseline minimum wage is modeled based on the late 2023 Gazette revision (৳12,500/month basic minimum), with overtime allowances reaching up to ৳22,000–৳28,000 for senior machinists.
2. **MFS Cash-Out Fee Schedule:**
   - Standard app cash-out fee is calibrated at ৳18.50 per ৳1,000 ($1.85\%$).
   - "Priyo Agent" / Favorite Agent discounted tariff is calibrated at ৳14.90 per ৳1,000 ($1.49\%$).
3. **DPS Schemes:**
   - Monthly bank/MFS DPS installments assume prevalent market tenors (৳500, ৳1,000, ৳2,000, ৳5,000) with assumed compounding rates of $7.0\% \text{ to } 9.5\%$.
4. **Inflation & Price Volatility:**
   - Basic grocery baskets (rice, lentils, edible oil) are modeled with realistic monthly price variance ($\pm 5\%$) around trailing averages.
