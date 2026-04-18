"""Model router (§13.2)."""
from __future__ import annotations

from decimal import Decimal

from aae.config.frozen.model_routing import (
    OPERATING_LOW_WATER_MARK_USD,
    PRICE_TABLE,
)
from aae.schemas.common import AgentTier, ModelID, TaskKind


def route(agent: AgentTier, task: TaskKind, operating_pot_usd: Decimal) -> ModelID:
    """Return the ModelID the LLM client should use for this (agent, task)."""
    if agent == AgentTier.ETHICS_AUDITOR:
        return ModelID.OPUS_47  # invariant — regardless of pot
    if agent == AgentTier.CODE_BUILDER:
        return ModelID.HAIKU_45
    # Mother / Children
    if operating_pot_usd < OPERATING_LOW_WATER_MARK_USD:
        return ModelID.HAIKU_45
    if task in {TaskKind.PROPOSE_VERTICAL, TaskKind.DEBUG_CHILD}:
        return ModelID.OPUS_47
    if task == TaskKind.BULK_CLASSIFY:
        return ModelID.GEMINI_FLASH_LITE_25
    return ModelID.SONNET_46


def estimate_cost_usd(model: ModelID, tokens_in: int, tokens_out: int) -> Decimal:
    price_in, price_out = PRICE_TABLE[model]
    return (
        (Decimal(tokens_in) * price_in + Decimal(tokens_out) * price_out)
        / Decimal("1000000")
    ).quantize(Decimal("0.000001"))
