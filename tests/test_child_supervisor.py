"""Rows 33 & 34 + row 35 support: ChildSupervisor decisions."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from aae.core.child_agent import AUP_FOOTER, ChildAgent, ChildContext
from aae.core.child_supervisor import ChildSupervisor, SupervisorError
from aae.core.trust_boundary import TrustViolation
from aae.schemas.child import ChildRun
from aae.schemas.vertical import KillCriteria


def _run(**over) -> ChildRun:
    d = dict(
        vertical_id=uuid4(),
        preregistration_id=uuid4(),
        status="live",
        monthly_budget_usd=Decimal("100"),
    )
    d.update(over)
    return ChildRun(**d)


def _kill(**over) -> KillCriteria:
    d = dict(
        max_days_to_first_dollar=14,
        min_revenue_by_day_30_usd=Decimal("50"),
        max_burn_before_first_dollar_usd=Decimal("30"),
        auto_kill_on_breach=True,
    )
    d.update(over)
    return KillCriteria(**d)


def test_auto_kill_on_day30_miss() -> None:
    # Row 33: child with revenue_mtd < day-30 target is killed
    sup = ChildSupervisor()
    past = datetime.now(timezone.utc) - timedelta(days=31)
    run = _run(spawned_at=past, revenue_mtd_usd=Decimal("10"))
    sup.register(run=run, kill=_kill())
    dec = sup.evaluate(run.id)
    assert dec.action == "kill"
    assert dec.reason == "below_day30_target"


def test_pause_on_monthly_budget() -> None:
    # Row 34: spent_mtd ≥ monthly budget → pause
    sup = ChildSupervisor()
    run = _run(spent_mtd_usd=Decimal("100"))
    sup.register(run=run, kill=_kill())
    dec = sup.evaluate(run.id)
    assert dec.action == "pause"
    assert dec.reason == "monthly_budget_breach"


def test_kill_on_first_dollar_deadline() -> None:
    sup = ChildSupervisor()
    past = datetime.now(timezone.utc) - timedelta(days=15)
    run = _run(spawned_at=past, revenue_mtd_usd=Decimal("0"))
    sup.register(run=run, kill=_kill(max_days_to_first_dollar=14))
    dec = sup.evaluate(run.id)
    assert dec.action == "kill"
    assert dec.reason == "no_revenue_by_deadline"


def test_kill_on_burn_without_revenue() -> None:
    sup = ChildSupervisor()
    run = _run()
    sup.register(run=run, kill=_kill(max_burn_before_first_dollar_usd=Decimal("30")))
    sup.record_spend(run.id, Decimal("35"))
    dec = sup.evaluate(run.id)
    assert dec.action == "kill"
    assert dec.reason == "burn_without_revenue"


def test_evaluate_keep_happy_path() -> None:
    sup = ChildSupervisor()
    run = _run(revenue_mtd_usd=Decimal("200"))
    sup.register(run=run, kill=_kill())
    assert sup.evaluate(run.id).action == "keep"


@pytest.mark.asyncio
async def test_kill_all_under_deadline() -> None:
    # Row 35 scaffolding (full sim row in test_kill_switch.py)
    sup = ChildSupervisor()
    for _ in range(5):
        sup.register(run=_run(), kill=_kill())
    killed, elapsed = await sup.kill_all(deadline_seconds=5.0)
    assert killed == 5
    assert elapsed < 5.0
    assert all(sup.get(cid).status == "killed" for cid in sup.children)


def test_supervisor_rejects_unknown_child() -> None:
    sup = ChildSupervisor()
    with pytest.raises(SupervisorError):
        sup.evaluate(uuid4())


# ---- ChildAgent ----

def test_child_agent_graph_has_no_spawn() -> None:
    # Row 18 already guards trust_boundary; confirm ChildAgent instantiates.
    run = _run()
    agent = ChildAgent(ChildContext(run=run, vertical_id=run.vertical_id, preregistration_id=run.preregistration_id))
    assert "spawn_child" not in agent.GRAPH_NODES
    assert agent.customer_footer() == AUP_FOOTER


def test_child_agent_budget_check() -> None:
    run = _run(monthly_budget_usd=Decimal("100"), spent_mtd_usd=Decimal("80"))
    a = ChildAgent(ChildContext(run=run, vertical_id=run.vertical_id, preregistration_id=run.preregistration_id))
    assert a.check_budget(Decimal("10")) is True
    assert a.check_budget(Decimal("25")) is False


def test_child_agent_heartbeat_payload_has_id_status() -> None:
    run = _run()
    a = ChildAgent(ChildContext(run=run, vertical_id=run.vertical_id, preregistration_id=run.preregistration_id))
    payload = a.heartbeat_payload()
    assert payload["child_id"] == str(run.id)
    assert payload["status"] == "live"
