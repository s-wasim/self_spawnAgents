"""Weekly digest smoke + simulation-mode scaffolding."""
from __future__ import annotations

from datetime import timedelta, timezone
from decimal import Decimal

from aae.core.clock import FakeClock
from aae.ops.simulation_mode import SIM_DAYS, SimulationHarness
from aae.ops.weekly_digest import build_weekly_digest, render_digest_email
from aae.schemas.cashflow import PotBalances


def _balances() -> PotBalances:
    return PotBalances(
        operating=Decimal("150"),
        reserve=Decimal("50"),
        growth=Decimal("25"),
    )


def test_build_weekly_digest_fields() -> None:
    clock = FakeClock()
    d = build_weekly_digest(
        pot_balances=_balances(),
        revenue_usd=Decimal("300"),
        cost_usd=Decimal("80"),
        active_children=2,
        proposals_awaiting_approval=1,
        ethics_escalations=0,
        clock=clock,
    )
    assert d.revenue_usd == Decimal("300")
    assert d.active_children == 2
    assert d.frozen_hash_drift is False  # hashes.lock matches
    assert d.human_reply_deadline > d.week_end
    assert (d.human_reply_deadline - d.week_end) == timedelta(days=14)


def test_render_digest_email_has_required_lines() -> None:
    clock = FakeClock()
    d = build_weekly_digest(
        pot_balances=_balances(),
        revenue_usd=Decimal("100"),
        cost_usd=Decimal("20"),
        active_children=1,
        proposals_awaiting_approval=0,
        ethics_escalations=0,
        clock=clock,
        notes=["auto-kill fired on vertical #3"],
    )
    txt = render_digest_email(d)
    for needle in ("Operating:", "Reserve:", "Growth:", "CONTINUE", "PAUSE", "KILL"):
        assert needle in txt


def test_simulation_harness_advances_days() -> None:
    h = SimulationHarness()
    start = h.clock.now()
    for _ in range(SIM_DAYS):
        h.advance_day()
    assert h.days_elapsed == SIM_DAYS
    assert h.clock.now() - start == timedelta(days=SIM_DAYS)


def test_simulation_tracks_margin() -> None:
    h = SimulationHarness()
    h.add_revenue(Decimal("500"))
    h.add_cost(Decimal("175"))
    assert h.margin_usd() == Decimal("325")
