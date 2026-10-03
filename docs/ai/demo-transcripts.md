# Sohoj Conversational AI Coach — Demo Transcripts

This document showcases realistic end-to-end conversation transcripts across **5 synthetic user personas** in the Sohoj ecosystem, exercising tool orchestration, deterministic financial engine computations, Server-Sent Events (SSE) events, and safety guardrails.

---

## Persona 1: Tariqul Islam (Disciplined Saver)

* **Profile Archetype**: `disciplined_saver` (Confidence: 0.94)  
* **Monthly Income**: ৳75,000 | **Average Expense**: ৳42,000 | **Savings Rate**: 44.0%  
* **Active Goal**: ৳500,000 Down Payment (Current: ৳280,000)  

### Dialogue 1: Long-term Compound Growth & Doubling Projections

**User:**
> "I have ৳200,000 in a fixed deposit earning 8.5% annual return. How long until it doubles, and what will it grow to if I also add ৳15,000 every month for 5 years?"

**SSE Event Stream:**
```
event: tool_status
data: {"tool": "calculate_doubling_time", "status": "completed", "call_index": 1}

event: tool_status
data: {"tool": "calculate_future_value", "status": "completed", "call_index": 2}

event: token
data: {"text": "Based on verified financial"}

event: token
data: {"text": " calculations for your 8.5%"}

event: token
data: {"text": " annual return fixed deposit:\n\n"}

event: token
data: {"text": "1. **Doubling Time**: At 8.5% annual compounding, your ৳200,000 deposit will double in approximately **8.49 years** (about 8 years and 6 months).\n\n"}

event: token
data: {"text": "2. **5-Year Growth**: If you keep the ৳200,000 principal and contribute ৳15,000 monthly for 5 years, your projected future value will be **৳1,422,946** (consisting of ৳1,100,000 total contributions and ৳322,946 total investment growth)."}

event: ui_action
data: {"ui_action": "open_growth_simulator", "payload": {"principal": 200000.0, "monthly": 15000.0, "rate": 8.5, "years": 5}}

event: done
data: {"message_id": "8d94b0f2-70b9-4672-91f8-95df2b881a20", "tokens_in": 142, "tokens_out": 195, "latency_ms": 28, "prompt_version": "v1.0.0", "is_fallback": false, "is_grounded": true}
```

**Final Validated Response Rendered to User:**
> Based on verified financial calculations for your 8.5% annual return fixed deposit:
> 
> 1. **Doubling Time**: At 8.5% annual compounding, your ৳200,000 deposit will double in approximately **8.49 years** (about 8 years and 6 months).
> 2. **5-Year Growth**: If you keep the ৳200,000 principal and contribute ৳15,000 monthly for 5 years, your projected future value will be **৳1,422,946** (consisting of ৳1,100,000 total contributions and ৳322,946 total investment growth).
> 
> *Disclaimer: Projections are illustrative estimates based on stated assumptions and are not guaranteed. Sohoj does not provide licensed investment or tax advice.*

---

## Persona 2: Shamima Akhter (Impulsive Spender)

* **Profile Archetype**: `impulsive_spender` (Confidence: 0.89)  
* **Monthly Income**: ৳45,000 | **Recent Expense**: ৳41,500 | **Unallocated Surplus**: ৳3,500  
* **Flagged Anomalies**: ৳12,000 apparel purchase at Jamuna Future Park  

### Dialogue 2: Affordability Check for an Impulsive Gadget Purchase

**User:**
> "Can I afford to buy a ৳9,500 smartwatch on sale today?"

**SSE Event Stream:**
```
event: tool_status
data: {"tool": "check_affordability", "status": "completed", "call_index": 1}

event: token
data: {"text": "Based on your current month"}

event: token
data: {"text": " finances, purchasing a ৳9,500"}

event: token
data: {"text": " smartwatch is **not recommended** right now.\n\n"}

event: token
data: {"text": "• **Current Monthly Surplus**: ৳3,500\n"}

event: token
data: {"text": "• **Shortfall**: Buying this smartwatch today would exceed your available surplus by **৳6,000**, which would force you to dip into emergency reserves.\n\n"}

event: token
data: {"text": "💡 **Alternative Suggestion**: If you set up a dedicated short-term goal of saving **৳3,167 per month**, you can purchase the smartwatch debt-free in 3 months."}

event: ui_action
data: {"ui_action": "open_goal_wizard", "payload": {"target_amount": 9500.0, "time_horizon_months": 3, "category": "electronics"}}

event: done
data: {"message_id": "f519c29e-a612-4d7a-8bfe-ec5a917e8891", "tokens_in": 128, "tokens_out": 174, "latency_ms": 22, "prompt_version": "v1.0.0", "is_fallback": false, "is_grounded": true}
```

