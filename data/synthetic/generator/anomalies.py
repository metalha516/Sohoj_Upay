"""Anomaly injection engine for ground-truth behavioral and transaction anomalies."""

import uuid
from dataclasses import dataclass
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

import numpy as np

from data.synthetic.generator.income import RawEvent
from data.synthetic.generator.population import SyntheticUser


@dataclass
class AnomalyGroundTruth:
    anomaly_id: uuid.UUID
    event_id: uuid.UUID
    user_id: uuid.UUID
    anomaly_type: str
    severity_score: Decimal
    description: str


class AnomalyInjector:
    """Injects calibrated 2.0% - 3.0% labeled anomalies into transaction streams."""

    def __init__(self, target_rate: float = 0.025, seed: int = 42) -> None:
        self.target_rate = target_rate
        self.rng = np.random.default_rng(seed)

    def _make_uuid(self) -> uuid.UUID:
        return uuid.UUID(bytes=bytes(self.rng.bytes(16)))

    def inject_anomalies(
        self, user: SyntheticUser, events: list[RawEvent]
    ) -> tuple[list[RawEvent], list[AnomalyGroundTruth]]:
        """Select a subset of events to transform or inject as ground-truth anomalies."""
        anomalies_gt: list[AnomalyGroundTruth] = []
        modified_events: list[RawEvent] = []

        # Target anomaly count ~ 2.5% of events
        num_target = max(1, int(len(events) * self.target_rate))
        chosen_indices = set(
            self.rng.choice(len(events), size=min(len(events), num_target), replace=False)
        )

        anomaly_types = [
            "category_spike",
            "burst_frequency",
            "unusual_cash_out",
            "odd_hour_activity",
        ]
        type_probs = [0.40, 0.25, 0.20, 0.15]

        for idx, ev in enumerate(events):
            if idx in chosen_indices and ev.txn_type in ("expense", "cash_out"):
                a_type = str(self.rng.choice(anomaly_types, p=type_probs))

                if a_type == "category_spike":
                    multiplier = float(self.rng.uniform(3.0, 5.5))
                    new_amt = (ev.amount * Decimal(str(round(multiplier, 2)))).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    ev.amount = new_amt
                    ev.is_anomaly = True
                    ev.anomaly_type = a_type
                    ev.description = f"{ev.description} (Unusual Spending Spike)"
                    anomalies_gt.append(
                        AnomalyGroundTruth(
                            anomaly_id=self._make_uuid(),
                            event_id=ev.event_id,
                            user_id=user.user_id,
                            anomaly_type=a_type,
                            severity_score=Decimal(str(round(multiplier / 6.0, 2))),
                            description=f"Transaction amount ৳{new_amt} is {multiplier:.1f}x higher than baseline {ev.category} spend",
                        )
                    )
                    modified_events.append(ev)

                elif a_type == "burst_frequency":
                    # Emit current event plus 3-5 rapid micro-transactions
                    ev.is_anomaly = True
                    ev.anomaly_type = a_type
                    modified_events.append(ev)
                    anomalies_gt.append(
                        AnomalyGroundTruth(
                            anomaly_id=self._make_uuid(),
                            event_id=ev.event_id,
                            user_id=user.user_id,
                            anomaly_type=a_type,
                            severity_score=Decimal("0.85"),
                            description="Rapid high-frequency transaction burst within 20 minutes",
                        )
                    )

                    burst_count = int(self.rng.integers(3, 6))
                    for b_i in range(burst_count):
                        b_ts = ev.ts + timedelta(minutes=int((b_i + 1) * 3))
                        b_amt = Decimal(str(self.rng.choice([20, 30, 50, 100]))).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                        b_ev = RawEvent(
                            event_id=self._make_uuid(),
                            user_id=user.user_id,
                            ts=b_ts,
                            txn_type="expense",
                            category="mobile_recharge",
                            purpose="necessity",
                            amount=b_amt,
                            fee=Decimal("0.00"),
                            description="Rapid Burst Mobile Recharge",
                            merchant="MFS Flexiload Gateway",
                            is_anomaly=True,
                            anomaly_type="burst_frequency",
                        )
                        modified_events.append(b_ev)
                        anomalies_gt.append(
                            AnomalyGroundTruth(
                                anomaly_id=self._make_uuid(),
                                event_id=b_ev.event_id,
                                user_id=user.user_id,
                                anomaly_type="burst_frequency",
                                severity_score=Decimal("0.85"),
                                description="Part of rapid high-frequency transaction burst cluster",
                            )
                        )

                elif a_type == "unusual_cash_out":
                    ev.txn_type = "cash_out"
                    ev.category = "cash_out"
                    large_co = max(Decimal("5000.00"), ev.amount * Decimal("3.0"))
                    ev.amount = large_co.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    ev.fee = (ev.amount * Decimal("0.0185")).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    ev.is_anomaly = True
                    ev.anomaly_type = a_type
                    ev.description = "Unusually Large Agent Cash-Out"
                    anomalies_gt.append(
                        AnomalyGroundTruth(
                            anomaly_id=self._make_uuid(),
                            event_id=ev.event_id,
                            user_id=user.user_id,
                            anomaly_type=a_type,
                            severity_score=Decimal("0.90"),
                            description=f"Sudden abnormal cash-out of ৳{ev.amount} exceeding 85% of average balance",
                        )
                    )
                    modified_events.append(ev)

                elif a_type == "odd_hour_activity":
                    # Shift transaction time to 2:15 AM - 4:20 AM
                    odd_hour = int(self.rng.choice([2, 3]))
                    odd_minute = int(self.rng.integers(10, 50))
                    ev.ts = ev.ts.replace(hour=odd_hour, minute=odd_minute)
                    ev.is_anomaly = True
                    ev.anomaly_type = a_type
                    anomalies_gt.append(
                        AnomalyGroundTruth(
                            anomaly_id=self._make_uuid(),
                            event_id=ev.event_id,
                            user_id=user.user_id,
                            anomaly_type=a_type,
                            severity_score=Decimal("0.75"),
                            description=f"Odd-hour transaction activity recorded at {ev.ts.strftime('%I:%M %p')}",
                        )
                    )
                    modified_events.append(ev)

            else:
                modified_events.append(ev)

        return modified_events, anomalies_gt
