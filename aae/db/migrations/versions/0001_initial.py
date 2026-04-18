"""Initial schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-18
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _pg() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "postgresql"


def upgrade() -> None:
    # ---- preregistrations
    op.create_table(
        "preregistrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("vertical_title", sa.String(200), nullable=False),
        sa.Column("primary_metric", sa.String(64), nullable=False),
        sa.Column("primary_threshold", sa.Numeric(12, 4), nullable=False),
        sa.Column("measurement_window_days", sa.Integer, nullable=False),
        sa.Column("locked", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("lock_hash", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.JSON, nullable=False),
    )

    # ---- vertical_proposals
    op.create_table(
        "vertical_proposals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("revenue_channel", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, index=True),
        sa.Column("preregistration_id", sa.String(36),
                  sa.ForeignKey("preregistrations.id"), nullable=False),
        sa.Column("ethics_verdict_id", sa.String(36), nullable=True),
        sa.Column("payload_json", sa.JSON, nullable=False),
    )

    # ---- ethics_verdicts
    op.create_table(
        "ethics_verdicts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("subject_type", sa.String(32), nullable=False),
        sa.Column("subject_id", sa.String(36), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("ruleset_hash", sa.String(64), nullable=False),
        sa.Column("model_used", sa.String(64), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ---- cashflow_ledger
    op.create_table(
        "cashflow_ledger",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("pot", sa.String(16), nullable=False),
        sa.Column("delta", sa.Numeric(12, 4), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("ref_id", sa.String(128), nullable=True),
        sa.Column("note", sa.String(512), server_default=""),
        sa.Column("written_by", sa.String(32), server_default="mother"),
    )

    # ---- agent_memory (pgvector embedding added below on Postgres)
    op.create_table(
        "agent_memory",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("agent_tier", sa.String(32), nullable=False),
        sa.Column("key", sa.String(256), nullable=False, index=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", sa.LargeBinary, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ---- build_requests + tool_artifacts
    op.create_table(
        "build_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("requested_by", sa.String(32), nullable=False),
        sa.Column("tool_name", sa.String(64), nullable=False),
        sa.Column("risk_tier", sa.String(16), nullable=False),
        sa.Column("network_required", sa.Boolean, nullable=False),
        sa.Column("payload_json", sa.JSON, nullable=False),
    )
    op.create_table(
        "tool_artifacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("build_request_id", sa.String(36),
                  sa.ForeignKey("build_requests.id"), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("code_path", sa.String(256), nullable=False),
        sa.Column("test_path", sa.String(256), nullable=False),
        sa.Column("coverage_pct", sa.Float, nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ethics_verdict_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(16), server_default="signed"),
    )

    # ---- child_runs
    op.create_table(
        "child_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("vertical_id", sa.String(36),
                  sa.ForeignKey("vertical_proposals.id"), nullable=False),
        sa.Column("preregistration_id", sa.String(36),
                  sa.ForeignKey("preregistrations.id"), nullable=False),
        sa.Column("spawned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, index=True),
        sa.Column("monthly_budget_usd", sa.Numeric(12, 4), nullable=False),
        sa.Column("spent_mtd_usd", sa.Numeric(12, 4), server_default="0"),
        sa.Column("revenue_mtd_usd", sa.Numeric(12, 4), server_default="0"),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_error", sa.Text, nullable=True),
    )

    # ---- tool_invocations
    op.create_table(
        "tool_invocations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tool_sha", sa.String(64), nullable=False, index=True),
        sa.Column("invoked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Integer, nullable=False),
        sa.Column("bytes_in", sa.Integer, server_default="0"),
        sa.Column("bytes_out", sa.Integer, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(12, 6), server_default="0"),
        sa.Column("outcome", sa.String(16), nullable=False),
    )

    # ---- channel_health
    op.create_table(
        "channel_health",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("channel", sa.String(32), nullable=False, index=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latency_ms", sa.Integer, nullable=False),
        sa.Column("ok", sa.Boolean, nullable=False),
        sa.Column("detail", sa.Text, nullable=True),
    )

    # ---- security_events
    op.create_table(
        "security_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rule", sa.String(128), nullable=False),
        sa.Column("detail", sa.Text, nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ---- frozen_hashes
    op.create_table(
        "frozen_hashes",
        sa.Column("path", sa.String(256), primary_key=True),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ---- weekly_digests
    op.create_table(
        "weekly_digests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("week_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("week_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_json", sa.JSON, nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("operator_reply", sa.Text, nullable=True),
    )

    # ---- operator_messages
    op.create_table(
        "operator_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verb", sa.String(32), nullable=False),
        sa.Column("arg", sa.String(128), nullable=True),
        sa.Column("raw_sha256", sa.String(64), nullable=False),
        sa.Column("raw_subject", sa.String(256), nullable=False),
        sa.Column("accepted", sa.Boolean, nullable=False),
    )

    # ---- Postgres-only: pgvector + row-level security + prereg lock trigger
    if _pg():
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.execute("ALTER TABLE agent_memory ADD COLUMN embedding_vec vector(1536)")
        op.execute(
            "CREATE INDEX agent_memory_embedding_hnsw ON agent_memory "
            "USING hnsw (embedding_vec vector_cosine_ops) WITH (m=16, ef_construction=64)"
        )
        # Row-level-security: only sessions setting app.agent_tier='mother' may write.
        op.execute("ALTER TABLE cashflow_ledger ENABLE ROW LEVEL SECURITY")
        op.execute(
            "CREATE POLICY mother_only_write ON cashflow_ledger "
            "FOR INSERT WITH CHECK (current_setting('app.agent_tier', true) = 'mother')"
        )
        # Trigger: reject UPDATE on locked preregistration rows except for payload_json-less status.
        op.execute(
            "CREATE OR REPLACE FUNCTION prereg_reject_update() RETURNS trigger AS $$ "
            "BEGIN IF OLD.locked THEN RAISE EXCEPTION 'preregistration row is locked'; "
            "END IF; RETURN NEW; END; $$ LANGUAGE plpgsql"
        )
        op.execute(
            "CREATE TRIGGER trg_prereg_lock BEFORE UPDATE ON preregistrations "
            "FOR EACH ROW EXECUTE FUNCTION prereg_reject_update()"
        )


def downgrade() -> None:
    suffix = " CASCADE" if _pg() else ""
    for table in (
        "operator_messages", "weekly_digests", "frozen_hashes", "security_events",
        "channel_health", "tool_invocations", "child_runs", "tool_artifacts",
        "build_requests", "agent_memory", "cashflow_ledger", "ethics_verdicts",
        "vertical_proposals", "preregistrations",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table}{suffix}")
