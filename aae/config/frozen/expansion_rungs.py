"""Profit-driven expansion ladder thresholds (§8.2). FROZEN."""
from __future__ import annotations

from decimal import Decimal

RUNG_THRESHOLDS: dict[int, dict[str, int | Decimal]] = {
    1: {"min_revenue_usd": Decimal("0"),     "min_channels": 0, "max_children": 1},
    2: {"min_revenue_usd": Decimal("100"),   "min_channels": 1, "max_children": 2},
    3: {"min_revenue_usd": Decimal("500"),   "min_channels": 2, "max_children": 3},
    4: {"min_revenue_usd": Decimal("2000"),  "min_channels": 2, "max_children": 5},
    5: {"min_revenue_usd": Decimal("10000"), "min_channels": 2, "max_children": 8},
}

CONCENTRATION_MIN_CHANNELS_ABOVE_500_USD = 2
