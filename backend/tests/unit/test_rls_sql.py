"""Unit tests verifying Alembic SQL migration output and Row-Level Security clauses."""

import pytest
from alembic.command import upgrade
from alembic.config import Config


def test_alembic_sql_generation_and_rls_policies(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that Alembic emits all required RLS, role, and append-only DDL in SQL generation."""
    alembic_cfg = Config("backend/alembic.ini")
    alembic_cfg.set_main_option("script_location", "backend/alembic")

    upgrade(alembic_cfg, "head", sql=True)
    captured = capsys.readouterr()
    sql_output = captured.out

    # 1. Verify extensions
    assert 'CREATE EXTENSION IF NOT EXISTS "pgcrypto"' in sql_output
    assert 'CREATE EXTENSION IF NOT EXISTS "citext"' in sql_output
    assert 'CREATE EXTENSION IF NOT EXISTS "vector"' in sql_output

    # 2. Verify roles provisioned with NOBYPASSRLS
    assert (
        "CREATE ROLE app_rw WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS"
        in sql_output
    )
    assert (
        "CREATE ROLE worker_rw WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS"
        in sql_output
    )
    assert (
        "CREATE ROLE readonly_analytics WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS"
        in sql_output
    )

    # 3. Verify RLS enabled and forced on user tables
    assert "ALTER TABLE users ENABLE ROW LEVEL SECURITY" in sql_output
    assert "ALTER TABLE users FORCE ROW LEVEL SECURITY" in sql_output
    assert "CREATE POLICY user_isolation_policy ON users" in sql_output

    assert "ALTER TABLE transactions ENABLE ROW LEVEL SECURITY" in sql_output
    assert "ALTER TABLE transactions FORCE ROW LEVEL SECURITY" in sql_output
    assert "CREATE POLICY transactions_isolation_policy ON transactions" in sql_output

    assert "ALTER TABLE financial_goals ENABLE ROW LEVEL SECURITY" in sql_output
    assert "ALTER TABLE financial_goals FORCE ROW LEVEL SECURITY" in sql_output

    # 4. Verify append-only security on audit_log
    assert (
        "REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM app_rw, worker_rw, PUBLIC" in sql_output
    )
    assert "GRANT INSERT, SELECT ON audit_log TO app_rw, worker_rw" in sql_output
