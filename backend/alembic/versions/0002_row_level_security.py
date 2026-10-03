"""Row-Level Security (RLS) and database role provisioning.

Revision ID: 0002_row_level_security
Revises: 0001_initial_schema
Create Date: 2026-10-03 12:30:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_row_level_security"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_SCOPED_TABLES = [
    "transactions",
    "financial_goals",
    "goal_contributions",
    "monthly_features",
    "behavior_profiles",
    "anomalies",
    "predictions",
    "ai_recommendations",
    "conversations",
    "chat_messages",
    "refresh_tokens",
    "synthetic_user_ground_truth",
    "synthetic_transaction_ground_truth",
]


def upgrade() -> None:
    # 1. Create database roles if they do not already exist
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'migrator') THEN
            CREATE ROLE migrator WITH LOGIN SUPERUSER;
        END IF;
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_rw') THEN
            CREATE ROLE app_rw WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
        END IF;
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'worker_rw') THEN
            CREATE ROLE worker_rw WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
        END IF;
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readonly_analytics') THEN
            CREATE ROLE readonly_analytics WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
        END IF;
    END
    $$;
    """)

    # 2. Configure RLS on 'users' table (uses 'id' instead of 'user_id')
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY;")
    op.execute("""
    CREATE POLICY user_isolation_policy ON users
        FOR ALL
        USING (id = NULLIF(current_setting('app.user_id', true), '')::uuid)
        WITH CHECK (id = NULLIF(current_setting('app.user_id', true), '')::uuid);
    """)

    # 3. Configure RLS on all standard user-scoped tables (using 'user_id')
    for table in USER_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
        CREATE POLICY {table}_isolation_policy ON {table}
            FOR ALL
            USING (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
            WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid);
        """)

    # 4. Append-Only Security Controls on 'audit_log'
    # Disallow UPDATE, DELETE, and TRUNCATE for all application roles
    op.execute("GRANT INSERT, SELECT ON audit_log TO app_rw, worker_rw;")
    op.execute("REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM app_rw, worker_rw, PUBLIC;")

    # 5. Grant Table Privileges per Role
    # app_rw: Full CRUD on user-facing tables subject to RLS
    for table in ["users"] + USER_SCOPED_TABLES:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO app_rw;")

    # Allow app_rw to insert outbox events and read RAG chunks
    op.execute("GRANT SELECT, INSERT, UPDATE ON outbox_events TO app_rw;")
    op.execute("GRANT SELECT ON rag_chunks TO app_rw;")

    # worker_rw: Processes outbox events, updates features, anomalies, predictions, profiles
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON outbox_events TO worker_rw;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON monthly_features TO worker_rw;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON anomalies TO worker_rw;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON predictions TO worker_rw;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON behavior_profiles TO worker_rw;")
    op.execute("GRANT SELECT ON users, transactions, financial_goals TO worker_rw;")

    # readonly_analytics: SELECT access only
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_analytics;")

    # Sequence usage for serial IDs (audit_log, outbox_events, rag_chunks)
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_rw, worker_rw;")


def downgrade() -> None:
    # 1. Drop RLS policies and disable RLS
    op.execute("DROP POLICY IF EXISTS user_isolation_policy ON users;")
    op.execute("ALTER TABLE users NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")

    for table in USER_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    # 2. Revoke granted permissions
    op.execute(
        "REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM app_rw, worker_rw, readonly_analytics;"
    )
    op.execute("REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM app_rw, worker_rw;")

    # Note: Roles are retained or dropped conditionally in downgrade
    op.execute("""
    DO $$
    BEGIN
        DROP ROLE IF EXISTS readonly_analytics;
        DROP ROLE IF EXISTS worker_rw;
        DROP ROLE IF EXISTS app_rw;
    END
    $$;
    """)
