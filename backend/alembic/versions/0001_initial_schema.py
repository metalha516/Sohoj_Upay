"""Initial schema creation.

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-10-03 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enable required PostgreSQL extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "citext";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector";')

    # 2. Create ENUM types
    op.execute(
        "CREATE TYPE txn_type AS ENUM ('income', 'expense', 'cash_in', 'cash_out', 'transfer');"
    )
    op.execute(
        "CREATE TYPE purpose_t AS ENUM ('necessity', 'savings_goal', 'discretionary', 'other');"
    )
    op.execute("CREATE TYPE goal_status AS ENUM ('active', 'achieved', 'paused', 'cancelled');")

    # 3. Table: users
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("monthly_income", sa.Numeric(14, 2), nullable=True),
        sa.Column("consent_ai", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("monthly_income >= 0", name="chk_user_monthly_income_non_negative"),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # 4. Table: financial_goals
    op.create_table(
        "financial_goals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("target_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "current_amount", sa.Numeric(14, 2), server_default=sa.text("0.00"), nullable=False
        ),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active", "achieved", "paused", "cancelled", name="goal_status", create_type=False
            ),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("target_amount > 0", name="chk_goal_target_amount_positive"),
        sa.CheckConstraint("current_amount >= 0", name="chk_goal_current_amount_non_negative"),
    )
    op.create_index("idx_goals_user", "financial_goals", ["user_id"])

    # 5. Table: transactions
    op.create_table(
        "transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "transaction_type",
            postgresql.ENUM(
                "income",
                "expense",
                "cash_in",
                "cash_out",
                "transfer",
                name="txn_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "purpose",
            postgresql.ENUM(
                "necessity",
                "savings_goal",
                "discretionary",
                "other",
                name="purpose_t",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("merchant", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "goal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("financial_goals.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name="chk_transaction_amount_positive"),
        sa.CheckConstraint(
            "transaction_type NOT IN ('expense', 'cash_out') OR purpose IS NOT NULL",
            name="chk_purpose_required_for_expense_and_cashout",
        ),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_user_idempotency_key"),
    )
    op.create_index("idx_txn_user_ts", "transactions", ["user_id", sa.text("ts DESC")])
    op.create_index(
        "idx_txn_user_cat_ts", "transactions", ["user_id", "category", sa.text("ts DESC")]
    )

    # 6. Table: goal_contributions
    op.create_table(
        "goal_contributions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "goal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("financial_goals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "transaction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transactions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name="chk_contribution_amount_positive"),
    )
    op.create_index("idx_goal_contrib_user", "goal_contributions", ["user_id"])
    op.create_index("idx_goal_contrib_goal", "goal_contributions", ["goal_id"])

    # 7. Table: monthly_features
    op.create_table(
        "monthly_features",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("month", sa.Date(), primary_key=True),
        sa.Column("income", sa.Numeric(14, 2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("expense", sa.Numeric(14, 2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("savings", sa.Numeric(14, 2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("savings_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column(
            "necessity_expense", sa.Numeric(14, 2), server_default=sa.text("0.00"), nullable=False
        ),
        sa.Column(
            "discretionary_expense",
            sa.Numeric(14, 2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column("necessity_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("discretionary_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("txn_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("cashout_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("avg_txn", sa.Numeric(14, 2), nullable=True),
        sa.Column("median_txn", sa.Numeric(14, 2), nullable=True),
        sa.Column("expense_variance", sa.Numeric(18, 4), nullable=True),
        sa.Column("spending_growth", sa.Numeric(8, 4), nullable=True),
        sa.Column("income_expense_ratio", sa.Numeric(8, 4), nullable=True),
        sa.Column("savings_consistency", sa.Numeric(6, 4), nullable=True),
        sa.Column(
            "category_breakdown",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 8. Table: behavior_profiles
    op.create_table(
        "behavior_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("profile", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("top_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("savings_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("necessity_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("discretionary_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("cashout_frequency", sa.Numeric(8, 4), nullable=True),
        sa.Column("spending_variance", sa.Numeric(18, 4), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("as_of_month", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_behavior_user_month", "behavior_profiles", ["user_id", "as_of_month"])

    # 9. Table: anomalies
    op.create_table(
        "anomalies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "transaction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transactions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("scope", sa.String(50), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("anomaly_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("observed_value", sa.Numeric(14, 2), nullable=False),
        sa.Column("baseline_value", sa.Numeric(14, 2), nullable=False),
        sa.Column("deviation_pct", sa.Numeric(8, 2), nullable=False),
        sa.Column("explanation", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default=sa.text("'open'"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("scope IN ('transaction', 'category_month')", name="chk_anomaly_scope"),
        sa.CheckConstraint(
            "status IN ('open', 'dismissed', 'confirmed')", name="chk_anomaly_status"
        ),
    )
    op.create_index("idx_anomalies_user_status", "anomalies", ["user_id", "status"])

    # 10. Table: predictions
    op.create_table(
        "predictions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prediction_type", sa.String(50), nullable=False),
        sa.Column("prediction_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("horizon_month", sa.Date(), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column(
            "prediction_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "prediction_type IN ('expense_forecast', 'savings_forecast', 'anomaly', 'behavior')",
            name="chk_prediction_type",
        ),
    )
    op.create_index("idx_predictions_user_type", "predictions", ["user_id", "prediction_type"])

    # 11. Table: ai_recommendations
    op.create_table(
        "ai_recommendations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("priority", sa.SmallInteger(), server_default=sa.text("3"), nullable=False),
        sa.Column("source_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_recommendations_user", "ai_recommendations", ["user_id"])

    # 12. Table: conversations
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_conversations_user", "conversations", ["user_id"])

    # 13. Table: chat_messages
    op.create_table(
        "chat_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_calls", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("feedback", sa.SmallInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("role IN ('user', 'assistant', 'tool')", name="chk_chat_message_role"),
    )
    op.create_index("idx_chat_msg_user", "chat_messages", ["user_id"])
    op.create_index("idx_chat_msg_convo", "chat_messages", ["conversation_id"])

    # 14. Table: audit_log (system-wide append-only)
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource", sa.String(255), nullable=True),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_audit_user_action", "audit_log", ["user_id", "action"])
    op.create_index("idx_audit_created_at", "audit_log", ["created_at"])

    # 15. Table: outbox_events (async pipeline trigger)
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_outbox_unprocessed", "outbox_events", ["processed_at", "created_at"])

    # 16. Table: rag_chunks
    op.create_table(
        "rag_chunks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("doc_id", sa.String(100), nullable=False),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("chunk", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("idx_rag_doc", "rag_chunks", ["doc_id"])
    op.execute(
        "CREATE INDEX idx_rag_embedding ON rag_chunks USING hnsw (embedding vector_cosine_ops);"
    )

    # 17. Table: synthetic_user_ground_truth
    op.create_table(
        "synthetic_user_ground_truth",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("true_persona", sa.String(100), nullable=False),
        sa.Column("true_occupation", sa.String(100), nullable=False),
        sa.Column("baseline_income_bdt", sa.Numeric(14, 2), nullable=False),
        sa.Column("target_savings_rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("is_drifting", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("drift_target_persona", sa.String(100), nullable=True),
        sa.Column("drift_start_month", sa.Integer(), nullable=True),
        sa.Column("generator_seed", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 18. Table: synthetic_transaction_ground_truth
    op.create_table(
        "synthetic_transaction_ground_truth",
        sa.Column(
            "transaction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transactions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "is_injected_anomaly", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("anomaly_type", sa.String(100), nullable=True),
        sa.Column("anomaly_multiplier", sa.Numeric(6, 2), nullable=True),
        sa.Column("life_event_code", sa.String(100), nullable=True),
        sa.Column("counterfactual_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_syn_txn_user", "synthetic_transaction_ground_truth", ["user_id"])

    # 19. Table: refresh_tokens
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_refresh_tokens_user", "refresh_tokens", ["user_id"])


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("refresh_tokens")
    op.drop_table("synthetic_transaction_ground_truth")
    op.drop_table("synthetic_user_ground_truth")
    op.drop_table("rag_chunks")
    op.drop_table("outbox_events")
    op.drop_table("audit_log")
    op.drop_table("chat_messages")
    op.drop_table("conversations")
    op.drop_table("ai_recommendations")
    op.drop_table("predictions")
    op.drop_table("anomalies")
    op.drop_table("behavior_profiles")
    op.drop_table("monthly_features")
    op.drop_table("goal_contributions")
    op.drop_table("transactions")
    op.drop_table("financial_goals")
    op.drop_table("users")

    # Drop custom ENUMs
    op.execute("DROP TYPE IF EXISTS goal_status;")
    op.execute("DROP TYPE IF EXISTS purpose_t;")
    op.execute("DROP TYPE IF EXISTS txn_type;")
