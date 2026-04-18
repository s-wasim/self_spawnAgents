"""Model router tests (§20 rows 26-28)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from aae.core.llm_client import BudgetExceeded, BudgetState, LLMClient
from aae.core.model_router import estimate_cost_usd, route
from aae.schemas.common import AgentTier, ModelID, TaskKind
from tests.fakes.llm import FakeLLMProvider


def test_downgrade_below_100():
    """Row 26."""
    m = route(AgentTier.MOTHER, TaskKind.GENERIC, Decimal("99"))
    assert m == ModelID.HAIKU_45
    m = route(AgentTier.MOTHER, TaskKind.PROPOSE_VERTICAL, Decimal("99"))
    assert m == ModelID.HAIKU_45


def test_ethics_uses_opus_always():
    """Row 27."""
    for pot in (Decimal("0"), Decimal("50"), Decimal("10000")):
        assert route(AgentTier.ETHICS_AUDITOR, TaskKind.GENERIC, pot) == ModelID.OPUS_47


def test_code_builder_uses_haiku():
    assert route(AgentTier.CODE_BUILDER, TaskKind.GENERIC, Decimal("1000")) == ModelID.HAIKU_45


def test_mother_opus_for_propose_vertical():
    assert route(AgentTier.MOTHER, TaskKind.PROPOSE_VERTICAL, Decimal("500")) == ModelID.OPUS_47


def test_mother_gemini_for_bulk_classify():
    assert route(AgentTier.MOTHER, TaskKind.BULK_CLASSIFY, Decimal("500")) == ModelID.GEMINI_FLASH_LITE_25


def test_mother_sonnet_default():
    assert route(AgentTier.MOTHER, TaskKind.GENERIC, Decimal("500")) == ModelID.SONNET_46


def test_estimate_cost_usd_monotonic():
    c0 = estimate_cost_usd(ModelID.HAIKU_45, 0, 0)
    c1 = estimate_cost_usd(ModelID.HAIKU_45, 1000, 1000)
    assert c1 > c0


@pytest.mark.asyncio
async def test_budget_exceeded_raises():
    """Row 28. A $6 estimated call against a $55 pot breaches the $50 floor."""
    provider = FakeLLMProvider()
    client = LLMClient(provider, cashflow=None)
    with pytest.raises(BudgetExceeded):
        await client.call(
            agent=AgentTier.MOTHER,
            task=TaskKind.GENERIC,
            system="x",
            user="y",
            max_tokens=1_000_000,
            expected_tokens_in=1_000_000,
            budget=BudgetState(operating_pot_usd=Decimal("55")),
        )


@pytest.mark.asyncio
async def test_budget_exceeded_monthly_cap():
    provider = FakeLLMProvider()
    client = LLMClient(provider, cashflow=None)
    with pytest.raises(BudgetExceeded):
        await client.call(
            agent=AgentTier.CHILD,
            task=TaskKind.GENERIC,
            system="x",
            user="y",
            max_tokens=1000,
            expected_tokens_in=1000,
            budget=BudgetState(
                operating_pot_usd=Decimal("1000"),
                monthly_budget_usd=Decimal("0.001"),
                spent_mtd_usd=Decimal("0"),
            ),
        )


@pytest.mark.asyncio
async def test_budget_ok_path():
    provider = FakeLLMProvider()
    client = LLMClient(provider, cashflow=None)
    resp = await client.call(
        agent=AgentTier.MOTHER,
        task=TaskKind.GENERIC,
        system="x",
        user="y",
        budget=BudgetState(operating_pot_usd=Decimal("1000")),
    )
    assert resp.model == ModelID.SONNET_46
    assert resp.content
