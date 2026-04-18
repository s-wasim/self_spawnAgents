"""Weekly digest schema (§4.8)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import Field

from aae.schemas.cashflow import PotBalances
from aae.schemas.common import StrictModel


class WeeklyDigest(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    week_start: datetime
    week_end: datetime
    pot_balances: PotBalances
    revenue_usd: Decimal
    cost_usd: Decimal
    active_children: int
    proposals_awaiting_approval: int
    ethics_escalations: int
    frozen_hash_drift: bool
    notes: list[str] = Field(default_factory=list)
    human_reply_deadline: datetime