**Final Validated Response Rendered to User:**
> Based on your current month finances, purchasing a ৳9,500 smartwatch is **not recommended** right now.
> 
> • **Current Monthly Surplus**: ৳3,500  
> • **Shortfall**: Buying this smartwatch today would exceed your available surplus by **৳6,000**, which would force you to dip into emergency reserves.  
> 
> 💡 **Alternative Suggestion**: If you set up a dedicated short-term goal of saving **৳3,167 per month**, you can purchase the smartwatch debt-free in 3 months.

---

## Persona 3: Farhan Kabir (Living Paycheck to Paycheck)

* **Profile Archetype**: `paycheck_to_paycheck` (Confidence: 0.91)  
* **Monthly Income**: ৳28,000 | **Necessity Ratio**: 89.0% | **Savings Rate**: 5.2%  
* **Context**: Vulnerable to unexpected medical or transit spikes  

### Dialogue 3: Building a Starter Emergency Fund

**User:**
> "I have almost nothing left at the end of the month. How can I possibly build an emergency fund on a ৳28,000 salary?"

**SSE Event Stream:**
```
event: tool_status
data: {"tool": "search_knowledge", "status": "completed", "call_index": 1}

event: tool_status
data: {"tool": "calculate_goal_plan", "status": "completed", "call_index": 2}

event: token
data: {"text": "Building emergency security on"}

event: token
data: {"text": " a tight budget is about"}

event: token
data: {"text": " small, consistent habits rather than"}

event: token
data: {"text": " large lump sums.\n\n"}

event: token
data: {"text": "1. **Start with a Mini Buffer**: Rather than aiming for 6 months immediately, aim for a **৳15,000 starter emergency fund**.\n"}

event: token
data: {"text": "2. **Micro-Savings Plan**: By setting aside **৳1,250 monthly** (about ৳40 per day, roughly 4.5% of your ৳28,000 income), you will achieve your ৳15,000 buffer in 12 months.\n"}

event: token
data: {"text": "3. **Automation**: Transfer this ৳1,250 on the day your salary arrives into a separate mobile wallet or DPS so it isn't absorbed by daily necessities."}

event: ui_action
data: {"ui_action": "open_goal_wizard", "payload": {"target_amount": 15000.0, "time_horizon_months": 12, "name": "Starter Emergency Fund"}}

event: done
data: {"message_id": "3b29c92a-8742-4911-9a7c-3b98c3658249", "tokens_in": 160, "tokens_out": 210, "latency_ms": 31, "prompt_version": "v1.0.0", "is_fallback": false, "is_grounded": true}
```

**Final Validated Response Rendered to User:**
> Building emergency security on a tight budget is about small, consistent habits rather than large lump sums.
> 
> 1. **Start with a Mini Buffer**: Rather than aiming for 6 months immediately, aim for a **৳15,000 starter emergency fund**.
> 2. **Micro-Savings Plan**: By setting aside **৳1,250 monthly** (about ৳40 per day, roughly 4.5% of your ৳28,000 income), you will achieve your ৳15,000 buffer in 12 months.
> 3. **Automation**: Transfer this ৳1,250 on the day your salary arrives into a separate mobile wallet or DPS so it isn't absorbed by daily necessities.

---

## Persona 4: Nusrat Jahan (Goal Builder)

* **Profile Archetype**: `goal_builder` (Confidence: 0.93)  
* **Monthly Income**: ৳60,000 | **Monthly Savings**: ৳18,000  
* **Target Milestone**: ৳120,000 Laptop in 8 Months  

### Dialogue 4: Milestone Feasibility & Trailing Savings Alignment

**User:**
> "I want to buy a ৳120,000 development laptop in 8 months. Can my current savings rate handle it, and what should my monthly target be?"

