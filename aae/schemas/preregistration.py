"""Pre-registration schema (§4.6)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field

from aae.schemas.common import StrictModel, utc_now


class PreRegistration(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=utc_now)
    vertical_title: str
    hypothesis: str = Field(..., min_length=50, max_length=1000)
    primary_metric: Literal[
        "monthly_recurring_revenue_usd",
        "gross_margin_usd_30d",
        "paid_conversions_30d",
    ]
    primary_threshold: Decimal = Field(..., gt=Decimal("0"))
    measurement_window_days: int = Field(..., ge=14, le=90)
    analysis_plan: str = Field(..., min_length=100, max_length=3000)
    stopping_rule: str = Field(..., min_length=30, max_length=500)
    locked: bool = True
    lock_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
