"""Vertical proposal schemas (§4.3)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from aae.schemas.common import StrictModel, utc_now


class RevenueChannel(str, Enum):
    POLAR = "polar"
    LEMONSQUEEZY = "lemonsqueezy"
    STRIPE_CONNECT = "stripe_connect"


class KillCriteria(StrictModel):
    max_days_to_first_dollar: int = Field(..., ge=7, le=60)
    min_revenue_by_day_30_usd: Decimal = Field(..., ge=Decimal("0"))
    max_burn_before_first_dollar_usd: Decimal = Field(..., gt=Decimal("0"))
    auto_kill_on_breach: bool = True

    @field_validator("auto_kill_on_breach")
    @classmethod
    def _must_auto_kill(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("auto_kill_on_breach MUST be True")
        return v


VerticalStatus = Literal[
    "drafted", "ethics_pending", "ethics_rejected",
    "awaiting_human", "human_rejected", "human_approved",
    "live", "paused", "killed", "archived",
]


class VerticalProposal(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=utc_now)
    title: str = Field(..., min_length=8, max_length=120)
    one_line: str = Field(..., min_length=20, max_length=280)
    problem: str = Field(..., min_length=100, max_length=2000)
    solution: str = Field(..., min_length=100, max_length=2000)
    target_user: str = Field(..., min_length=20, max_length=500)
    revenue_channel: RevenueChannel
    pricing_model: Literal["one_time", "subscription_monthly", "usage_based"]
    unit_price_usd: Decimal = Field(..., gt=Decimal("0"), le=Decimal("9999"))
    projected_monthly_revenue_usd: Decimal = Field(..., ge=Decimal("0"))
    projected_monthly_cost_usd: Decimal = Field(..., ge=Decimal("0"))
    launch_budget_usd: Decimal = Field(..., gt=Decimal("0"), le=Decimal("500"))
    kill_criteria: KillCriteria
    preregistration_id: UUID
    ethics_verdict_id: UUID | None = None
    status: VerticalStatus = "drafted"
