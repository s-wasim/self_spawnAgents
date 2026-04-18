"""Simulation-mode harness (§19).

Replaces clock, channels, and LLM with deterministic fakes so the 14-day
simulation runs in ~90 minutes (FakeClock tick is 90min / 14d ≈ 2688× real).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

from aae.core.clock import FakeClock


SIM_DAYS: int = 14
SIM_WALLCLOCK_MINUTES: int = 90


@dataclass
class SimulationHarness:
    """Compresses sim days into wall-clock minutes via FakeClock ticks."""

    clock: FakeClock = field(default_factory=FakeClock)
    days_elapsed: int = 0
    revenue_total_usd: Decimal = Decimal("0")
    cost_total_usd: Decimal = Decimal("0")

    @property
    def tick(self) -> timedelta:
        return timedelta(days=SIM_DAYS) / (SIM_WALLCLOCK_MINUTES * 60)  # per real-second

    def advance_day(self) -> None:
        self.clock.advance(timedelta(days=1))
        self.days_elapsed += 1

    def add_revenue(self, amount_usd: Decimal) -> None:
        self.revenue_total_usd += amount_usd

    def add_cost(self, amount_usd: Decimal) -> None:
        self.cost_total_usd += amount_usd

    def margin_usd(self) -> Decimal:
        return self.revenue_total_usd - self.cost_total_usd
