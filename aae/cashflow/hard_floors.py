"""Cashflow hard floors (§7.2). FROZEN. Do not edit without CHANGELOG.frozen.md entry."""
from __future__ import annotations

from decimal import Decimal

OPERATING_SPLIT = Decimal("0.60")
RESERVE_SPLIT   = Decimal("0.25")
GROWTH_SPLIT    = Decimal("0.15")

OPERATING_HARD_FLOOR_USD = Decimal("50")

RESERVE_INVIOLATE = True  # operator-signed emergency_transfer only

GROWTH_CAP_PCT_OF_90D_REVENUE = Decimal("0.30")

# 90-day burn-rate runway target for the Reserve pot.
RESERVE_RUNWAY_DAYS = 90
