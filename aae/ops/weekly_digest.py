"""Weekly digest generator (§4.8 + §15.3)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from aae.core.clock import TimeProvider, SystemClock
from aae.ops.freeze_experiment import verify_exit_code
from aae.schemas.cashflow import PotBalances
from aae.schemas.digest import WeeklyDigest


def build_weekly_digest(
    *,
    pot_balances: PotBalances,
    revenue_usd: Decimal,
    cost_usd: Decimal,
    active_children: int,
    proposals_awaiting_approval: int,
    ethics_escalations: int,
    clock: TimeProvider | None = None,
    notes: list[str] | None = None,
) -> WeeklyDigest:
    clk = clock or SystemClock()
    now = clk.now()
    week_start = now - timedelta(days=7)
    drift = verify_exit_code() != 0
    return WeeklyDigest(
        week_start=week_start,
        week_end=now,
        pot_balances=pot_balances,
        revenue_usd=revenue_usd,
        cost_usd=cost_usd,
        active_children=active_children,
        proposals_awaiting_approval=proposals_awaiting_approval,
        ethics_escalations=ethics_escalations,
        frozen_hash_drift=drift,
        notes=notes or [],
        human_reply_deadline=now + timedelta(days=14),
    )


def render_digest_email(d: WeeklyDigest) -> str:
    lines = [
        "Weekly AAE digest",
        f"Week: {d.week_start.date()} → {d.week_end.date()}",
        "",
        f"Operating: ${d.pot_balances.operating}",
        f"Reserve:   ${d.pot_balances.reserve}",
        f"Growth:    ${d.pot_balances.growth}",
        "",
        f"Revenue (7d): ${d.revenue_usd}",
        f"Cost (7d):    ${d.cost_usd}",
        f"Active children: {d.active_children}",
        f"Proposals awaiting approval: {d.proposals_awaiting_approval}",
        f"Ethics escalations: {d.ethics_escalations}",
        f"Frozen-hash drift: {d.frozen_hash_drift}",
        "",
        "Reply CONTINUE / PAUSE / KILL [ALL|<child_id>] by "
        f"{d.human_reply_deadline.date()} or the system auto-PAUSEs.",
    ]
    if d.notes:
        lines.extend(["", "Notes:"])
        lines.extend(f"- {n}" for n in d.notes)
    return "\n".join(lines)
