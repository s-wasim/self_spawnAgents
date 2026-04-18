"""Rows 22 & 23: artifact SHA determinism + high-risk ethics gate."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from aae.codebuilder.agent import build, render
from aae.codebuilder.signer import compute_artifact_sha
from aae.schemas.build import BuildRequest, ToolArtifact
from aae.tools.registry import ToolPolicyError, ToolRegistry
from aae.tools.runtime import DomainNotAllowed, enforce_domain, invoke

from tests.fakes.sandbox import FakeSandboxRunner


def _req(**over) -> BuildRequest:
    d = dict(
        requested_by="mother",
        purpose="Compute daily revenue for newsletter vertical aggregates.",
        tool_name="rev_aggregator",
        input_schema_json=json.dumps({"type": "object"}),
        output_schema_json=json.dumps({"type": "object"}),
        network_required=False,
        allowed_domains=[],
        risk_tier="low",
    )
    d.update(over)
    return BuildRequest(**d)


def test_artifact_sha_determinism() -> None:
    # Row 22: same inputs → identical sha; tiny input change → different sha.
    req = _req()
    t, s = render(req)
    assert compute_artifact_sha(tool_py=t, test_py=s, build_request=req) \
        == compute_artifact_sha(tool_py=t, test_py=s, build_request=req)
    t2 = t + b"\n# comment\n"
    assert compute_artifact_sha(tool_py=t2, test_py=s, build_request=req) != \
        compute_artifact_sha(tool_py=t, test_py=s, build_request=req)


def test_high_risk_blocked_without_verdict(tmp_path: Path) -> None:
    # Row 23: registering a high-risk tool without ethics_verdict_id is rejected.
    req = _req(risk_tier="high", network_required=True, allowed_domains=["api.polar.sh"])
    out = build(req, runner=FakeSandboxRunner(mode="pass"), target_root=tmp_path)
    assert out.status == "artifact"
    assert out.artifact.ethics_verdict_id is None
    reg = ToolRegistry()
    with pytest.raises(ToolPolicyError, match="high-risk"):
        reg.register(artifact=out.artifact, build_request=req)


def test_high_risk_registers_with_verdict(tmp_path: Path) -> None:
    req = _req(risk_tier="high", network_required=True, allowed_domains=["api.polar.sh"])
    out = build(req, runner=FakeSandboxRunner(mode="pass"), target_root=tmp_path)
    # attach a dummy ethics verdict id
    approved = out.artifact.model_copy(update={"ethics_verdict_id": uuid4()})
    reg = ToolRegistry()
    rt = reg.register(artifact=approved, build_request=req)
    assert rt.risk_tier == "high"
    assert rt.ethics_verdict_id


def test_registry_uses_sha_key_not_name(tmp_path: Path) -> None:
    req = _req()
    out = build(req, runner=FakeSandboxRunner(mode="pass"), target_root=tmp_path)
    reg = ToolRegistry()
    reg.register(artifact=out.artifact, build_request=req)
    assert reg.get(out.artifact.sha256).name == "rev_aggregator"
    with pytest.raises(ToolPolicyError):
        reg.get("deadbeef" * 8)  # not 64 hex chars but still missing


def test_retire_marks_status(tmp_path: Path) -> None:
    req = _req()
    out = build(req, runner=FakeSandboxRunner(mode="pass"), target_root=tmp_path)
    reg = ToolRegistry()
    reg.register(artifact=out.artifact, build_request=req)
    retired = reg.retire(out.artifact.sha256)
    assert retired.status == "retired"
    assert retired.retired_at is not None


def test_runtime_invokes_tool(tmp_path: Path) -> None:
    req = _req()
    out = build(req, runner=FakeSandboxRunner(mode="pass"), target_root=tmp_path)
    reg = ToolRegistry()
    reg.register(artifact=out.artifact, build_request=req)
    result, wall = invoke(reg, sha=out.artifact.sha256, payload={"a": 1, "b": 2})
    assert result == {"echoed_keys": ["a", "b"]}
    assert wall >= 0.0


def test_runtime_rejects_retired(tmp_path: Path) -> None:
    req = _req()
    out = build(req, runner=FakeSandboxRunner(mode="pass"), target_root=tmp_path)
    reg = ToolRegistry()
    reg.register(artifact=out.artifact, build_request=req)
    reg.retire(out.artifact.sha256)
    with pytest.raises(ToolPolicyError, match="retired"):
        invoke(reg, sha=out.artifact.sha256, payload={})


def test_enforce_domain_allowlist() -> None:
    enforce_domain("https://api.polar.sh/v1/orgs", ("api.polar.sh",))
    enforce_domain("https://sub.api.polar.sh/x", ("api.polar.sh",))
    with pytest.raises(DomainNotAllowed):
        enforce_domain("https://evil.example.com", ("api.polar.sh",))
