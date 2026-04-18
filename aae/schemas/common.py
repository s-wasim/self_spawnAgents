"""Shared primitives for all AAE schemas (§4.1)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    """All AAE schemas inherit this. No extra fields, frozen instances."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=False)


class Money(StrictModel):
    amount_usd: Decimal = Field(..., max_digits=12, decimal_places=4, ge=Decimal("0"))

    @field_validator("amount_usd")
    @classmethod
    def _quantize(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.0001"))


class AgentTier(str, Enum):
    MOTHER = "mother"
    CODE_BUILDER = "code_builder"
    ETHICS_AUDITOR = "ethics_auditor"
    CHILD = "child"


class ModelID(str, Enum):
    OPUS_47 = "claude-opus-4-7"
    SONNET_46 = "claude-sonnet-4-6"
    HAIKU_45 = "claude-haiku-4-5-20251001"
    GEMINI_FLASH_LITE_25 = "gemini-2.5-flash-lite"


class TaskKind(str, Enum):
    PROPOSE_VERTICAL = "propose_vertical"
    DEBUG_CHILD = "debug_child"
    BULK_CLASSIFY = "bulk_classify"
    GENERIC = "generic"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
