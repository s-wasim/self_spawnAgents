"""Child run schema (§4.7)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field

from aae.schemas.common import StrictModel, utc_now


class ChildRun(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    vertical_id: UUID
    preregistration_id: UUID
    spawned_at: datetime = Field(default_factory=utc_now)
    status: Literal["starting", "live", "paused", "killed", "archived"]
    monthly_budget_usd: Decimal = Field(..., gt=Decimal("0"), le=Decimal("1000"))
    spent_mtd_usd: Decimal = Field(default=Decimal("0"))
    revenue_mtd_usd: Decimal = Field(default=Decimal("0"))
    last_heartbeat: datetime = Field(default_factory=utc_now)
    last_error: str | None = Field(default=None, max_length=2000)
