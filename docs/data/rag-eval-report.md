# RAG Retrieval Evaluation Report

**Evaluation Status:** `PASS` (Target: hit@4 >= 0.85)

## Summary Metrics

| Metric | Target | Result | Status |
|---|---|---|---|
| **Evaluation Queries** | >= 40 | **54** | PASS |
| **hit@1** | Informational | **94.44%** (51/54) | - |
| **hit@4** | >= 85.0% | **100.00%** (54/54) | PASS |
| **No-Result Rate** | <= 5.0% | **0.00%** (0/54) | PASS |
| **Groundedness Pass Rate** | >= 85.0% | **100.00%** (54/54) | PASS |
| **Mean Top-1 Cosine Score** | > 0.30 | **0.3788** | PASS |

## Query Performance Breakdown

| ID | Question | Expected Doc | Top-1 Retrieved | hit@1 | hit@4 | Top Score |
|---|---|---|---|---|---|---|
| `eval_01` | What percentage of after-tax income should go towa... | `budgeting-50-30-20` | `budgeting-50-30-20` | YES | YES | 0.2977 |
| `eval_02` | How does zero based budgeting allocate every unit ... | `budgeting-zero-based` | `budgeting-zero-based` | YES | YES | 0.3242 |
| `eval_03` | What happens when an envelope runs out of money in... | `budgeting-envelope-system` | `budgeting-envelope-system` | YES | YES | 0.3554 |
| `eval_04` | Why is reverse budgeting called paying yourself fi... | `budgeting-pay-yourself-first` | `budgeting-pay-yourself-first` | YES | YES | 0.2611 |
| `eval_05` | How does the simplified 80/20 budget divide person... | `budgeting-80-20-rule` | `budgeting-80-20-rule` | YES | YES | 0.4821 |
| `eval_06` | How should a freelancer manage living expenses dur... | `budgeting-irregular-income` | `budgeting-fixed-vs-variable` | NO | YES | 0.3533 |
| `eval_07` | Why is daily expense tracking important to prevent... | `budgeting-tracking-expenses` | `budgeting-tracking-expenses` | YES | YES | 0.3645 |
| `eval_08` | What is the difference between fixed expenses like... | `budgeting-fixed-vs-variable` | `budgeting-fixed-vs-variable` | YES | YES | 0.4486 |
| `eval_09` | What is the primary purpose and psychological bene... | `emergency-fund-purpose` | `emergency-fund-purpose` | YES | YES | 0.3876 |
| `eval_10` | How many months of essential living expenses shoul... | `emergency-fund-sizing` | `emergency-fund-sizing` | YES | YES | 0.4631 |
| `eval_11` | Where should I park emergency savings for immediat... | `emergency-fund-storage` | `emergency-fund-storage` | YES | YES | 0.3731 |
| `eval_12` | Is holiday shopping or gadget upgrading a valid re... | `emergency-fund-rules` | `emergency-fund-rules` | YES | YES | 0.3415 |
| `eval_13` | What steps should I take to rebuild an emergency c... | `emergency-fund-rebuilding` | `emergency-fund-rebuilding` | YES | YES | 0.2557 |
| `eval_14` | What are the fundamental differences between savin... | `saving-vs-investing-basics` | `saving-vs-investing-basics` | YES | YES | 0.3946 |
| `eval_15` | Is there any financial investment that guarantees ... | `investing-risk-and-return` | `investing-risk-and-return` | YES | YES | 0.3611 |
| `eval_16` | Why should long term goals have higher equity expo... | `investing-time-horizons` | `investing-time-horizons` | YES | YES | 0.3447 |
| `eval_17` | What is the opportunity cost and inflation loss of... | `investing-opportunity-cost` | `investing-opportunity-cost` | YES | YES | 0.3843 |
| `eval_18` | How does asset diversification across uncorrelated... | `investing-diversification` | `investing-diversification` | YES | YES | 0.3415 |
| `eval_19` | How does compound interest create exponential grow... | `compound-interest-mechanics` | `compound-interest-mechanics` | YES | YES | 0.5068 |
| `eval_20` | Does monthly compounding interest yield a higher e... | `compound-interest-frequencies` | `compound-interest-frequencies` | YES | YES | 0.5594 |
| `eval_21` | How do I use the Rule of 72 mental shortcut to est... | `compound-interest-rule-of-72` | `compound-interest-rule-of-72` | YES | YES | 0.3674 |
| `eval_22` | Why does starting to save early at age 22 beat wai... | `compound-interest-starting-early` | `compound-interest-starting-early` | YES | YES | 0.3554 |
| `eval_23` | How do I calculate real returns by subtracting inf... | `compound-interest-real-returns` | `inflation-real-interest-rate` | NO | YES | 0.4372 |
| `eval_24` | What is inflation and how does it erode the purcha... | `inflation-basics` | `investing-opportunity-cost` | NO | YES | 0.3758 |
| `eval_25` | What categories of consumer goods and services mak... | `inflation-measuring-cpi` | `inflation-measuring-cpi` | YES | YES | 0.4636 |
| `eval_26` | What personal finance strategies help protect savi... | `inflation-hedging-strategies` | `inflation-hedging-strategies` | YES | YES | 0.2815 |
| `eval_27` | How do I calculate real interest rate on a deposit... | `inflation-real-interest-rate` | `inflation-real-interest-rate` | YES | YES | 0.5171 |
| `eval_28` | How does a Deposit Pension Scheme DPS monthly inst... | `savings-dps-overview` | `savings-dps-overview` | YES | YES | 0.4126 |
| `eval_29` | What is a Fixed Deposit Receipt FDR term deposit a... | `savings-fdr-overview` | `savings-fdr-overview` | YES | YES | 0.5137 |
| `eval_30` | What is the difference between a high-yield saving... | `savings-accounts-comparison` | `savings-accounts-comparison` | YES | YES | 0.3073 |
| `eval_31` | What interest penalty occurs when breaking an FDR ... | `savings-premature-encashment` | `savings-premature-encashment` | YES | YES | 0.3683 |
| `eval_32` | How does laddering fixed deposits provide staggere... | `savings-fdr-dps-laddering` | `savings-fdr-dps-laddering` | YES | YES | 0.3318 |
| `eval_33` | How does the debt avalanche repayment method order... | `debt-avalanche-method` | `debt-avalanche-method` | YES | YES | 0.5786 |
| `eval_34` | Why does the debt snowball strategy focus on payin... | `debt-snowball-method` | `debt-snowball-method` | YES | YES | 0.4784 |
| `eval_35` | What distinguishes productive good debt from high-... | `debt-good-vs-bad` | `debt-good-vs-bad` | YES | YES | 0.4448 |
| `eval_36` | Why does paying only the credit card minimum payme... | `debt-credit-card-interest` | `debt-credit-card-interest` | YES | YES | 0.3852 |
| `eval_37` | How is the Debt-to-Income DTI ratio calculated to ... | `debt-to-income-ratio` | `debt-to-income-ratio` | YES | YES | 0.4090 |
| `eval_38` | How does the 24-hour delay rule curb impulse shopp... | `impulse-spending-24-hour-rule` | `impulse-spending-24-hour-rule` | YES | YES | 0.3569 |
| `eval_39` | What psychological triggers lead to stress shoppin... | `impulse-spending-emotional-triggers` | `impulse-spending-emotional-triggers` | YES | YES | 0.3109 |
| `eval_40` | Why do frictionless mobile payments make spending ... | `impulse-spending-mfs-friction` | `impulse-spending-mfs-friction` | YES | YES | 0.3899 |
| `eval_41` | How can consumers resist marketing alerts and arti... | `impulse-spending-marketing-nudges` | `impulse-spending-marketing-nudges` | YES | YES | 0.3134 |
| `eval_42` | How do I distinguish between essential needs and u... | `impulse-spending-needs-vs-wants` | `impulse-spending-needs-vs-wants` | YES | YES | 0.2478 |
| `eval_43` | What KPIs are shown on the financial dashboard ove... | `app-dashboard-reading-kpis` | `app-dashboard-reading-kpis` | YES | YES | 0.3920 |
| `eval_44` | How does the Sohoj platform calculate monthly savi... | `app-metrics-savings-rate` | `app-metrics-savings-rate` | YES | YES | 0.3086 |
| `eval_45` | How are necessity expenses and discretionary expen... | `app-metrics-necessity-ratio` | `app-metrics-necessity-ratio` | YES | YES | 0.3848 |
| `eval_46` | What does a spending anomaly alert indicate when a... | `app-anomalies-guide` | `app-anomalies-guide` | YES | YES | 0.4022 |
| `eval_47` | What are the six behavioral spending archetypes su... | `app-behavior-profiles-guide` | `app-behavior-profiles-guide` | YES | YES | 0.3555 |
| `eval_48` | How should I interpret the p10, p50, and p90 predi... | `app-expense-forecast-guide` | `app-expense-forecast-guide` | YES | YES | 0.3763 |
| `eval_49` | What are the standard agent cash out fees for mobi... | `mfs-tariffs-fees` | `mfs-tariffs-fees` | YES | YES | 0.3925 |
| `eval_50` | Why should I never share my wallet PIN or one-time... | `mfs-security-privacy` | `mfs-security-privacy` | YES | YES | 0.2560 |
| `eval_51` | How does Row-Level Security protect user data and ... | `app-privacy-and-ai-consent` | `app-privacy-and-ai-consent` | YES | YES | 0.3694 |
| `eval_52` | How does the app track financial goal progress per... | `app-goals-tracking-faq` | `app-goals-tracking-faq` | YES | YES | 0.3742 |
| `eval_53` | What is the definition of assets, liabilities, and... | `glossary-personal-finance` | `glossary-personal-finance` | YES | YES | 0.3506 |
| `eval_54` | What does lifestyle creep mean when your spending ... | `glossary-spending-and-behavior` | `glossary-spending-and-behavior` | YES | YES | 0.2465 |
