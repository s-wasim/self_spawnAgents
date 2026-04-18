"""Build request / tool artifact schemas (§4.4)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field

from aae.schemas.common import AgentTier, StrictModel, utc_now


class BuildRequest(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    requested_by: AgentTier
    purpose: str = Field(..., min_length=20, max_length=1000)
    tool_name: str = Field(..., pattern=r"^[a-z][a-z0-9_]{2,48}$")
    input_schema_json: str
    output_schema_json: str
    network_required: bool
    allowed_domains: list[str] = Field(default_factory=list, max_length=20)
    risk_tier: Literal["low", "medium", "high"]
    max_wall_seconds: int = Field(default=300, ge=1, le=300)
    created_at: datetime = Field(default_factory=utc_now)


class ToolArtifact(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    build_request_id: UUID
    sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    code_path: str
    test_path: str
    passed_tests: list[str]
    coverage_pct: float = Field(..., ge=0.0, le=100.0)
    signed_by: Literal["code_builder_v3"]
    signed_at: datetime
    ethics_verdict_id: UUID | None = None


class BuildFailure(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    build_request_id: UUID
    reason: Literal[
        "tests_failed", "sandbox_timeout", "policy_violation",
        "schema_invalid", "coverage_below_threshold", "lint_failed",
    ]
    detail: str = Field(..., max_length=4000)
    attempts: int = Field(..., ge=1, le=3)
