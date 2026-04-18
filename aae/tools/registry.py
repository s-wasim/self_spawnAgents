"""Tool registry (§9.6).

Only place production tools are registered. Keys tools by sha256 (not name) to
prevent shadow-swap. Enforces `ethics_verdict_id` for risk_tier=high. Exposes
a lookup + a guarded register.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from aae.schemas.build import BuildRequest, ToolArtifact


class ToolPolicyError(Exception):
    pass


@dataclass(frozen=True)
class RegisteredTool:
    sha256: str
    name: str
    risk_tier: Literal["low", "medium", "high"]
    code_path: str
    test_path: str
    build_request_id: str
    ethics_verdict_id: str | None
    allowed_domains: tuple[str, ...]
    registered_at: datetime
    status: Literal["registered", "retired"] = "registered"
    retired_at: datetime | None = None


@dataclass
class ToolRegistry:
    by_sha: dict[str, RegisteredTool] = field(default_factory=dict)

    def register(
        self,
        *,
        artifact: ToolArtifact,
        build_request: BuildRequest,
    ) -> RegisteredTool:
        if artifact.build_request_id != build_request.id:
            raise ToolPolicyError("artifact/build_request id mismatch")
        if build_request.risk_tier == "high" and artifact.ethics_verdict_id is None:
            raise ToolPolicyError("high-risk tool requires ethics_verdict_id")
        rt = RegisteredTool(
            sha256=artifact.sha256,
            name=build_request.tool_name,
            risk_tier=build_request.risk_tier,
            code_path=artifact.code_path,
            test_path=artifact.test_path,
            build_request_id=str(build_request.id),
            ethics_verdict_id=(
                str(artifact.ethics_verdict_id) if artifact.ethics_verdict_id else None
            ),
            allowed_domains=tuple(build_request.allowed_domains),
            registered_at=datetime.now(timezone.utc),
        )
        self.by_sha[artifact.sha256] = rt
        return rt

    def get(self, sha: str) -> RegisteredTool:
        if sha not in self.by_sha:
            raise ToolPolicyError(f"unknown tool sha {sha}")
        return self.by_sha[sha]

    def retire(self, sha: str) -> RegisteredTool:
        rt = self.get(sha)
        retired = RegisteredTool(
            **{**rt.__dict__, "status": "retired", "retired_at": datetime.now(timezone.utc)}
        )
        self.by_sha[sha] = retired
        return retired
