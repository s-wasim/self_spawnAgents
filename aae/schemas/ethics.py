"""Ethics review schemas (§4.5)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from aae.schemas.common import ModelID, StrictModel, utc_now


class EthicsReviewRequest(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    subject_type: Literal["vertical_proposal", "tool_artifact"]
    subject_id: UUID
    payload_json: str
    created_at: datetime = Field(default_factory=utc_now)


class EthicsVerdict(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    decision: Literal["approve", "reject", "escalate"]
    rationale: str = Field(..., min_length=50, max_length=4000)
    ruleset_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    model_used: ModelID
    decided_at: datetime = Field(default_factory=utc_now)

    @field_validator("model_used")
    @classmethod
    def _only_opus(cls, v: ModelID) -> ModelID:
        if v != ModelID.OPUS_47:
            raise ValueError("Ethics Auditor must use Opus 4.7 only")
        return v
