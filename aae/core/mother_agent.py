"""Mother Agent — deterministic expansion controller (§8).

Full LangGraph wiring happens at runtime; here we expose the pure, testable
policy functions the graph nodes call:
  * current_rung()     — which rung we're on
  * can_propose_new()  — gating decision
  * select_rung_config() — threshold row for that rung
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from aae.config.frozen.expansion_rungs import RUNG_THRESHOLDS


@dataclass(frozen=True)
class RungConfig:
    rung: int
    min_revenue_usd: Decimal
    min_channels: int
    max_children: int


def _as_config(rung: int) -> RungConfig:
    row = RUNG_THRESHOLDS[rung]
    return RungConfig(
        rung=rung,
        min_revenue_usd=Decimal(str(row["min_revenue_usd"])),
        min_channels=int(row["min_channels"]),
        max_children=int(row["max_children"]),
    )


def current_rung(*, trailing_30d_revenue_usd: Decimal, live_channel_count: int) -> int:
    """Pick the highest rung whose thresholds are satisfied."""
    best = 1
    for rung in sorted(RUNG_THRESHOLDS):
        cfg = _as_config(rung)
        if (
            trailing_30d_revenue_usd >= cfg.min_revenue_usd
            and live_channel_count >= cfg.min_channels
        ):
            best = rung
    return best


@dataclass
class ProposalGate:
    allowed: bool
    reason: str
    rung: int
    max_children: int


def can_propose_new(
    *,
    trailing_30d_revenue_usd: Decimal,
    live_channel_count: int,
    live_children: int,
) -> ProposalGate:
    """§8.1/§8.4: can the Mother propose a new vertical right now?"""
    rung = current_rung(
        trailing_30d_revenue_usd=trailing_30d_revenue_usd,
        live_channel_count=live_channel_count,
    )
    cfg = _as_config(rung)
    # §8.4 concentration rule: at ≥ $500 trailing, must have ≥ 2 channels
    if trailing_30d_revenue_usd >= Decimal("500") and live_channel_count < 2:
        return ProposalGate(False, "concentration_rule_halt", rung, cfg.max_children)
    if live_children >= cfg.max_children:
        return ProposalGate(False, f"max_children_reached_{cfg.max_children}", rung, cfg.max_children)
    # Rung 2 specifically requires $100 + 1 channel live before Child #2
    if live_children >= 1 and trailing_30d_revenue_usd < Decimal("100"):
        return ProposalGate(False, "rung2_requires_100_revenue", rung, cfg.max_children)
    return ProposalGate(True, "ok", rung, cfg.max_children)


def must_use_different_channel(*, live_channels: list[str], proposed_channel: str) -> bool:
    """§8.1 rung 3: diversification — 3rd vertical must differ from #1 and #2."""
    if len(live_channels) >= 2:
        return proposed_channel not in live_channels
    return True
