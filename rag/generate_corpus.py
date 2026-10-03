"""Author the curated financial-literacy corpus for Sohoj RAG knowledge base.

Generates 52 unique, educational, agent-authored documents with YAML front-matter.
Strictly adheres to:
- No copyrighted text copying.
- Zero 'guaranteed return' / 'risk-free profit' claims.
- Proper heading hierarchy for heading-aware chunking.
"""

from __future__ import annotations

from pathlib import Path

DOCS_DIR = Path("rag/documents")

DOCUMENTS: dict[str, dict[str, str]] = {
    # 1. Budgeting Basics & Frameworks
    "budgeting-50-30-20.md": {
        "title": "50/30/20 Budgeting Rule Explained",
        "topic": "budgeting",
        "language": "en",
        "version": "1.0",
        "content": """# 50/30/20 Budgeting Rule Explained

The 50/30/20 rule is an intuitive budgeting framework designed to divide after-tax income into three distinct functional categories: necessities, discretionary spending, and savings or debt reduction.

## Category Breakdown

### 50% for Needs
Needs encompass non-negotiable living expenses required for survival and livelihood. In personal finance, this includes:
- Housing costs such as apartment rent or mortgage service.
- Essential grocery staples and home cooking supplies.
- Basic utilities: electricity, water, gas, and essential mobile connectivity.
- Commute and transportation expenses necessary for work.
- Minimum monthly payments on existing loans.

### 30% for Wants
Wants consist of lifestyle choices and discretionary consumption that enhance quality of life but are not strictly vital:
- Dining out, café visits, and food delivery.
- Entertainment, streaming subscriptions, and hobby purchases.
- Non-essential shopping and electronics upgrades.
- Vacation and leisure travel.

### 20% for Savings and Future Security
The final 20% is earmarked for financial stability:
- Building and replenishing the emergency fund.
- Long-term deposits, pension schemes, and investment contributions.
- Accelerated debt paydown beyond minimum payments.

## Adapting the Rule for Varied Incomes
While the 50/30/20 allocation serves as a widely recognized starting point, high living costs in urban areas may require temporary adjustment to 60/20/20 or 70/20/10 until earnings expand.
""",
    },
    "budgeting-zero-based.md": {
        "title": "Zero-Based Budgeting: Give Every Taka a Job",
        "topic": "budgeting",
        "language": "en",
        "version": "1.0",
        "content": """# Zero-Based Budgeting Guide

Zero-based budgeting is an intentional financial method where your total monthly income minus every allocated expense, saving, and debt payment equals exactly zero at the end of planning.

## The Core Concept: Zero Balance Planning
A zero balance does not mean having zero money in your bank account or wallet. Rather, it means that every single unit of currency earned is given a dedicated, premeditated purpose before the month begins.

$$\\text{Income} - \\text{Expenses} - \\text{Savings Allocations} = 0$$

## How to Build a Zero-Based Budget

### Step 1: Record Total Expected Monthly Cash Inflow
Calculate reliable net monthly income, including salary, freelance invoices, and business earnings.

### Step 2: List Mandatory Fixed and Variable Expenses
Account for shelter, groceries, utility bills, and transport costs.

### Step 3: Assign Surplus to Savings and Debt Paydown
Direct any leftover unallocated funds into explicit targets such as an emergency fund, savings goals, or loan principal reductions.

### Step 4: Track and Reconcile Weekly
Compare actual spending against planned allotments. If grocery costs run higher than anticipated, adjust by reducing discretionary spending in another category to keep the bottom line balanced.
""",
    },
    "budgeting-envelope-system.md": {
        "title": "Envelope Budgeting and Digital Sub-Wallets",
        "topic": "budgeting",
        "language": "en",
        "version": "1.0",
        "content": """# Envelope Budgeting and Digital Sub-Wallets

The envelope budgeting method is a visual cash management technique that prevents overspending by physically or digitally isolating allocated funds into distinct category buckets.

## Traditional Cash Envelopes
In its classic form, income is withdrawn in cash on salary day and distributed into labelled physical paper envelopes:
- Groceries Envelope
- Transportation Envelope
- Dining & Social Envelope
- Personal Care Envelope

Once the cash inside an envelope is exhausted, spending in that specific category ceases until the following month, enforcing strict discipline.

## Digital Adaptation Using MFS and Sub-Accounts
In modern cashless and digital banking environments:
- Use multiple mobile financial service (MFS) wallets or digital sub-accounts to isolate funds.
- Maintain a primary transactional account for automated utility bills and rent.
- Transfer specific allowances into separate digital cards or wallets for daily discretionary transactions.
- Never borrow from bills or savings envelopes to cover discretionary category shortfalls.
""",
    },
    "budgeting-pay-yourself-first.md": {
        "title": "Pay Yourself First: Reverse Budgeting Explained",
        "topic": "budgeting",
        "language": "en",
        "version": "1.0",
        "content": """# Pay Yourself First Strategy

Pay yourself first, often referred to as reverse budgeting, prioritizes savings and debt reduction goals before allocating money to lifestyle consumption.

## The Flaw of Traditional Residual Saving
Most people approach saving with the residual equation:

$$\\text{Savings} = \\text{Income} - \\text{Expenses}$$

Under this approach, individuals spend throughout the month and save whatever remains at month-end. In practice, lifestyle creep and impulse transactions typically absorb all remaining liquidity, leaving little to no savings.

## The Reverse Budgeting Formula
The reverse budgeting framework inverts this order:

$$\\text{Allowable Expenses} = \\text{Income} - \\text{Pre-committed Savings}$$

## Implementation Routine
1. On the day your salary or primary income arrives, immediately transfer a pre-determined percentage (e.g., 15% to 25%) to your savings or investment account.
2. Automate recurring standing instructions or scheduled transfers to eliminate reliance on willpower.
3. Freely spend the remaining income on necessary bills and guilt-free lifestyle expenses, knowing your future financial commitments are already satisfied.
""",
    },
    "budgeting-80-20-rule.md": {
        "title": "The 80/20 Simplified Savings Budget",
        "topic": "budgeting",
        "language": "en",
        "version": "1.0",
        "content": """# The 80/20 Simplified Budget

The 80/20 budget is a streamlined financial system designed for individuals who find detailed category tracking overly cumbersome.

## How the 80/20 Rule Operates
The formula separates your net monthly earnings into only two broad buckets:

### 20% Toward Financial Security
The first 20% of your earnings goes directly toward long-term financial health:
- Emergency fund contributions.
- Long-term savings and investments.
- Accelerated principal payments on existing debts.

### 80% Toward All Other Living Expenses
The remaining 80% covers all other expenditures combined:
- Housing, food, utilities, transport, healthcare.
- Leisure, dining out, hobbies, and personal shopping.

## Who Benefits from the 80/20 Budget?
- Busy professionals who dislike micro-tracking dozens of spending categories.
- Individuals with relatively stable incomes and consistent basic expenses.
- Anyone seeking a friction-free entry point into disciplined personal savings habits.
""",
    },
    "budgeting-irregular-income.md": {
        "title": "Budgeting on Variable and Freelance Income",
        "topic": "budgeting",
        "language": "en",
        "version": "1.0",
        "content": """# Budgeting on Variable and Freelance Income

Managing finances with irregular, seasonal, or gig-based income requires specialized risk controls to maintain stability through unpredictable earnings cycles.

## Calculate Your Baseline Survival Budget
Determine the minimum amount required to cover essential necessities every month:
- Rent, groceries, utility bills, internet connection, and minimum debt commitments.
- Exclude all discretionary outings, luxury purchases, and non-vital upgrades.
- This baseline represents your critical monthly spending threshold.

## The Holding Account Buffer Strategy
1. Establish a dedicated business or deposit holding account where client payouts arrive.
2. Transfer a fixed 'salary' amount each month from the holding account to your personal living account.
3. During high-income months, allow excess funds to accumulate in the holding account.
4. During lean months, draw your steady 'salary' from the accumulated holding buffer without financial stress.

## Prioritizing an Expanded Emergency Reserve
Freelancers and gig workers should aim for an emergency buffer covering 6 to 9 months of baseline expenses rather than the traditional 3 months for salaried employees.
""",
    },
    "budgeting-tracking-expenses.md": {
        "title": "Daily Expense Tracking Best Practices",
        "topic": "budgeting",
        "language": "en",
        "version": "1.0",
        "content": """# Daily Expense Tracking Methods

Tracking daily expenses provides the observational foundation needed to understand spending behavior, plug cash leaks, and make informed financial decisions.

## Why Tracking Matters
Without tracking, micro-expenses such as daily street snacks, ride-sharing trips, and small online purchases easily accumulate unnoticed, resulting in month-end cash shortages.

## Systematic Tracking Approaches
- **Real-Time Digital Entry:** Record transactions immediately using mobile apps or wallet logs at the point of sale.
- **Daily Evening Audit:** Spend 3 minutes each evening reviewing digital payment receipts and pocket cash outflows.
- **Weekly Expense Review:** Aggregate weekly outflows by category to identify emerging overspending trends before the month closes.

## Common Tracking Pitfalls
- Forgetting small cash transactions given to local vendors or delivery tips.
- Delaying data entry until receipts and memories fade.
- Over-complicating category structures with dozens of niche tags instead of broad, clear buckets.
""",
    },
    "budgeting-fixed-vs-variable.md": {
        "title": "Fixed vs Variable Expenses in Personal Budgeting",
        "topic": "budgeting",
        "language": "en",
        "version": "1.0",
        "content": """# Fixed vs Variable Expenses Explained

Understanding the distinction between fixed and variable costs is essential for optimizing monthly cash flow and creating actionable spending adjustments.

## Defining Fixed Expenses
Fixed expenses remain predictable and constant in amount from month to month:
- Residential rent or fixed mortgage payments.
- Internet service and recurring broadband subscriptions.
- Insurance premiums and loan installments.
- Children's fixed school tuition fees.

Fixed expenses are difficult to reduce quickly without major lifestyle decisions such as moving homes or refinancing debts.

## Defining Variable Expenses
Variable expenses fluctuate in response to day-to-day decisions and external conditions:
- Grocery shopping and household supplies.
- Electricity and gas utility usage.
- Commute and transportation costs.
- Social outings, dining out, and entertainment.

Variable expenses represent the quickest leverage point when urgent spending reductions are required.
""",
    },
    # 2. Emergency Fund
    "emergency-fund-purpose.md": {
        "title": "What is an Emergency Fund and Why It Matters",
        "topic": "emergency_fund",
        "language": "en",
        "version": "1.0",
        "content": """# What is an Emergency Fund and Why it Matters

An emergency fund is a dedicated, liquid cash reserve set aside exclusively to protect against unplanned financial shocks and severe life disruptions.

## Purpose of the Safety Cushion
The primary objective of an emergency fund is not wealth creation or investment yield, but psychological security and financial defense:
- Prevents turning to high-interest borrowing or credit card debt when emergencies arise.
- Avoids the forced liquidation of long-term investments or property at distressed market prices.
- Provides breathing room during unexpected medical crises or sudden job loss.

## What Constitutes a True Emergency?
An authentic emergency meets three criteria:
1. **Unplanned:** It could not have been foreseen or scheduled.
2. **Necessary:** Addressing it is essential for health, safety, or basic livelihood.
3. **Urgent:** Immediate financial action is required without delay.
""",
    },
    "emergency-fund-sizing.md": {
        "title": "Sizing Your Emergency Fund: 3 to 6 Months Guide",
        "topic": "emergency_fund",
        "language": "en",
        "version": "1.0",
        "content": """# Sizing Your Emergency Fund: 3 to 6 Months Guide

Determining the appropriate size of an emergency fund depends on personal income stability, household obligations, and employment predictability.

## The Essential Monthly Expense Metric
Emergency funds should be measured in terms of **months of essential living expenses**, not gross income:

$$\\text{Target Emergency Fund} = \\text{Monthly Essential Needs} \\times \\text{Number of Months}$$

Essential needs include rent, food, medical necessities, utilities, and mandatory debt obligations.

## Guidelines by Household Profile
- **3 Months of Expenses:** Dual-income households with stable corporate jobs and no major dependents.
- **6 Months of Expenses:** Single-income households, families with young children or elderly dependents, and homeowners with property obligations.
- **9 to 12 Months of Expenses:** Freelancers, independent contractors, small business owners, and workers in cyclical industries.
""",
    },
    "emergency-fund-storage.md": {
        "title": "Where to Park Emergency Savings (Liquidity vs Yield)",
        "topic": "emergency_fund",
        "language": "en",
        "version": "1.0",
        "content": """# Where to Park Emergency Savings

Choosing where to hold emergency savings involves balancing instant accessibility with capital safety and inflation preservation.

## Priority #1: Liquidity and Capital Preservation
Emergency money must be immediately accessible and free from market risk. Never place your emergency cushion into volatile assets such as equities, commodities, or illiquid real estate.

## Recommended Multi-Tier Storage Structure
To balance access with modest earnings, consider a two-tier arrangement:

### Tier 1: Immediate Cash (1 to 2 Months)
- High-yield bank savings account or verified mobile wallet balance.
- Instant debit card or ATM access 24 hours a day, 7 days a week.

### Tier 2: Secondary Liquidity (2 to 4 Months)
- Short-term fixed deposits (e.g., 3-month or 6-month term deposits) with clear premature withdrawal options.
- Treasury bills or short-term government bonds that can be liquidated within 1 to 2 business days.
""",
    },
    "emergency-fund-rules.md": {
        "title": "When (and When Not) to Tap into an Emergency Fund",
        "topic": "emergency_fund",
        "language": "en",
        "version": "1.0",
        "content": """# When to Use an Emergency Fund

Clear boundary rules prevent the gradual depletion of your safety cushion on everyday non-emergencies.

## Valid Reasons to Tap Emergency Savings
- Sudden involuntary unemployment or complete business interruption.
- Emergency medical procedures, hospitalization, or critical prescriptions.
- Essential vehicle repairs required to commute to work.
- Urgent household repairs (e.g., major plumbing failure, broken refrigerator).

## Invalid Reasons to Tap Emergency Savings
- Festival shopping, wedding gifts, and holiday bonuses.
- Flash sales, gadget upgrades, or promotional discounts.
- Predictable annual expenses like vehicle registration or school tuition (these belong in a sinking fund).
- Speculative investment opportunities.
""",
    },
    "emergency-fund-rebuilding.md": {
        "title": "Rebuilding an Emergency Fund After Depletion",
        "topic": "emergency_fund",
        "language": "en",
        "version": "1.0",
        "content": """# Rebuilding an Emergency Fund After Depletion

Using emergency savings for a genuine crisis is a sign the system worked as intended. However, promptly restoring the fund is critical to protect against subsequent shocks.

## Immediate Steps to Replenish
1. **Pause Non-Essential Discretionary Goals:** Temporarily redirect money allocated for luxury items, vacations, and optional upgrades toward replenishing the emergency fund.
2. **Audit Recurring Subscriptions:** Cancel unused services and trim variable living expenses for 60 to 90 days.
3. **Funnel Windfalls Directly to Safety:** Deposit seasonal bonuses, tax refunds, and overtime earnings straight into the safety account.
4. **Automate Dedicated Rebuilding Transfers:** Establish a scheduled standing transfer on pay day to steadily rebuild the reserve until the targeted buffer is reached.
""",
    },
    # 3. Saving vs. Investing
    "saving-vs-investing-basics.md": {
        "title": "Saving vs. Investing: Fundamental Differences",
        "topic": "investing",
        "language": "en",
        "version": "1.0",
        "content": """# The Difference Between Saving and Investing

While saving and investing are complementary financial activities, they serve fundamentally different purposes in wealth management.

## Defining Saving
Saving involves setting aside current cash for short-term needs or emergencies in safe, liquid accounts.
- **Primary Goal:** Capital preservation and immediate access.
- **Risk Level:** Very low; principal is generally protected.
- **Time Horizon:** 0 to 3 years.
- **Vehicles:** Bank savings accounts, term deposits, digital wallets.

## Defining Investing
Investing involves deploying capital into assets with the expectation of generating capital growth or recurring income over the long term.
- **Primary Goal:** Growing purchasing power faster than inflation.
- **Risk Level:** Moderate to high; principal fluctuates and returns are subject to market conditions.
- **Time Horizon:** 5 years or longer.
- **Vehicles:** Equities, index funds, mutual funds, real estate, and government bonds.
""",
    },
    "investing-risk-and-return.md": {
        "title": "Risk and Return Trade-offs Explained",
        "topic": "investing",
        "language": "en",
        "version": "1.0",
        "content": """# Risk and Expected Return Profiles

In financial markets, the relationship between potential risk and expected return is governed by the principle that higher potential returns require taking on greater risk.

## The Core Trade-off
No legitimate financial asset provides high returns with zero risk. Any proposition claiming guaranteed high profits without downside risk should be treated with extreme caution.

## Spectrum of Financial Assets
- **Cash and Bank Deposits:** Lowest risk of nominal capital loss, but high vulnerability to purchasing power erosion from inflation.
- **Government Debt and Sovereign Bonds:** Low credit risk backed by state revenue, offering predictable coupon payments with modest real yield.
- **Broad Market Equities:** Higher volatility in the short term, with historical potential for long-term real growth over 7-to-10-year horizons.
- **Alternative Assets and Commodities:** High volatility driven by supply, demand, and speculative cycles.
""",
    },
    "investing-time-horizons.md": {
        "title": "Time Horizon: Short-Term Goals vs Long-Term Growth",
        "topic": "investing",
        "language": "en",
        "version": "1.0",
        "content": """# Aligning Time Horizons with Financial Strategy

Matching your investment vehicle with your planned time horizon prevents forced liquidation during unfavorable market downturns.

## Short-Term Horizon (Under 3 Years)
- **Goals:** Wedding expenses, vehicle down payment, emergency cushion.
- **Strategy:** Capital preservation is paramount. Stick to high-yield savings accounts, fixed deposits, and short-term debt instruments where nominal value does not fluctuate.

## Medium-Term Horizon (3 to 7 Years)
- **Goals:** Home purchase down payment, graduate degree tuition.
- **Strategy:** Balanced asset allocation combining high-quality fixed income instruments with conservative equity exposure.

## Long-Term Horizon (7+ Years)
- **Goals:** Retirement security, generational wealth, children's higher education.
- **Strategy:** Higher equity exposure to harness compounding growth, with sufficient time to weather market volatility.
""",
    },
    "investing-opportunity-cost.md": {
        "title": "The Opportunity Cost of Holding Idle Cash",
        "topic": "investing",
        "language": "en",
        "version": "1.0",
        "content": """# The Opportunity Cost of Holding Idle Cash

While holding cash provides emotional comfort and liquidity, keeping excessive cash reserves beyond emergency needs incurs a significant hidden cost.

## Understanding Inflation Drag
Cash does not grow on its own. When annual inflation averages 7% to 9%, paper cash or low-interest current balances lose purchasing power every year:

$$\\text{Real Value After } t \\text{ Years} = \\frac{\\text{Nominal Cash}}{(1 + \\text{Inflation Rate})^t}$$

A ৳100,000 cash balance in an environment with 8% annual inflation loses approximately half of its purchasing power in roughly 9 years.

## Balancing Prudence with Growth
Prudent personal finance distinguishes between:
- **Operating cash and emergency reserves:** Must remain liquid and safe regardless of yield.
- **Surplus wealth:** Should be deployed into productive, inflation-hedging assets to maintain long-term financial independence.
""",
    },
    "investing-diversification.md": {
        "title": "Asset Diversification Fundamentals",
        "topic": "investing",
        "language": "en",
        "version": "1.0",
        "content": """# Asset Diversification Fundamentals

Diversification is the risk management practice of spreading investments across different asset classes, industries, and instruments to reduce the impact of any single failure.

## Why Diversification Protects Wealth
Different asset classes respond differently to economic cycles:
- During periods of rising inflation, tangible assets and commodities may perform well while fixed-coupon bonds suffer.
- During economic downturns, high-quality government securities often preserve value while equity prices drop.

By holding an uncorrelated mix of assets, overall portfolio volatility is dampened without necessarily compromising long-term return expectations.

## Practical Diversification Steps
- Avoid concentrating all savings in a single bank or term deposit.
- Spread equity investments across broad-market index funds rather than individual company stocks.
- Maintain a thoughtful balance between fixed-income instruments and growth assets.
""",
    },
    # 4. Compound Interest Explained
    "compound-interest-mechanics.md": {
        "title": "How Compound Interest Works: Principle, Rate, Time",
        "topic": "compound_interest",
        "language": "en",
        "version": "1.0",
        "content": """# How Compound Interest Works Over Time

Compound interest is interest calculated on the initial principal and on the accumulated interest from previous periods, often called 'interest on interest'.

## The Mathematical Foundation
The future value formula for compound growth is:

$$A = P \\left(1 + \\frac{r}{n}\\right)^{nt}$$

Where:
- $A$ = Final accrued amount
- $P$ = Initial principal balance
- $r$ = Annual nominal interest rate (decimal)
- $n$ = Number of compounding periods per year
- $t$ = Number of years invested

## The Hockey Stick Curve
In the early years, growth appears gradual because the interest base is modest. However, as accumulated interest grows larger than the original contributions, asset growth accelerates exponentially over extended time horizons.
""",
    },
    "compound-interest-frequencies.md": {
        "title": "Compounding Frequency: Monthly vs Annual",
        "topic": "compound_interest",
        "language": "en",
        "version": "1.0",
        "content": """# Compounding Frequency: Monthly vs Annual

The frequency at which interest is credited directly influences the total return earned on savings or charged on borrowed capital.

## More Frequent Compounding Yields Higher Return
When interest compounds monthly rather than annually, earned interest begins generating additional interest eleven times earlier during the year.

### Effective Annual Rate (EAR)
The Effective Annual Rate reflects the true annual return accounting for compounding frequency:

$$\\text{EAR} = \\left(1 + \\frac{r}{n}\\right)^n - 1$$

For example, an 8.0% nominal annual rate compounded monthly ($n=12$) yields an effective annual rate of:

$$\\text{EAR} = \\left(1 + \\frac{0.08}{12}\\right)^{12} - 1 \\approx 8.30\\%$$

## Significance for Savings Schemes
Deposit schemes (such as DPS) with monthly compounding credit gains faster than annual instruments, compounding each contribution immediately upon deposit.
""",
    },
    "compound-interest-rule-of-72.md": {
        "title": "The Rule of 72 for Estimating Doubling Time",
        "topic": "compound_interest",
        "language": "en",
        "version": "1.0",
        "content": """# The Rule of 72 for Estimating Doubling Time

The Rule of 72 is a practical mental math shortcut used to estimate how many years it takes for an investment to double at a given annual compound interest rate.

## The Rule of 72 Formula

$$\\text{Years to Double} \\approx \\frac{72}{\\text{Annual Rate (\\%)}}$$

## Examples across Common Return Rates
- **At 6% annual return:** $72 / 6 = 12$ years to double.
- **At 8% annual return:** $72 / 8 = 9$ years to double.
- **At 10% annual return:** $72 / 10 = 7.2$ years to double.
- **At 12% annual return:** $72 / 12 = 6$ years to double.

## Application to Inflation
The Rule of 72 applies equally to the erosion of purchasing power. If inflation averages 8%, the purchasing power of idle cash will be halved in approximately $72 / 8 = 9$ years.
""",
    },
    "compound-interest-starting-early.md": {
        "title": "The Advantage of Starting Early in Wealth Accumulation",
        "topic": "compound_interest",
        "language": "en",
        "version": "1.0",
        "content": """# The Cost of Waiting: Starting Early vs Later

In compound growth calculations, **time** is often more powerful than the total cash amount contributed.

## Illustrative Comparison
Consider two savers investing at an assumed 8% annual compound return:
- **Saver A:** Begins at age 22, contributes ৳5,000 monthly for 10 years (until age 32), and stops adding new money, letting it compound until age 55.
- **Saver B:** Waits until age 32, then contributes ৳5,000 monthly for 23 consecutive years until age 55.

Even though Saver B contributes more than twice as much total capital, Saver A's early 10-year head start allows compounding to produce a comparable or larger ending balance by age 55.

## Key Takeaway
Do not delay saving while waiting for a larger salary. Regular, modest contributions started in your twenties or early thirties work harder than larger sums added under time pressure later in life.
""",
    },
    "compound-interest-real-returns.md": {
        "title": "Real Returns: Nominal Growth vs. Purchasing Power",
        "topic": "compound_interest",
        "language": "en",
        "version": "1.0",
        "content": """# Real Returns: Nominal Growth vs. Purchasing Power

Evaluating financial growth requires distinguishing between the face value of money (nominal return) and its true purchasing capability (real return).

## The Fisher Equation
The relationship between nominal interest rate ($i$), real interest rate ($r$), and inflation rate ($\\\\pi$) is given by:

$$1 + i = (1 + r)(1 + \\pi)$$

For standard calculations, this is approximated as:

$$r \\approx i - \\pi$$

## Practical Implications
If a fixed deposit yields a nominal 8.5% interest rate while national inflation runs at 9.0%, the investor's real return is:

$$r \\approx 8.5\\% - 9.0\\% = -0.5\\%$$

In real purchasing terms, the investor is losing half a percent of purchasing capability annually despite seeing a larger nominal balance on paper.
""",
    },
    # 5. Inflation
    "inflation-basics.md": {
        "title": "What is Inflation and How Purchasing Power Erodes",
        "topic": "inflation",
        "language": "en",
        "version": "1.0",
        "content": """# What is Inflation and How Purchasing Power Erodes

Inflation is the sustained, general increase in the price of goods and services across an economy over time, resulting in a loss of purchasing power per unit of currency.

## Everyday Effects of Inflation
When inflation occurs, every unit of currency buys a smaller quantity of goods and services:
- Staple food prices (rice, lentils, cooking oil) require higher monthly allocations.
- Transport tariffs, electricity tariffs, and housing rents adjust upward.
- Living expenses increase even when personal consumption habits remain identical.

## The Cumulative Compounding Effect
Just as compound interest expands savings, inflation compounds against wealth. An annual inflation rate of 7% doubles the cost of living in approximately 10 years, making passive cash savings inadequate for long-term security without inflation-hedging strategies.
""",
    },
    "inflation-measuring-cpi.md": {
        "title": "How Inflation is Measured: The Consumer Price Index",
        "topic": "inflation",
        "language": "en",
        "version": "1.0",
        "content": """# Consumer Price Index (CPI) and Cost of Living

National statistics agencies measure inflation by tracking the Consumer Price Index (CPI), which monitors the cost of a standardized basket of household consumer goods.

## Composition of the CPI Basket
The typical consumer basket reflects average household consumption:
- Food and non-alcoholic beverages (often the largest weight in developing economies).
- Housing, utilities, water, gas, and electricity.
- Transportation and vehicle fuel costs.
- Healthcare and educational services.
- Clothing and footwear.

## Headline vs. Core Inflation
- **Headline Inflation:** The total inflation rate reflecting all goods in the CPI basket, including volatile food and energy commodities.
- **Core Inflation:** Excludes food and energy items to measure underlying, persistent inflationary pressure driven by broader economic factors.
""",
    },
    "inflation-hedging-strategies.md": {
        "title": "Personal Finance Strategies to Hedge Against Inflation",
        "topic": "inflation",
        "language": "en",
        "version": "1.0",
        "content": """# Hedging Against Inflation in Personal Finance

Protecting household wealth against ongoing currency debasement requires practical defensive strategies across earning, spending, and investing.

## Asset Allocation Defenses
- **Productive Equities:** Well-managed companies can raise prices to match inflation, protecting operational cash flows over long horizons.
- **Real Estate and Land:** Real property values and rental incomes historically adjust alongside general inflation trends.
- **Floating-Rate and High-Yield Term Instruments:** Shorter-maturity deposits allow periodic reinvestment at updated, higher prevailing interest rates.

## Personal Income Defenses
- Cultivate specialized skills and multiple income streams to negotiate salary increases that outpace headline CPI inflation.
- Audit recurring lifestyle spending regularly to cut non-essential consumption that rises in price without adding value.
""",
    },
    "inflation-real-interest-rate.md": {
        "title": "Nominal Interest Rates vs Real Interest Rates",
        "topic": "inflation",
        "language": "en",
        "version": "1.0",
        "content": """# Nominal Interest Rates vs. Real Interest Rates

Understanding the gap between nominal rates and real rates prevents savers from misjudging the true performance of their deposit accounts.

## Core Definitions
- **Nominal Interest Rate:** The stated percentage rate paid by a bank on a deposit or bond, before accounting for taxes, fees, and inflation.
- **Real Interest Rate:** The percentage increase in real purchasing power gained after adjusting for prevailing inflation.

## Calculating Real Yield on Savings
When evaluating deposit pension schemes or term deposits:
1. Identify the gross nominal interest rate offered by the institution.
2. Deduct applicable tax on interest (e.g., 10% to 15% withholding tax).
3. Deduct the prevailing inflation rate.

$$\\text{Real After-Tax Rate} = [\\text{Nominal Rate} \\times (1 - \\text{Tax Rate})] - \\text{Inflation Rate}$$

If the resulting figure is positive, your capital is expanding in real terms; if negative, purchasing power is declining.
""",
    },
    # 6. DPS, FDR & Savings Concepts (Generic Educational Level)
    "savings-dps-overview.md": {
        "title": "Deposit Pension Scheme (DPS) Mechanics and Structure",
        "topic": "banking_products",
        "language": "en",
        "version": "1.0",
        "content": """# Deposit Pension Scheme (DPS) Mechanics

A Deposit Pension Scheme (DPS) is a contractual, recurring monthly deposit product offered by banks and non-bank financial institutions to build disciplined savings over time.

## How a DPS Works
- **Fixed Monthly Installment:** The account holder agrees to deposit a predetermined amount (e.g., ৳1,000 to ৳25,000) every month on a set date.
- **Fixed Tenure:** Common terms range from 3, 5, 7, to 10 years.
- **Compounding Interest:** Accumulated monthly contributions earn compound interest over the selected tenure.
- **Lump-Sum Maturity:** At maturity, the depositor receives the full principal plus accrued interest minus applicable withholding tax.

## Key Considerations
- Late monthly installments typically incur minor penalty fees.
- Withdrawing before completion usually results in lower, standard savings account interest rates rather than the full DPS rate.
""",
    },
    "savings-fdr-overview.md": {
        "title": "Fixed Deposit Receipt (FDR) Term Deposit Basics",
        "topic": "banking_products",
        "language": "en",
        "version": "1.0",
        "content": """# Fixed Deposit Receipt (FDR) Term Deposits

A Fixed Deposit Receipt (FDR), also known as a term deposit, is a savings instrument where a single lump sum is locked for a specified maturity period at an agreed rate.

## Operating Characteristics
- **Lump-Sum Commitment:** Unlike recurring DPS products, an FDR requires the full principal upfront.
- **Tenure Flexibility:** Terms typically range from 1 month to 3 or 5 years.
- **Interest Payout Options:** Depositors can choose to receive interest payouts monthly, quarterly, or compounded until final maturity.
- **Capital Safety:** Deposits within regulated banking institutions carry minimal default risk compared to speculative assets.

## Suitability
FDRs are well-suited for parking cash reserves, business capital buffers, or funds committed to known medium-term milestones (e.g., a home down payment needed in 2 years).
""",
    },
    "savings-accounts-comparison.md": {
        "title": "Savings Accounts vs. Current Accounts",
        "topic": "banking_products",
        "language": "en",
        "version": "1.0",
        "content": """# High-Yield Savings Accounts vs. Current Accounts

Selecting the right transaction account ensures daily cash flow needs are met without leaving liquid reserves unrewarded.

## Current Accounts
- **Purpose:** High-volume daily transactions and commercial operations.
- **Interest:** Typically pays zero interest.
- **Restrictions:** No limits on transaction frequency or daily deposit/withdrawal counts.
- **Best For:** Businesses, merchants, and transactional operating accounts.

## Savings Accounts
- **Purpose:** Safe personal storage for liquid emergency buffers and household funds.
- **Interest:** Pays a modest interest rate, often calculated on daily or minimum monthly balances.
- **Restrictions:** May enforce monthly withdrawal limits or minimum balance thresholds.
- **Best For:** Individuals holding emergency funds and money for upcoming monthly bills.
""",
    },
    "savings-premature-encashment.md": {
        "title": "Premature Encashment Penalties on Term Deposits",
        "topic": "banking_products",
        "language": "en",
        "version": "1.0",
        "content": """# Premature Encashment Penalties and Rules

Breaking a Fixed Deposit or DPS before its contractual maturity date carries financial consequences that depositors should understand in advance.

## The Penalty Mechanism
When an FDR or DPS is closed early:
- The financial institution forfeits the agreed term deposit rate.
- Interest is recalculated using the lower, standard savings account rate for the period held.
- If liquidated within a short initial window (e.g., within 3 or 6 months), the bank may pay zero interest, returning only the original principal.

## How to Prevent Premature Liquidations
- Maintain an independent liquid emergency fund in a regular savings account so you are never forced to break an FDR for minor emergencies.
- Stagger term deposit tenures into smaller amounts rather than locking your entire balance in a single large deposit.
""",
    },
    "savings-fdr-dps-laddering.md": {
        "title": "Laddering Fixed Deposits for Staggered Liquidity",
        "topic": "banking_products",
        "language": "en",
        "version": "1.0",
        "content": """# Laddering FDRs and DPS for Liquidity and Staggered Maturity

Deposit laddering is an allocation strategy that balances access to cash with higher interest rates by staggering maturities across multiple intervals.

## How an FDR Ladder Works
Instead of investing ৳300,000 into a single 3-year term deposit:
1. Place ৳100,000 into a 1-year deposit.
2. Place ৳100,000 into a 2-year deposit.
3. Place ৳100,000 into a 3-year deposit.

## The Rolling Maturity Cycle
When the 1-year deposit matures, reinvest it into a new 3-year deposit. Continue this annual rollover process.

### Benefits of the Ladder
- **Predictable Liquidity:** One-third of your capital matures every year, providing regular access to cash without penalties.
- **Rate Reinvestment Flexibility:** If interest rates rise, maturing portions can be rolled into higher-yielding instruments.
- **Reduced Reinvestment Risk:** You avoid locking your entire savings at a single point in the interest rate cycle.
""",
    },
    # 7. Debt Repayment Strategies
    "debt-avalanche-method.md": {
        "title": "The Debt Avalanche Method: High Interest First",
        "topic": "debt_management",
        "language": "en",
        "version": "1.0",
        "content": """# Debt Avalanche Method Explained

The Debt Avalanche is a mathematically optimal debt elimination strategy that focuses extra payments on the loan carrying the highest interest rate.

## Step-by-Step Implementation
1. List all active debts, noting the outstanding balance, minimum monthly payment, and annual interest rate (APR).
2. Pay the minimum required installment on all debts to protect your credit standing.
3. Channel all remaining debt repayment funds toward the debt with the **highest interest rate**.
4. Once that debt is fully repaid, roll its entire payment amount into the debt with the next-highest rate.

## Mathematical Efficiency
By eliminating high-interest debt first, the avalanche method minimizes the total interest paid over the life of the loans and shortens overall repayment time.
""",
    },
    "debt-snowball-method.md": {
        "title": "The Debt Snowball Method: Smallest Balance First",
        "topic": "debt_management",
        "language": "en",
        "version": "1.0",
        "content": """# Debt Snowball Method Explained

The Debt Snowball is a behavior-focused debt repayment strategy that prioritizes paying off debts in order of smallest outstanding balance first.

## How the Snowball Works
1. List all debts ordered by **smallest balance to largest balance**, regardless of interest rates.
2. Pay the mandatory minimum on all debts.
3. Direct all extra repayment funds toward the debt with the **smallest balance** until it is completely cleared.
4. Take the full payment from that first cleared debt and apply it to the next-smallest balance on your list.

## Why Psychological Momentum Matters
While the avalanche method saves more on interest on paper, the snowball method delivers quick wins that boost motivation. Clearing accounts off your list provides tangible psychological momentum, helping borrowers stick with their debt payoff plan.
""",
    },
    "debt-good-vs-bad.md": {
        "title": "Good Debt vs Bad Debt Fundamentals",
        "topic": "debt_management",
        "language": "en",
        "version": "1.0",
        "content": """# Good Debt vs. Bad Debt Fundamentals

Debt is a financial tool whose value depends on whether borrowed capital finances productive assets or depreciating lifestyle consumption.

## Characteristics of Productive ('Good') Debt
- Borrowed at manageable, competitive interest rates.
- Funds assets with the potential to appreciate or generate future income (e.g., education, business expansion, modest mortgage).
- Monthly payments fit comfortably within household cash flow limits.

## Characteristics of High-Cost ('Bad') Debt
- High annual interest rates, such as credit card debt or uncollateralized microloans.
- Funds immediate lifestyle consumption, dining, or rapidly depreciating consumer electronics.
- Strains monthly liquidity, making it difficult to save or invest for future goals.
""",
    },
    "debt-credit-card-interest.md": {
        "title": "Credit Card Interest Traps and Revolving Debt",
        "topic": "debt_management",
        "language": "en",
        "version": "1.0",
        "content": """# Credit Card Interest Traps and Revolving Debt

Credit cards are convenient payment tools, but carrying an unpaid balance can quickly lead to high-cost revolving debt.

## How Revolving Interest Accumulates
- **The Grace Period:** If you pay your statement balance in full every month, no interest is charged on retail purchases.
- **The Minimum Payment Trap:** Paying only the mandatory minimum (often 5% of the balance) leaves the remaining balance subject to steep annual interest charges (often 20% to 30%+).
- **Loss of Grace Period:** Once a balance rolls over, new purchases begin accruing daily interest immediately from the transaction date.

## Safe Usage Guidelines
- Treat a credit card as a digital debit card; never charge purchases you cannot cover with cash immediately.
- Pay the full statement balance every month before the due date to avoid interest charges and penalty fees.
""",
    },
    "debt-to-income-ratio.md": {
        "title": "Debt-to-Income (DTI) Ratio and Borrowing Limits",
        "topic": "debt_management",
        "language": "en",
        "version": "1.0",
        "content": """# Debt-to-Income (DTI) Ratio and Borrowing Limits

The Debt-to-Income (DTI) ratio is a key metric used by lenders and financial planners to assess an individual's debt burden relative to earnings.

## Calculating DTI

$$\\text{DTI} = \\left(\\frac{\\text{Total Monthly Debt Service}}{\\text{Gross Monthly Income}}\\right) \\times 100$$

Monthly debt service includes personal loan installments, mortgage payments, auto loans, and minimum credit card obligations.

## Evaluating Your Ratio
- **Below 20% (Healthy):** Debt payments are manageable, leaving ample cash flow for living expenses and regular savings.
- **20% to 35% (Moderate):** Borrowing is at a sustainable level, but additional debt should be taken on cautiously.
- **36% to 49% (Elevated):** Debt service consumes a significant share of income, limiting savings and increasing vulnerability to financial shocks.
- **50% and Above (Critical):** Immediate debt restructuring and spending reductions are recommended to regain financial flexibility.
""",
    },
    # 8. Avoiding Impulse Spending
    "impulse-spending-24-hour-rule.md": {
        "title": "The 24-Hour / 30-Day Delay Rule for Impulse Purchases",
        "topic": "spending_habits",
        "language": "en",
        "version": "1.0",
        "content": """# The 24-Hour / 30-Day Delay Rule

Impulse purchases often stem from momentary emotional spikes rather than genuine need. Adding intentional delay breaks this impulse cycle.

## How the Rules Work

### The 24-Hour Rule (Minor Purchases)
When tempted by an unplanned item under a certain threshold (e.g., ৳2,000 to ৳5,000):
- Step away from the checkout screen or physical store.
- Wait a full 24 hours before deciding.
- In most instances, the initial emotional urge fades, making it easy to pass on the purchase.

### The 30-Day Rule (Major Purchases)
For larger discretionary items (e.g., gadgets, designer apparel, luxury furniture):
- Write the item and price on a 30-day wish list.
- If you still view it as a valuable addition to your life after 30 days and have cash on hand, proceed with a clear conscience.
""",
    },
    "impulse-spending-emotional-triggers.md": {
        "title": "Identifying Spending Triggers and Emotional Shopping",
        "topic": "spending_habits",
        "language": "en",
        "version": "1.0",
        "content": """# Identifying Spending Triggers and Emotional Shopping

Emotional spending occurs when money is spent to cope with stress, boredom, social pressure, or fatigue rather than to satisfy practical needs.

## Common Psychological Triggers
- **Stress Relief Shopping:** Buying items as a reward or coping mechanism after a difficult workday.
- **Social Comparison (FOMO):** Purchasing goods, tech upgrades, or dining experiences to match peer lifestyle displays.
- **Boredom Scrolling:** Browsing e-commerce platforms and social media feeds during idle moments, leading to unplanned orders.

## Practical Antidotes
- Recognize your personal emotional triggers and find non-financial alternatives (exercise, hobbies, talking with friends).
- Remove saved credit cards and auto-fill payment profiles from e-commerce apps to introduce friction before checkout.
""",
    },
    "impulse-spending-mfs-friction.md": {
        "title": "Friction in Mobile Financial Services (MFS) Payments",
        "topic": "spending_habits",
        "language": "en",
        "version": "1.0",
        "content": """# Friction in Mobile Financial Services (MFS) Payments

Mobile wallets and QR payments make transactions fast and convenient, but eliminating payment friction can inadvertently increase unplanned spending.

## The Psychology of Painless Digital Money
Physical cash exchanges create sensory feedback: handing over paper notes visually reduces cash in hand, naturally encouraging hesitation. In contrast, tapping a screen or entering an MFS PIN minimizes transaction friction, making spending feel abstract.

## How to Reintroduce Healthy Friction
- Keep daily transactional balances in your MFS wallet low, transferring only what is needed for planned purchases.
- Disable one-click checkouts and biometric instant pay for optional lifestyle apps.
- Establish an agreement with yourself or your partner to discuss discretionary purchases above a certain amount before confirming digital payments.
""",
    },
    "impulse-spending-marketing-nudges.md": {
        "title": "Defending Against Promotional Alerts and Flash Sales",
        "topic": "spending_habits",
        "language": "en",
        "version": "1.0",
        "content": """# Resisting Promotional SMS and Marketing Alerts

Modern retail marketing uses targeted nudges, countdown timers, and promotional discounts designed to trigger artificial urgency.

## Deconstructing Artificial Urgency
Marketing messages frequently use phrases like:
- "Only 2 hours left!"
- "Flash sale: Buy now and save 40%!"

Remember: spending ৳3,000 on an item you did not need simply because it was discounted by 40% does not save you ৳2,000—it costs you ৳3,000.

## Defensive Habits
- Unsubscribe from promotional email lists and marketing SMS feeds.
- Mute promotional app notifications during evenings and weekends.
- Shop with a predefined, written shopping list and stick to it strictly.
""",
    },
    "impulse-spending-needs-vs-wants.md": {
        "title": "Distinguishing Needs vs. Wants in Practice",
        "topic": "spending_habits",
        "language": "en",
        "version": "1.0",
        "content": """# Distinguishing Needs vs. Wants in Practice

Telling the difference between needs and wants can be challenging when lifestyle upgrades feel essential over time.

## The Clarifying Framework
- **Need:** An item or service required for basic health, safety, shelter, or primary employment. Without it, your livelihood or wellbeing is impaired.
- **Want:** An upgrade, convenience, or luxury that enhances comfort but is not essential for daily functioning.

## The Upgrade Test
Are you paying for basic utility or the premium version of a product?
- Basic transport to work is a **need**; premium rideshare services every day are a **want**.
- Nutrient-rich groceries for home-cooked meals are a **need**; frequent dining out and gourmet food delivery are **wants**.

Recognizing upgrades helps you identify practical places to trim spending without compromising basic quality of life.
""",
    },
    # 9. Reading the App's Dashboard & Metrics
    "app-dashboard-reading-kpis.md": {
        "title": "Understanding Income vs Expense Tracking on the Dashboard",
        "topic": "app_guide",
        "language": "en",
        "version": "1.0",
        "content": """# How to Read the App's Dashboard Metrics

The Sohoj financial dashboard gives you a consolidated overview of your monthly cash flows, savings progress, and overall financial trajectory.

## Key Performance Indicators (KPIs)

### Net Inflow / Income
The sum of all verified incoming transactions during the calendar month, including salaries, business earnings, and deposits.

### Total Expenses
All recorded outflows, including direct payments and cash-out withdrawals tagged for necessity or discretionary purposes. Transfers between your own accounts are excluded to prevent double-counting.

### Net Savings Surplus
The difference between total monthly income and total expenses:

$$\\text{Surplus} = \\text{Income} - \\text{Expenses}$$

A consistent positive surplus indicates you are spending below your earnings and building financial cushion.
""",
    },
    "app-metrics-savings-rate.md": {
        "title": "Interpreting Your Monthly Savings Rate",
        "topic": "app_guide",
        "language": "en",
        "version": "1.0",
        "content": """# How the App Calculates Savings Rate

The savings rate is one of the clearest indicators of your wealth-building pace, measuring the proportion of income set aside for the future.

## Formula Used in the Platform

$$\\text{Savings Rate} = \\frac{\\text{Total Monthly Savings}}{\\text{Total Monthly Income}}$$

Where total savings includes deliberate goal funding, recurring DPS contributions, and unspent surplus.

## Reading the Indicators
- **Under 10%:** A tight savings margin. Focus on reviewing variable expenses and building a basic emergency buffer.
- **10% to 20%:** A solid baseline that meets standard financial planning guidelines.
- **20% to 35%:** Strong financial discipline that accelerates milestone achievement and long-term security.
- **Above 35%:** Exceptional savings velocity, typical of high earners or low-overhead households.
""",
    },
    "app-metrics-necessity-ratio.md": {
        "title": "Necessity vs. Discretionary Expense Ratios",
        "topic": "app_guide",
        "language": "en",
        "version": "1.0",
        "content": """# Necessity vs Discretionary Expense Breakdown

The Sohoj platform groups your spending into necessity and discretionary categories to help you see where your money goes.

## Metric Definitions

### Necessity Share
The proportion of total expenses directed toward non-negotiable living costs (rent, utilities, groceries, transport, healthcare).

$$\\text{Necessity Share} = \\frac{\\text{Necessity Expenses}}{\\text{Total Expenses}}$$

### Discretionary Share
The proportion of spending directed toward lifestyle choices (dining out, entertainment, shopping, hobby gear).

$$\\text{Discretionary Share} = \\frac{\\text{Discretionary Expenses}}{\\text{Total Expenses}}$$

## How to Use This Data
If your discretionary share trends upward while savings remain flat, review non-essential shopping and dining out to bring allocations back into balance.
""",
    },
    "app-anomalies-guide.md": {
        "title": "What Spending Anomaly Alerts Mean",
        "topic": "app_guide",
        "language": "en",
        "version": "1.0",
        "content": """# What Spending Anomaly Alerts Mean

The platform uses statistical pattern monitoring to highlight unusual transactions or atypical category spending spikes.

## How Anomalies Are Detected
The system monitors your typical spending using median and Median Absolute Deviation (MAD) baselines for each category. An alert is flagged when:
- A single transaction is significantly larger than your historical average in that category.
- Total spending in a category surges well above typical monthly levels.

## Responding to Alerts
- **Confirmed:** You recognize the purchase (e.g., seasonal festival shopping or an annual vehicle repair). Confirming the alert updates your profile context.
- **Dismissed:** If the alert was triggered by an ordinary variation or miscategorized transaction, dismiss it to keep your anomaly feed organized.
""",
    },
    "app-behavior-profiles-guide.md": {
        "title": "Understanding Behavioral Spending Archetypes",
        "topic": "app_guide",
        "language": "en",
        "version": "1.0",
        "content": """# Understanding Behavioral Spending Archetypes

The platform's machine learning model categorizes spending patterns into distinct behavioral profiles to provide personalized financial insights.

## The Six Spending Archetypes
1. **Balanced Spender:** Maintains a steady equilibrium between essential needs, lifestyle desires, and consistent monthly savings.
2. **Consistent Saver:** Prioritizes high savings rates and goal contributions with disciplined control over discretionary spending.
3. **Tight Budgeter:** Operates with high necessity expenses relative to income, leaving a slim margin for variable spending.
4. **Discretionary Spender:** Allocates a notable share of income toward non-essential shopping, leisure, and entertainment.
5. **Cash Dominant Transactor:** Relies heavily on physical cash withdrawals rather than digital transactions.
6. **Volatile Earner:** Manages fluctuating or seasonal earnings that require dynamic cash buffers.

Profiles update periodically as your financial habits evolve over time.
""",
    },
    "app-expense-forecast-guide.md": {
        "title": "Interpreting Next-Month Expense Forecasts",
        "topic": "app_guide",
        "language": "en",
        "version": "1.0",
        "content": """# Interpreting Next-Month Expense Forecasts

The forecasting engine projects expected spending for the upcoming calendar month to help you plan ahead and avoid surprises.

## Understanding Prediction Intervals
Forecasts are presented with three statistical bounds:
- **Expected Point Estimate (p50):** The median projected expense based on your recent spending history and seasonal factors.
- **Lower Bound (p10):** A low-spend scenario where discretionary spending remains minimal.
- **Upper Bound (p90):** A conservative ceiling reflecting potential surges or seasonal peaks.

## Important Disclaimer
Forecasts represent statistical estimates based on historical transaction patterns. They are planning aids, not guaranteed outcomes, and do not account for unforeseen life events or intentional lifestyle changes.
""",
    },
    # 10. App & Mobile Financial Services (MFS) FAQ
    "mfs-tariffs-fees.md": {
        "title": "Mobile Financial Services (MFS) Cash-Out Tariffs and Fees",
        "topic": "mfs_faq",
        "language": "en",
        "version": "1.0",
        "content": """# Mobile Financial Services (MFS) Cash-Out Tariffs and Fees

Using mobile wallets for daily transactions is convenient, but cash-out fees can add up if not monitored carefully.

## Standard Cash-Out Fee Structures
In Bangladesh, MFS platforms (such as bKash, Nagad, and Rocket) apply percentage fees on agent cash withdrawals:
- **Agent Cash-Out:** Typically ranges from 1.49% to 1.85% (approximately ৳14.90 to ৳18.50 per ৳1,000 withdrawn).
- **ATM Cash-Out:** Often carries a lower fee of approximately 0.8% (৳8.00 per ৳1,000) when using affiliated bank ATMs.
- **Direct Merchant QR Payments:** Generally free for consumers when paying retail merchants directly.

## Tips to Minimize Fees
- Pay merchants directly via QR codes or digital transfers rather than withdrawing cash to pay manually.
- Make fewer, planned cash withdrawals rather than frequent small withdrawals to keep transaction fees predictable.
""",
    },
    "mfs-security-privacy.md": {
        "title": "Account Security and PIN Protection for Digital Wallets",
        "topic": "mfs_faq",
        "language": "en",
        "version": "1.0",
        "content": """# Account Security and PIN Protection for Digital Wallets

Securing your mobile financial accounts is essential to prevent unauthorized access and protect your digital savings.

## Fundamental Security Rules
- **Never Share Your PIN or OTP:** Legitimate bank and MFS representatives will never ask for your confidential PIN, password, or One-Time Password (OTP) over phone calls, SMS, or email.
- **Avoid Predictable PINs:** Do not use consecutive numbers (e.g., 1234) or your birth year as your wallet PIN.
- **Enable Biometric App Lock:** Use fingerprint or facial recognition as an extra security layer on your mobile device.
- **Beware of Social Engineering Calls:** Be cautious of callers claiming accidental money transfers or urgent lottery winnings requiring verification codes.
""",
    },
    "app-privacy-and-ai-consent.md": {
        "title": "How Your Data is Protected and How AI Consent Works",
        "topic": "app_faq",
        "language": "en",
        "version": "1.0",
        "content": """# Data Privacy and AI Consent in Sohoj

Sohoj is built with strict privacy controls to keep your personal financial information secure and isolated.

## Row-Level Security and Tenant Isolation
- Your transactions, account balances, and savings goals are protected by database-level Row-Level Security (RLS).
- No other user can view, query, or access your financial records.

## Explicit AI Consent Policy
- Generating AI-driven insights or conversing with the financial assistant requires your explicit opt-in consent (`consent_ai`).
- When enabled, only aggregated figures and relevant context are shared with the assistant.
- Sensitive identifiers like your name, email, and phone number are never included in analytical payloads.
- You can revoke AI consent at any time in your profile settings.
""",
    },
    "app-goals-tracking-faq.md": {
        "title": "Setting and Tracking Financial Goals in the App",
        "topic": "app_faq",
        "language": "en",
        "version": "1.0",
        "content": """# Setting and Tracking Financial Goals in the App

The financial goals feature helps you plan, fund, and track progress toward specific savings milestones.

## Creating a Goal
When creating a new goal, specify:
- **Goal Name:** A clear label (e.g., 'Emergency Buffer', 'Laptop Upgrade', 'Family Vacation').
- **Target Amount:** The total sum required in Taka.
- **Target Date:** Your preferred completion timeline.

## How Progress and ETAs Are Calculated
The platform compares your total saved amount against the target goal:

$$\\text{Progress Percentage} = \\left(\\frac{\\text{Current Amount}}{\\text{Target Amount}}\\right) \\times 100$$

Based on your average monthly savings over the past 3 months, the system estimates a realistic completion timeline (ETA) and assesses whether your pace is on track or requires higher contributions.
""",
    },
    # 11. Glossary
    "glossary-personal-finance.md": {
        "title": "Financial Terms: Liquidity, Asset, Liability, Net Worth",
        "topic": "glossary",
        "language": "en",
        "version": "1.0",
        "content": """# Personal Finance and Banking Terms Glossary

A quick reference glossary of foundational personal finance and banking terms.

## Terms and Definitions

### Asset
Anything of economic value owned by an individual that can be converted into cash or generate future utility. Examples include cash deposits, term investments, real property, and vehicles.

### Liability
A financial obligation or debt owed to another party. Examples include personal loans, mortgages, credit card balances, and unpaid utility bills.

### Net Worth
The total value of all assets minus all outstanding liabilities:

$$\\text{Net Worth} = \\text{Total Assets} - \\text{Total Liabilities}$$

### Liquidity
How quickly and easily an asset can be converted into spendable cash without losing significant value. Cash is completely liquid, whereas real estate is relatively illiquid.

### Principal
The original sum of money lent, borrowed, or invested, before any interest, earnings, or capital gains accrue.

### Yield
The income return on an investment, such as the interest or dividends received from holding a particular security, expressed as an annual percentage.
""",
    },
    "glossary-spending-and-behavior.md": {
        "title": "Spending and Behavioral Terms Glossary",
        "topic": "glossary",
        "language": "en",
        "version": "1.0",
        "content": """# Spending and Behavioral Terms Glossary

Key terms related to consumer behavior, lifestyle spending, and financial habits.

## Terms and Definitions

### Discretionary Expense
Non-essential spending on goods and services that enhance comfort or leisure but are not required for survival or employment.

### Lifestyle Creep (Lifestyle Inflation)
The gradual increase in spending as income rises, where former luxury items become perceived as everyday necessities, often keeping savings rates flat despite higher earnings.

### Sunk Cost Fallacy
The cognitive tendency to continue investing time or money into a commitment simply because of prior resources spent, even when cutting losses is the more sensible choice.

### Sinking Fund
Money set aside in regular installments to cover a known, planned future expense (e.g., annual insurance premiums or home repairs), distinct from an emergency fund.

### Opportunity Cost
The potential benefit or return forgone when choosing one financial decision over another (e.g., spending cash today versus investing it for long-term compound growth).
""",
    },
}


def generate_all_documents() -> int:
    """Write all 52 educational documents to rag/documents/."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for filename, doc in DOCUMENTS.items():
        filepath = DOCS_DIR / filename
        frontmatter = (
            f"---\n"
            f'title: "{doc["title"]}"\n'
            f'topic: "{doc["topic"]}"\n'
            f'language: "{doc["language"]}"\n'
            f'version: "{doc["version"]}"\n'
            f"---\n\n"
        )
        content = frontmatter + doc["content"].strip() + "\n"
        filepath.write_text(content, encoding="utf-8")
        count += 1
    return count


if __name__ == "__main__":
    written = generate_all_documents()
    print(f"Successfully generated {written} documents in {DOCS_DIR}")
