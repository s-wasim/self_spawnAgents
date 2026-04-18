"""SQLAlchemy models (§14.2).

Everything is stored here; no in-memory state survives a restart. Postgres-specific
features (row-level security, pgvector) are applied via Alembic migrations; SQLAlchemy
core types are used here for portability (SQLite in tests).
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _uuid_col() -> Mapped[UUID]:
    return mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))


class AgentMemory(Base):
    __tablename__ = "agent_memory"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_tier: Mapped[str] = mapped_column(String(32), nullable=False)
    key: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # pgvector column is added in an env-gated Alembic migration on Postgres.
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CashflowLedger(Base):
    __tablename__ = "cashflow_ledger"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    pot: Mapped[str] = mapped_column(String(16), nullable=False)
    delta: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    ref_id: Mapped[str | None] = mapped_column(String(128))
    note: Mapped[str] = mapped_column(String(512), default="")
    written_by: Mapped[str] = mapped_column(String(32), default="mother")


class VerticalProposalRow(Base):
    __tablename__ = "vertical_proposals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    revenue_channel: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    preregistration_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("preregistrations.id"), nullable=False
    )
    ethics_verdict_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ethics_verdicts.id"), nullable=True
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class PreRegistrationRow(Base):
    __tablename__ = "preregistrations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    vertical_title: Mapped[str] = mapped_column(String(200), nullable=False)
    primary_metric: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_threshold: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    measurement_window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    lock_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class BuildRequestRow(Base):
    __tablename__ = "build_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    requested_by: Mapped[str] = mapped_column(String(32), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(16), nullable=False)
    network_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class ToolArtifactRow(Base):
    __tablename__ = "tool_artifacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    build_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("build_requests.id"), nullable=False
    )
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    code_path: Mapped[str] = mapped_column(String(256), nullable=False)
    test_path: Mapped[str] = mapped_column(String(256), nullable=False)
    coverage_pct: Mapped[float] = mapped_column(Float, nullable=False)
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ethics_verdict_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ethics_verdicts.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), default="signed")


class EthicsVerdictRow(Base):
    __tablename__ = "ethics_verdicts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    ruleset_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    model_used: Mapped[str] = mapped_column(String(64), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChildRunRow(Base):
    __tablename__ = "child_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    vertical_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vertical_proposals.id"), nullable=False
    )
    preregistration_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("preregistrations.id"), nullable=False
    )
    spawned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    monthly_budget_usd: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    spent_mtd_usd: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"))
    revenue_mtd_usd: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"))
    last_heartbeat: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class ToolInvocation(Base):
    __tablename__ = "tool_invocations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tool_sha: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    invoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    bytes_in: Mapped[int] = mapped_column(Integer, default=0)
    bytes_out: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal("0"))
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)


class ChannelHealth(Base):
    __tablename__ = "channel_health"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    ok: Mapped[bool] = mapped_column(Boolean, nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)


class SecurityEventRow(Base):
    __tablename__ = "security_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rule: Mapped[str] = mapped_column(String(128), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FrozenHashRow(Base):
    __tablename__ = "frozen_hashes"
    path: Mapped[str] = mapped_column(String(256), primary_key=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WeeklyDigestRow(Base):
    __tablename__ = "weekly_digests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    week_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    week_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    operator_reply: Mapped[str | None] = mapped_column(Text, nullable=True)


class OperatorMessageRow(Base):
    __tablename__ = "operator_messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verb: Mapped[str] = mapped_column(String(32), nullable=False)
    arg: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_subject: Mapped[str] = mapped_column(String(256), nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
