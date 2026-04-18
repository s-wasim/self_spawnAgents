"""Rows 31 & 32: expansion ladder + concentration halt."""
from __future__ import annotations

from decimal import Decimal

from aae.core.mother_agent import (
    ProposalGate,
    can_propose_new,
    current_rung,
    must_use_different_channel,
)


def test_rung2_gates() -> None:
    # Row 31: rung 2 requires $100 + 1 channel BEFORE the Mother may propose Child #2.
    # At $0 revenue we're still on rung 1 (max_children=1); 1 live child blocks.
    gate = can_propose_new(
        trailing_30d_revenue_usd=Decimal("0"),
        live_channel_count=1,
        live_children=1,
    )
    assert gate.allowed is False

    # At $99 revenue with 1 channel, we're still rung 1 — cap is 1, so no.
    gate = can_propose_new(
        trailing_30d_revenue_usd=Decimal("99"),
        live_channel_count=1,
        live_children=1,
    )
    assert gate.allowed is False

    # At exactly $100 with 1 channel & 1 live child, we're at rung 2 (cap 2) → allowed.
    gate = can_propose_new(
        trailing_30d_revenue_usd=Decimal("100"),
        live_channel_count=1,
        live_children=1,
    )
    assert gate.allowed is True
    assert gate.rung == 2


def test_single_channel_halts_proposals() -> None:
    # Row 32: trailing $500+ but only 1 channel live → no new proposals
    gate = can_propose_new(
        trailing_30d_revenue_usd=Decimal("750"),
        live_channel_count=1,
        live_children=2,
    )
    assert gate.allowed is False
    assert gate.reason == "concentration_rule_halt"

    # Same revenue with 2 channels → allowed
    gate = can_propose_new(
        trailing_30d_revenue_usd=Decimal("750"),
        live_channel_count=2,
        live_children=2,
    )
    assert gate.allowed is True


def test_rung_selection_monotonic() -> None:
    assert current_rung(trailing_30d_revenue_usd=Decimal("0"), live_channel_count=0) == 1
    assert current_rung(trailing_30d_revenue_usd=Decimal("100"), live_channel_count=1) == 2
    assert current_rung(trailing_30d_revenue_usd=Decimal("500"), live_channel_count=2) == 3
    assert current_rung(trailing_30d_revenue_usd=Decimal("2000"), live_channel_count=2) == 4
    assert current_rung(trailing_30d_revenue_usd=Decimal("10000"), live_channel_count=2) == 5


def test_max_children_cap() -> None:
    # rung 5 caps at 8 children
    gate = can_propose_new(
        trailing_30d_revenue_usd=Decimal("10000"),
        live_channel_count=3,
        live_children=8,
    )
    assert gate.allowed is False
    assert "8" in gate.reason


def test_channel_diversification() -> None:
    # rung 3: 3rd vertical must use a different channel
    assert must_use_different_channel(live_channels=["polar", "stripe_connect"], proposed_channel="lemonsqueezy") is True
    assert must_use_different_channel(live_channels=["polar", "stripe_connect"], proposed_channel="polar") is False
    # fewer than 2 live → rule not yet binding
    assert must_use_different_channel(live_channels=["polar"], proposed_channel="polar") is True


def test_proposal_gate_shape() -> None:
    gate = can_propose_new(
        trailing_30d_revenue_usd=Decimal("50"),
        live_channel_count=1,
        live_children=0,
    )
    assert isinstance(gate, ProposalGate)
    assert gate.max_children >= 1
