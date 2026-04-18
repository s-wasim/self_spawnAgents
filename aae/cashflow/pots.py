"""Pot-level helpers (§7.1)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from aae.cashflow.hard_floors import GROWTH_CAP_PCT_OF_90D_REVENUE
from aae.schemas.cashflow import Pot


@dataclass(frozen=True)
class PotSnapshot:
    operating: Decimal
    reserve: Decimal
    growth: Decimal

    def get(self, pot: Pot) -> Decimal:
        return {
            Pot.OPERATING: self.operating,
            Pot.RESERVE: self.reserve,
            Pot.GROWTH: self.growth,
        }[pot]


def reserve_cap_from_burn(daily_burn_usd: Decimal, runway_days: int = 90) -> Decimal:
    return (daily_burn_usd * runway_days).quantize(Decimal("0.0001"))


def growth_cap_from_trailing_revenue(trailing_90d_revenue_usd: Decimal) -> Decimal:
    return (trailing_90d_revenue_usd * GROWTH_CAP_PCT_OF_90D_REVENUE).quantize(Decimal("0.0001"))
