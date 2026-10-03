"""Master orchestration engine for synthetic financial data generation."""

import time
from dataclasses import dataclass
from pathlib import Path

from data.synthetic.generator.anomalies import AnomalyGroundTruth, AnomalyInjector
from data.synthetic.generator.behavior import SpendingBehaviorEngine
from data.synthetic.generator.calendar import DhakaCalendar
from data.synthetic.generator.income import IncomeGenerator
from data.synthetic.generator.life_events import LifeEventGenerator
from data.synthetic.generator.population import PopulationGenerator, SyntheticUser
from data.synthetic.generator.wallet import SimulationResult, WalletSimulator


@dataclass
class GenerationReport:
    total_users: int
    total_transactions: int
    total_goals: int
    total_contributions: int
    total_anomalies: int
    anomaly_rate: float
    elapsed_seconds: float
    invariant_failures: int
    persona_counts: dict[str, int]
    occupation_counts: dict[str, int]
    type_counts: dict[str, int]


class SyntheticDataOrchestrator:
    """Orchestrates multi-module generation of Bangladeshi MFS user lifetimes."""

    def __init__(self, config_dir: Path | None = None, seed: int = 42) -> None:
        if config_dir is None:
            config_dir = Path("data/synthetic/config")
        self.config_dir = config_dir
        self.seed = seed

        self.calendar = DhakaCalendar(config_dir / "calendar.yaml")
        self.pop_gen = PopulationGenerator(config_dir, seed=seed)
        self.inc_gen = IncomeGenerator(self.calendar, seed=seed + 1)
        self.life_gen = LifeEventGenerator(self.calendar, seed=seed + 2)
        self.spend_engine = SpendingBehaviorEngine(self.calendar, seed=seed + 3)
        self.anomaly_injector = AnomalyInjector(target_rate=0.016, seed=seed + 4)
        self.wallet_sim = WalletSimulator()

    def generate(
        self, num_users: int = 600
    ) -> tuple[
        list[SyntheticUser], list[SimulationResult], list[AnomalyGroundTruth], GenerationReport
    ]:
        """Run the end-to-end generation pipeline."""
        start_time = time.perf_counter()

        # 1. Generate Population
        users = self.pop_gen.generate_users(num_users)

        all_results: list[SimulationResult] = []
        all_anomalies: list[AnomalyGroundTruth] = []
        invariant_failures = 0

        persona_counts: dict[str, int] = {}
        occupation_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}

        for user in users:
            persona_counts[user.persona] = persona_counts.get(user.persona, 0) + 1
            occupation_counts[user.occupation] = occupation_counts.get(user.occupation, 0) + 1

            # 2. Incomes
            inc_events = self.inc_gen.generate_user_income(user)

            # 3. Life Events
            life_events, shock_events = self.life_gen.generate_user_life_events(user)

            # 4. Spending
            spend_events = self.spend_engine.generate_user_spending(user, inc_events)

            # 5. Combine and Inject Anomalies
            combined_events = inc_events + shock_events + spend_events
            modified_events, user_anomalies = self.anomaly_injector.inject_anomalies(
                user, combined_events
            )
            all_anomalies.extend(user_anomalies)

            # 6. Wallet Chronological Simulation & Solvency Guarantee
            sim_res = self.wallet_sim.simulate_user_wallet(user, modified_events)
            all_results.append(sim_res)

            if not sim_res.invariant_passed:
                invariant_failures += 1

            for t in sim_res.transactions:
                type_counts[t.txn_type] = type_counts.get(t.txn_type, 0) + 1

        elapsed = time.perf_counter() - start_time

        total_txns = sum(len(r.transactions) for r in all_results)
        total_goals = sum(len(u.goals) for u in users)
        total_contribs = sum(len(r.goal_contributions) for r in all_results)
        anomaly_rate = (len(all_anomalies) / total_txns) if total_txns > 0 else 0.0

        report = GenerationReport(
            total_users=len(users),
            total_transactions=total_txns,
            total_goals=total_goals,
            total_contributions=total_contribs,
            total_anomalies=len(all_anomalies),
            anomaly_rate=round(anomaly_rate, 4),
            elapsed_seconds=round(elapsed, 2),
            invariant_failures=invariant_failures,
            persona_counts=persona_counts,
            occupation_counts=occupation_counts,
            type_counts=type_counts,
        )

        return users, all_results, all_anomalies, report
