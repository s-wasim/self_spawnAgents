"""Tests for Pydantic schemas (§4)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aae.schemas import (
    AgentTier,
    BuildRequest,
    CashflowEntry,
    ChildRun,
    EthicsVerdict,
    KillCriteria,
    ModelID,
    Pot,
    PotBalances,
    PreRegistration,
    RevenueChannel,
    ToolArtifact,
    VerticalProposal,
    WeeklyDigest,
)


def _valid_kill_criteria() -> KillCriteria:
    return KillCriteria(
        max_days_to_first_dollar=30,
        min_revenue_by_day_30_usd=Decimal("100"),
        max_burn_before_first_dollar_usd=Decimal("50"),
        auto_kill_on_breach=True,
    )


def _valid_proposal() -> VerticalProposal:
    return VerticalProposal(
        title="SaaS widget for X users",
        one_line="A useful widget that solves the Y problem for Z audience.",
        problem="X" * 120,
        solution="Y" * 120,
        target_user="Indie devs who need a widget " * 2,
        revenue_channel=RevenueChannel.POLAR,
        pricing_model="subscription_monthly",
        unit_price_usd=Decimal("9.99"),
        projected_monthly_revenue_usd=Decimal("500"),
        projected_monthly_cost_usd=Decimal("40"),
        launch_budget_usd=Decimal("50"),
        kill_criteria=_valid_kill_criteria(),
        preregistration_id=uuid4(),
    )


def test_strict_model_forbids_extra():
    with pytest.raises(ValidationError):
        CashflowEntry(
            pot=Pot.OPERATING,
            delta=Decimal("1"),
            source="revenue_polar",
            bogus="extra",  # type: ignore[call-arg]
        )


def test_strict_model_is_frozen():
    entry = CashflowEntry(pot=Pot.OPERATING, delta=Decimal("1"), source="revenue_polar")
    with pytest.raises(ValidationError):
        entry.delta = Decimal("2")  # type: ignore[misc]


def test_kill_criteria_auto_kill_must_be_true():
    with pytest.raises(ValidationError):
        KillCriteria(
            max_days_to_first_dollar=30,
            min_revenue_by_day_30_usd=Decimal("0"),
            max_burn_before_first_dollar_usd=Decimal("50"),
            auto_kill_on_breach=False,
        )


def test_vertical_proposal_valid():
    prop = _valid_proposal()
    assert prop.status == "drafted"


def test_vertical_proposal_launch_budget_cap():
    with pytest.raises(ValidationError):
        VerticalProposal(
            **{**_valid_proposal().model_dump(), "launch_budget_usd": Decimal("501")}
        )


def test_ethics_verdict_rejects_non_opus():
    with pytest.raises(ValidationError):
        EthicsVerdict(
            request_id=uuid4(),
            decision="approve",
            rationale="X" * 60,
            ruleset_hash="a" * 64,
            model_used=ModelID.SONNET_46,
        )


def test_ethics_verdict_accepts_opus():
    v = EthicsVerdict(
        request_id=uuid4(),
        decision="approve",
        rationale="X" * 60,
        ruleset_hash="a" * 64,
        model_used=ModelID.OPUS_47,
    )
    assert v.decision == "approve"


def test_build_request_tool_name_pattern():
    with pytest.raises(ValidationError):
        BuildRequest(
            requested_by=AgentTier.MOTHER,
            purpose="X" * 40,
            tool_name="BadName",  # uppercase forbidden
            input_schema_json="{}",
            output_schema_json="{}",
            network_required=False,
            risk_tier="low",
        )


def test_tool_artifact_sha_pattern():
    with pytest.raises(ValidationError):
        ToolArtifact(
            build_request_id=uuid4(),
            sha256="nothex",
            code_path="x",
            test_path="y",
            passed_tests=[],
            coverage_pct=90.0,
            signed_by="code_builder_v3",
            signed_at=datetime.now(timezone.utc),
        )


def test_prereg_primary_threshold_positive():
    with pytest.raises(ValidationError):
        PreRegistration(
            vertical_title="X",
            hypothesis="X" * 60,
            primary_metric="monthly_recurring_revenue_usd",
            primary_threshold=Decimal("0"),
            measurement_window_days=30,
            analysis_plan="X" * 120,
            stopping_rule="X" * 60,
            lock_hash="a" * 64,
        )


def test_child_run_budget_cap():
    with pytest.raises(ValidationError):
        ChildRun(
            vertical_id=uuid4(),
            preregistration_id=uuid4(),
            status="live",
            monthly_budget_usd=Decimal("1001"),
        )


def test_pot_balances_round_trip():
    b = PotBalances(operating=Decimal("10"), reserve=Decimal("0"), growth=Decimal("0"))
    assert b.operating == Decimal("10")


def test_weekly_digest_fields():
    d = WeeklyDigest(
        week_start=datetime.now(timezone.utc),
        week_end=datetime.now(timezone.utc),
        pot_balances=PotBalances(
            operating=Decimal("100"), reserve=Decimal("0"), growth=Decimal("0")
        ),
        revenue_usd=Decimal("500"),
        cost_usd=Decimal("40"),
        active_children=1,
        proposals_awaiting_approval=0,
        ethics_escalations=0,
        frozen_hash_drift=False,
        human_reply_deadline=datetime.now(timezone.utc),
    )
    assert d.active_children == 1