**SSE Event Stream:**
```
event: tool_status
data: {"tool": "calculate_goal_plan", "status": "completed", "call_index": 1}

event: tool_status
data: {"tool": "get_monthly_summary", "status": "completed", "call_index": 2}

event: token
data: {"text": "Great news! Your goal is"}

event: token
data: {"text": " **highly feasible** with your current"}

event: token
data: {"text": " savings discipline:\n\n"}

event: token
data: {"text": "• **Required Monthly Saving**: **৳15,000** for 8 months to reach ৳120,000.\n"}

event: token
data: {"text": "• **Current Monthly Savings**: You are currently saving **৳18,000** monthly (a 30.0% savings rate on your ৳60,000 income).\n"}

event: token
data: {"text": "• **Surplus Remaining**: Even after allocating ৳15,000 to this laptop goal, you retain **৳3,000** monthly for other savings and emergencies."}

event: ui_action
data: {"ui_action": "open_goal_wizard", "payload": {"target_amount": 120000.0, "time_horizon_months": 8, "name": "Work Laptop"}}

event: done
data: {"message_id": "c830a7d2-7e11-4560-b0cf-5a3d420a823b", "tokens_in": 154, "tokens_out": 192, "latency_ms": 25, "prompt_version": "v1.0.0", "is_fallback": false, "is_grounded": true}
```

**Final Validated Response Rendered to User:**
> Great news! Your goal is **highly feasible** with your current savings discipline:
> 
> • **Required Monthly Saving**: **৳15,000** for 8 months to reach ৳120,000.  
> • **Current Monthly Savings**: You are currently saving **৳18,000** monthly (a 30.0% savings rate on your ৳60,000 income).  
> • **Surplus Remaining**: Even after allocating ৳15,000 to this laptop goal, you retain **৳3,000** monthly for other savings and emergencies.

---

## Persona 5: Kamal Hossain (Cold-Start / New User)

* **Profile Archetype**: `insufficient_data` (Confidence: 0.0)  
* **Account Age**: 2 days | **Logged Transactions**: 2 transactions totaling ৳850  

### Dialogue 5: Onboarding Guidance & Cold-Start Explanations

**User:**
> "Why is my spending behavior profile saying 'insufficient data', and what should I do first?"

**SSE Event Stream:**
```
event: tool_status
data: {"tool": "get_behavior_profile", "status": "completed", "call_index": 1}

event: tool_status
data: {"tool": "search_knowledge", "status": "completed", "call_index": 2}

event: token
data: {"text": "Welcome to Sohoj! Your account"}

event: token
data: {"text": " currently displays 'insufficient_data'"}

event: token
data: {"text": " because our behavioral machine learning"}

event: token
data: {"text": " models require at least **2 consecutive calendar months** of transaction history to detect reliable spending patterns.\n\n"}

event: token
data: {"text": "Here is how to get the most out of Sohoj right away:\n\n"}

event: token
data: {"text": "1. **Log Your Daily Expenses**: Record your groceries, rent, transit, and mobile recharges as they happen.\n"}

event: token
data: {"text": "2. **Apply the 50/30/20 Rule**: As a starting benchmark, aim to keep needs under 50%, discretionary wants under 30%, and save at least 20%.\n"}

event: token
data: {"text": "3. **Deterministic Tools are Ready**: Even without ML history, you can already use our **Goal Planner** and **Financial Growth Simulators**."}

event: ui_action
data: {"ui_action": "view_monthly_breakdown", "payload": {"prompt": "log_first_month_expenses"}}

event: done
data: {"message_id": "71a2e998-3f41-4712-ba78-654e58b88d2f", "tokens_in": 138, "tokens_out": 220, "latency_ms": 29, "prompt_version": "v1.0.0", "is_fallback": false, "is_grounded": true}
```

**Final Validated Response Rendered to User:**
> Welcome to Sohoj! Your account currently displays 'insufficient_data' because our behavioral machine learning models require at least **2 consecutive calendar months** of transaction history to detect reliable spending patterns.
> 
> Here is how to get the most out of Sohoj right away:
> 
> 1. **Log Your Daily Expenses**: Record your groceries, rent, transit, and mobile recharges as they happen.
> 2. **Apply the 50/30/20 Rule**: As a starting benchmark, aim to keep needs under 50%, discretionary wants under 30%, and save at least 20%.
> 3. **Deterministic Tools are Ready**: Even without ML history, you can already use our **Goal Planner** and **Financial Growth Simulators**.

---

## 6. Verification Summary

All transcripts above have been verified to satisfy:
1. **Protocol Compliance**: Each turn emits SSE events in strict order (`tool_status*` $\to$ `token*` $\to$ `ui_action?` $\to$ `done`).
2. **Deterministic Grounding**: Every numerical figure ($৳1,422,946$, $8.49\text{ years}$, $৳3,500$, $৳6,000$, etc.) matches exact output values from `FinancialEngine`.
3. **Regulatory Safety**: Unprompted projection disclaimers accompany compound calculations.
4. **Zero 5xx Guarantee**: If any upstream error or budget exhaustion occurs, the conversation manager degrades to verified static guidance without server error.
