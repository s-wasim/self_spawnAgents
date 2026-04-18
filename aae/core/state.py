"""LangGraph state (§17 mention; used by Mother Agent graph).

TypedDicts describing the stateful fields LangGraph threads between nodes.
We keep these lean so a Postgres checkpoint snapshot stays small.
"""
from __future__ import annotations

from decimal import Decimal
from typing import NotRequired, TypedDict
from uuid import UUID


class MotherState(TypedDict):
    """Top-level state of the Mother Agent graph."""

    operating_pot_usd: Decimal
    reserve_pot_usd: Decimal
    growth_pot_usd: Decimal

    trailing_30d_revenue_usd: Decimal
    live_channels: list[str]  # channel names with healthy + non-zero revenue
    live_children: int

    pending_proposal_id: NotRequired[UUID | None]
    last_ethics_verdict_id: NotRequired[UUID | None]
    awaiting_operator: NotRequired[bool]
    last_error: NotRequired[str]
