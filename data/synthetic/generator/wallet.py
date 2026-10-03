"""Wallet balance simulation engine enforcing non-negative balances and accounting invariants."""

import uuid
from dataclasses import dataclass
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from data.synthetic.generator.income import RawEvent
from data.synthetic.generator.population import SyntheticUser


@dataclass
class FinalTransaction:
    transaction_id: uuid.UUID
    user_id: uuid.UUID
    ts: str  # ISO string
    txn_type: str
    purpose: str | None
    category: str
    amount: Decimal
    fee: Decimal
    balance_after: Decimal
    idempotency_key: str
    description: str
    merchant: str | None
    goal_id: uuid.UUID | None
    is_anomaly: bool
    anomaly_type: str | None


@dataclass
class SimulationResult:
    user_id: uuid.UUID
    starting_balance: Decimal
    final_balance: Decimal
    total_inflows: Decimal
    total_outflows: Decimal
    transactions: list[FinalTransaction]
    goal_contributions: list[dict[str, object]]
    invariant_passed: bool


class WalletSimulator:
    """Chronologically processes user events, ensures solvency, and verifies wallet invariants."""

    def simulate_user_wallet(
        self, user: SyntheticUser, raw_events: list[RawEvent]
    ) -> SimulationResult:
        """Process all events chronologically, adjusting amounts to never allow negative balances."""
        # Sort all incoming raw events chronologically
        events = sorted(raw_events, key=lambda e: e.ts)

        running_balance = user.starting_balance
        final_txns: list[FinalTransaction] = []
        goal_contributions: list[dict[str, object]] = []

        total_inflows = Decimal("0.00")
        total_outflows = Decimal("0.00")

        # Map goal_id to SyntheticGoal for updating current_amount
        goal_map = {g.goal_id: g for g in user.goals}

        for ev in events:
            # -------------------------------------------------------------
            # 1. Inflow Events (income, cash_in)
            # -------------------------------------------------------------
            if ev.txn_type in ("income", "cash_in"):
                running_balance += ev.amount
                total_inflows += ev.amount

                final_txns.append(
                    FinalTransaction(
                        transaction_id=ev.event_id,
                        user_id=ev.user_id,
                        ts=ev.ts.isoformat(),
                        txn_type=ev.txn_type,
                        purpose=ev.purpose,
                        category=ev.category,
                        amount=ev.amount,
                        fee=ev.fee,
                        balance_after=running_balance,
                        idempotency_key=f"syn_{ev.event_id.hex}",
                        description=ev.description,
                        merchant=ev.merchant,
                        goal_id=ev.goal_id,
                        is_anomaly=ev.is_anomaly,
                        anomaly_type=ev.anomaly_type,
                    )
                )

            # -------------------------------------------------------------
            # 2. Outflow Events (expense, cash_out, transfer)
            # -------------------------------------------------------------
            else:
                outflow_amt = ev.amount

                # Check if running balance is insufficient
                if running_balance < outflow_amt:
                    # For elective/discretionary spending or transfers: shrink or skip
                    if ev.purpose == "discretionary" or ev.category in (
                        "dining",
                        "shopping",
                        "savings_deposit",
                    ):
                        if running_balance >= Decimal("50.00"):
                            # Shrink expenditure to fit available balance
                            outflow_amt = (running_balance * Decimal("0.85")).quantize(
                                Decimal("0.01"), rounding=ROUND_HALF_UP
                            )
                            if outflow_amt < Decimal("20.00"):
                                continue  # Skip if too trivial
                        else:
                            # Skip transaction - user has insufficient funds for discretionary spend
                            continue
                    else:
                        # For mandatory necessities (rent, utility bill, medical, required cash-out):
                        # Realistic user behavior: "Add Money" / Cash-In from bank or agent
                        shortfall = outflow_amt - running_balance
                        # Round up shortfall to next ৳500
                        topup_num = int((shortfall / Decimal("500.00")).to_integral_value()) + 1
                        topup_amt = (Decimal(str(topup_num)) * Decimal("500.00")).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )

                        # Insert a cash_in event 45 seconds prior to the outflow
                        topup_ts = ev.ts - timedelta(seconds=45)
                        running_balance += topup_amt
                        total_inflows += topup_amt

                        topup_id = uuid.uuid5(
                            user.user_id, f"topup_{ev.event_id}_{len(final_txns)}"
                        )
                        final_txns.append(
                            FinalTransaction(
                                transaction_id=topup_id,
                                user_id=ev.user_id,
                                ts=topup_ts.isoformat(),
                                txn_type="cash_in",
                                purpose="necessity",
                                category="cash_in_self",
                                amount=topup_amt,
                                fee=Decimal("0.00"),
                                balance_after=running_balance,
                                idempotency_key=f"syn_topup_{topup_id.hex[:12]}",
                                description="Bank to MFS Add Money (Wallet Top-up)",
                                merchant="Bangladesh Bank NPSB Gateway",
                                goal_id=None,
                                is_anomaly=False,
                                anomaly_type=None,
                            )
                        )

                # Process outflow
                running_balance -= outflow_amt
                total_outflows += outflow_amt

                final_txns.append(
                    FinalTransaction(
                        transaction_id=ev.event_id,
                        user_id=ev.user_id,
                        ts=ev.ts.isoformat(),
                        txn_type=ev.txn_type,
                        purpose=ev.purpose,
                        category=ev.category,
                        amount=outflow_amt,
                        fee=ev.fee,
                        balance_after=running_balance,
                        idempotency_key=f"syn_{ev.event_id.hex}",
                        description=ev.description,
                        merchant=ev.merchant,
                        goal_id=ev.goal_id,
                        is_anomaly=ev.is_anomaly,
                        anomaly_type=ev.anomaly_type,
                    )
                )

                # If this was a goal contribution, track it
                if ev.txn_type == "transfer" and ev.goal_id and ev.goal_id in goal_map:
                    goal = goal_map[ev.goal_id]
                    goal.current_amount += outflow_amt
                    contrib_id = uuid.uuid5(
                        user.user_id, f"contrib_{ev.event_id}_{len(goal_contributions)}"
                    )
                    goal_contributions.append(
                        {
                            "contribution_id": str(contrib_id),
                            "goal_id": str(ev.goal_id),
                            "user_id": str(user.user_id),
                            "amount": str(outflow_amt),
                            "created_at": ev.ts.isoformat(),
                        }
                    )

        # Mathematical Invariant Check:
        # Starting Balance + Total Inflows - Total Outflows == Final Balance
        expected_final = user.starting_balance + total_inflows - total_outflows
        diff = abs(running_balance - expected_final)
        invariant_passed = bool(diff < Decimal("0.001")) and (running_balance >= Decimal("0.00"))

        return SimulationResult(
            user_id=user.user_id,
            starting_balance=user.starting_balance,
            final_balance=running_balance,
            total_inflows=total_inflows,
            total_outflows=total_outflows,
            transactions=final_txns,
            goal_contributions=goal_contributions,
            invariant_passed=invariant_passed,
        )
