"""Unit and property tests for the synthetic data generator."""

from datetime import date
from decimal import Decimal

from data.synthetic.generator.calendar import DhakaCalendar
from data.synthetic.generator.engine import SyntheticDataOrchestrator
from data.synthetic.generator.population import PopulationGenerator


def test_dhaka_calendar_logic() -> None:
    """Verify Bangladeshi weekends, festivals, and category multipliers."""
    cal = DhakaCalendar()

    # 1. Weekends: Friday and Saturday
    friday = date(2026, 1, 2)  # Jan 2, 2026 is Friday
    saturday = date(2026, 1, 3)
    sunday = date(2026, 1, 4)
    assert cal.is_weekend(friday) is True
    assert cal.is_weekend(saturday) is True
    assert cal.is_weekend(sunday) is False

    # 2. Ramadan 2026
    ramadan_date = date(2026, 3, 5)
    assert cal.is_ramadan(ramadan_date) is True
    assert cal.is_ramadan(date(2026, 1, 15)) is False

    # 3. Pre-Eid Shopping Rush
    pre_eid = date(2026, 3, 10)
    assert cal.is_eid_ul_fitr_shopping(pre_eid) is True
    mult_shop = cal.get_category_multiplier("shopping", pre_eid)
    assert mult_shop > Decimal("2.00")

    # 4. Pohela Boishakh
    boishakh = date(2026, 4, 14)
    assert cal.is_pohela_boishakh(boishakh) is True


def test_population_generator_demographics() -> None:
    """Verify demographics, names, emails, phones, and income bounds."""
    pop_gen = PopulationGenerator(seed=101)
    users = pop_gen.generate_users(n=50)

    assert len(users) == 50

    drifting_count = sum(1 for u in users if u.is_drifting)
    # Roughly 10% drifting
    assert 1 <= drifting_count <= 15

    for u in users:
        # Check name has at least 2 parts
        assert len(u.full_name.split()) >= 2
        # Check safe test email domain
        assert u.email.endswith("@example.test")
        # Check BD MFS operator prefix
        assert any(
            u.phone.startswith(pfx)
            for pfx in ["+88017", "+88018", "+88019", "+88013", "+88014", "+88015", "+88016"]
        )
        # Check baseline income and starting balance
        assert u.baseline_income > Decimal("0.00")
        assert u.starting_balance >= Decimal("200.00")


def test_wallet_invariants_and_solvency_property_test() -> None:
    """Property test: 100% of users must satisfy start + inflows - outflows = final_balance and never negative."""
    orchestrator = SyntheticDataOrchestrator(seed=202)
    users, sim_results, _, report = orchestrator.generate(num_users=25)

    assert report.invariant_failures == 0
    assert len(sim_results) == 25

    for res in sim_results:
        assert res.invariant_passed is True
        # Property: start + inflows - outflows == final
        expected = res.starting_balance + res.total_inflows - res.total_outflows
        assert abs(res.final_balance - expected) < Decimal("0.001")
        # Property: final balance non-negative
        assert res.final_balance >= Decimal("0.00")

        # Property: every single transaction balance_after is non-negative
        for txn in res.transactions:
            assert txn.balance_after >= Decimal("0.00")
            assert txn.amount > Decimal("0.00")
            if txn.txn_type in ("expense", "cash_out"):
                assert txn.purpose is not None


def test_anomaly_injection_rate() -> None:
    """Verify that anomaly injection rate stays within 2.0% - 3.0% of total transactions."""
    orchestrator = SyntheticDataOrchestrator(seed=303)
    _, _, all_anomalies, report = orchestrator.generate(num_users=20)

    assert 0.018 <= report.anomaly_rate <= 0.035
    assert len(all_anomalies) == report.total_anomalies


def test_determinism_same_seed_identical_output() -> None:
    """Verify that identical seeds produce identical transaction streams, hashes, and amounts."""
    orch1 = SyntheticDataOrchestrator(seed=777)
    users1, res1, _, rep1 = orch1.generate(num_users=5)

    orch2 = SyntheticDataOrchestrator(seed=777)
    users2, res2, _, rep2 = orch2.generate(num_users=5)

    # Identical counts
    assert rep1.total_transactions == rep2.total_transactions
    assert rep1.total_anomalies == rep2.total_anomalies

    # Identical user IDs and balances
    for u1, u2 in zip(users1, users2, strict=True):
        assert u1.email == u2.email
        assert u1.baseline_income == u2.baseline_income
        assert u1.starting_balance == u2.starting_balance

    # Identical transactions
    for r1, r2 in zip(res1, res2, strict=True):
        assert len(r1.transactions) == len(r2.transactions)
        for t1, t2 in zip(r1.transactions, r2.transactions, strict=True):
            assert t1.amount == t2.amount
            assert t1.balance_after == t2.balance_after
            assert t1.category == t2.category
            assert t1.ts == t2.ts
