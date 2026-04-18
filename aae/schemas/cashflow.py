"""Cashflow schemas (§4.2)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field

from aae.schemas.common import StrictModel, utc_now


class Pot(str, Enum):
    OPERATING = "operating"
    RESERVE = "reserve"
    GROWTH = "growth"


CashflowSource = Literal[
    "revenue_polar", "revenue_lemonsqueezy", "revenue_stripe",
    "cost_anthropic", "cost_google", "cost_infra", "cost_domain",
    "transfer_operating_to_reserve", "transfer_operating_to_growth",
    "transfer_growth_to_operating", "manual_topup",
    "emergency_transfer_reserve_to_operating",
]


class CashflowEntry(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    ts: datetime = Field(default_factory=utc_now)
    pot: Pot
    delta: Decimal = Field(..., max_digits=12, decimal_places=4)
    source: CashflowSource
    ref_id: str | None = None
    note: str = Field(default="", max_length=512)


class PotBalances(StrictModel):
    operating: Decimal
    reserve: Decimal
    growth: Decimal
    as_of: datetime = Field(default_factory=utc_now)
