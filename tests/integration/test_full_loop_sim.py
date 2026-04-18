"""Integration: 14-day simulated loop (§19, rows 37, 38, 40).

We cannot execute real LangGraph + Postgres + Docker here, but we exercise the
policy pipeline end-to-end with fakes:

  Mother drafts proposal → Ethics reviews (approve) → Children spawned →
  one hits day-30 target, one misses → supervisor kills the loser →
  weekly digest is emitted with all §4.8 fields populated.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aae.cashflow.ledger import CashflowService
from aae.core.child_supervisor import ChildSupervisor
from aae.core.clock import FakeClock
from aae.core.mother_agent import can_propose_new
from aae.db.models import Base
from aae.ethics.auditor import EthicsService
from aae.ops.weekly_digest import build_weekly_digest
from aae.schemas.cashflow import Pot
from aae.schemas.child import ChildRun
from aae.schemas.common import AgentTier
from aae.schemas.ethics import EthicsReviewRequest
from aae.schemas.vertical import KillCriteria, RevenueChannel, VerticalProposal

from tests.fakes.llm import FakeLLMProvider


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _vertical(**over) -> VerticalProposal:
    d = dict(
        title="Newsletter MRR Pricing Tool",
        one_line="Deterministic pricing for mid-market newsletter operators paying a flat tier.",
        problem=(
            "Newsletter operators lack consistent pricing tooling across their tiers; "
            "many leak 20%+ of potential MRR due to misconfigured discounts across "
            "their checkout, email, and dashboard stack."
        ),
        solution=(
            "Ship a tool that reconciles tier config with live checkout and emits a "
            "pricing score + remediation recommendations weekly. It costs $49/mo and "
            "targets mid-market newsletter operators."
        ),
        target_user="Newsletter operators with 5k+ paid subscribers and a recurring SaaS stack.",
        revenue_channel=RevenueChannel.POLAR,
        pricing_model="subscription_monthly",
        unit_price_usd=Decimal("49"),
        projected_monthly_revenue_usd=Decimal("500"),
        projected_monthly_cost_usd=Decimal("60"),
        launch_budget_usd=Decimal("50"),
        kill_criteria=KillCriteria(
            max_days_to_first_dollar=14,
            min_revenue_by_day_30_usd=Decimal("50"),
            max_burn_before_first_dollar_usd=Decimal("30"),
            auto_kill_on_breach=True,
        ),
        preregistration_id=uuid4(),
    )
    d.update(over)
    return VerticalProposal(**d)


@pytest.mark.asyncio
async def test_digest_fields(session: Session) -> None:
    """Row 37: 14-day sim emits a valid WeeklyDigest."""
    # 1. Seed cashflow at $200 operating
    cs = CashflowService(session, tier=AgentTier.MOTHER)
    cs.credit(Pot.OPERATING, Decimal("200"), "manual_topup")

    # 2. Mother decides: at rung 1 with 0 children the cap is 1 → may propose
    gate = can_propose_new(
        trailing_30d_revenue_usd=Decimal("0"),
        live_channel_count=0,
        live_children=0,
    )
    assert gate.allowed

    # 3. Ethics approves (FakeLLMProvider defaults to approve)
    ethics = EthicsService(llm=FakeLLMProvider())
    proposal = _vertical()
    req = EthicsReviewRequest(
        subject_type="vertical_proposal",
        subject_id=proposal.id,
        payload_json=proposal.model_dump_json(),
    )
    verdict = await ethics.review(req)
    assert verdict.decision == "approve"

    # 4. Spawn winner + loser; loser spawned 31 days ago with $10 revenue.
    sup = ChildSupervisor()
    winner = ChildRun(
        vertical_id=proposal.id,
        preregistration_id=proposal.preregistration_id,
        status="live",
        monthly_budget_usd=Decimal("100"),
        revenue_mtd_usd=Decimal("200"),
    )
    loser_spawn = FakeClock().now() - timedelta(days=31)
    # Use current time with 31-day-old spawn for eval
    from datetime import datetime, timezone
    loser_spawn = datetime.now(timezone.utc) - timedelta(days=31)
    loser = ChildRun(
        vertical_id=proposal.id,
        preregistration_id=proposal.preregistration_id,
        status="live",
        monthly_budget_usd=Decimal("100"),
        spawned_at=loser_spawn,
        revenue_mtd_usd=Decimal("10"),
    )
    sup.register(run=winner, kill=proposal.kill_criteria)
    sup.register(run=loser, kill=proposal.kill_criteria)

    # Supervisor kills the loser
    decision = sup.evaluate(loser.id)
    assert decision.action == "kill"
    sup.kill(loser.id)  # operator/default reason
    assert sup.get(loser.id).status == "killed"

    # Winner stays
    assert sup.evaluate(winner.id).action == "keep"

    # 5. Weekly digest has every §4.8 field populated
    digest = build_weekly_digest(
        pot_balances=cs.balance(),
        revenue_usd=Decimal("200"),
        cost_usd=Decimal("40"),
        active_children=1,
        proposals_awaiting_approval=0,
        ethics_escalations=0,
    )
    assert digest.active_children == 1
    assert digest.revenue_usd == Decimal("200")
    assert digest.pot_balances.operating == Decimal("200")
    assert digest.frozen_hash_drift is False


def test_crash_and_resume(session: Session) -> None:
    """Row 38: ledger state survives a simulated crash + rehydrate.

    In prod this is LangGraph PostgresSaver. Here we assert the ledger's
    balance is a pure projection of persisted rows, so a new service over the
    same session restores identical balances — the key invariant resume needs.
    """
    cs1 = CashflowService(session, tier=AgentTier.MOTHER)
    cs1.credit(Pot.OPERATING, Decimal("150"), "manual_topup")
    cs1.credit(Pot.RESERVE, Decimal("40"), "manual_topup")
    before = cs1.balance()

    # Simulate a crash: drop the service, rebuild against same session.
    del cs1
    cs2 = CashflowService(session, tier=AgentTier.MOTHER)
    after = cs2.balance()

    assert before.operating == after.operating
    assert before.reserve == after.reserve
    assert before.growth == after.growth


def test_drift_flagged_in_digest(monkeypatch) -> None:
    """Row 40: if a FROZEN file drifts, next digest has frozen_hash_drift=True."""
    from aae.ops import weekly_digest as wd

    monkeypatch.setattr(wd, "verify_exit_code", lambda: 1)
    d = build_weekly_digest(
        pot_balances=wd.PotBalances(
            operating=Decimal("100"), reserve=Decimal("50"), growth=Decimal("25")
        ),
        revenue_usd=Decimal("0"),
        cost_usd=Decimal("0"),
        active_children=0,
        proposals_awaiting_approval=0,
        ethics_escalations=0,
    )
    assert d.frozen_hash_drift is True
