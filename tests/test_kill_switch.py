"""Rows 35 & 36: KILL ALL completes within 30s; EMERGENCY_TRANSFER needs HMAC."""
from __future__ import annotations

import hashlib
import hmac
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aae.cashflow.ledger import (
    BadHMAC,
    CashflowService,
    verify_emergency_hmac,
)
from aae.core.child_supervisor import ChildSupervisor
from aae.db.models import Base
from aae.schemas.cashflow import Pot
from aae.schemas.child import ChildRun
from aae.schemas.common import AgentTier
from aae.schemas.vertical import KillCriteria


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _kill_criteria() -> KillCriteria:
    return KillCriteria(
        max_days_to_first_dollar=14,
        min_revenue_by_day_30_usd=Decimal("50"),
        max_burn_before_first_dollar_usd=Decimal("30"),
        auto_kill_on_breach=True,
    )


def _child(**over) -> ChildRun:
    d = dict(
        vertical_id=uuid4(),
        preregistration_id=uuid4(),
        status="live",
        monthly_budget_usd=Decimal("100"),
    )
    d.update(over)
    return ChildRun(**d)


@pytest.mark.asyncio
async def test_kill_all_30s() -> None:
    # Row 35: 20 children all killed well inside 30s.
    sup = ChildSupervisor()
    for _ in range(20):
        sup.register(run=_child(), kill=_kill_criteria())
    killed, elapsed = await sup.kill_all(deadline_seconds=30.0)
    assert killed == 20
    assert elapsed < 30.0
    for cid in sup.children:
        assert sup.get(cid).status == "killed"


def _sign(secret: str, amount: Decimal, date_iso: str) -> str:
    msg = f"{amount}|{date_iso}".encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def test_emergency_transfer_hmac_required(session: Session) -> None:
    secret = "operator-secret-xyz"
    today = date.today().isoformat()

    # Valid sig verifies
    good = _sign(secret, Decimal("100"), today)
    assert verify_emergency_hmac(secret, Decimal("100"), today, good) is True
    # Tampered amount breaks verification
    assert verify_emergency_hmac(secret, Decimal("101"), today, good) is False
    # Wrong secret breaks verification
    assert verify_emergency_hmac("wrong-secret", Decimal("100"), today, good) is False

    cs = CashflowService(session, tier=AgentTier.MOTHER)
    cs.credit(Pot.RESERVE, Decimal("200"), "manual_topup")
    with pytest.raises(BadHMAC):
        cs.emergency_transfer_reserve_to_operating(
            amount_usd=Decimal("100"),
            date_iso=today,
            signature="deadbeef",
            operator_secret=secret,
        )


def test_emergency_transfer_with_valid_hmac_succeeds(session: Session) -> None:
    secret = "operator-secret-xyz"
    today = date.today().isoformat()
    cs = CashflowService(session, tier=AgentTier.MOTHER)
    cs.credit(Pot.RESERVE, Decimal("200"), "manual_topup")
    good = _sign(secret, Decimal("100"), today)
    cs.emergency_transfer_reserve_to_operating(
        amount_usd=Decimal("100"),
        date_iso=today,
        signature=good,
        operator_secret=secret,
    )
    bal = cs.balance()
    assert bal.reserve == Decimal("100")
    assert bal.operating == Decimal("100")


def test_pause_all_flips_status() -> None:
    sup = ChildSupervisor()
    for _ in range(3):
        sup.register(run=_child(), kill=_kill_criteria())
    paused = sup.pause_all()
    assert paused == 3
    for cid in sup.children:
        assert sup.get(cid).status == "paused"
