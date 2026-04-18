"""DB layer / Alembic smoke tests."""
from __future__ import annotations

import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from aae.db.models import Base


def test_models_create_all_tables():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    tables = set(inspect(engine).get_table_names())
    expected = {
        "agent_memory", "cashflow_ledger", "vertical_proposals", "preregistrations",
        "build_requests", "tool_artifacts", "ethics_verdicts", "child_runs",
        "tool_invocations", "channel_health", "security_events", "frozen_hashes",
        "weekly_digests", "operator_messages",
    }
    assert expected.issubset(tables), f"Missing: {expected - tables}"


def test_alembic_upgrade_head_on_sqlite(tmp_path: Path):
    dsn = f"sqlite:///{tmp_path}/t.db"
    cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", dsn)
    command.upgrade(cfg, "head")

    engine = create_engine(dsn)
    tables = set(inspect(engine).get_table_names())
    assert "cashflow_ledger" in tables
    assert "preregistrations" in tables
    assert "ethics_verdicts" in tables
