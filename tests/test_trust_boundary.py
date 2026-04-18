"""Trust boundary tests (§20 rows 17, 18)."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aae.cashflow.ledger import CashflowService
from aae.core.trust_boundary import (
    CHILD_FORBIDDEN_NODES,
    TrustViolation,
    assert_child_graph_allowed,
    assert_no_network_in_builder,
    require_mother_for_ledger,
)
from aae.db.models import Base
from aae.schemas.common import AgentTier


def test_non_mother_cannot_write_ledger():
    """Row 17."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    for forbidden in (AgentTier.CHILD, AgentTier.CODE_BUILDER, AgentTier.ETHICS_AUDITOR):
        with Session(engine) as s, pytest.raises(TrustViolation):
            CashflowService(s, tier=forbidden)


def test_require_mother_for_ledger_raises():
    for bad in (AgentTier.CHILD, AgentTier.ETHICS_AUDITOR, AgentTier.CODE_BUILDER):
        with pytest.raises(TrustViolation):
            require_mother_for_ledger(bad)
    # happy path does not raise.
    require_mother_for_ledger(AgentTier.MOTHER)


def test_child_graph_has_no_spawn_node():
    """Row 18."""
    legal = {"observe", "act", "report_metrics", "await_ok"}
    assert_child_graph_allowed(legal)  # no raise
    for forbidden in CHILD_FORBIDDEN_NODES:
        with pytest.raises(TrustViolation):
            assert_child_graph_allowed({forbidden})


def test_builder_sandbox_no_network():
    assert_no_network_in_builder(False)  # ok
    with pytest.raises(TrustViolation):
        assert_no_network_in_builder(True)
