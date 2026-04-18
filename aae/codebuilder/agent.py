"""Code Builder agent (§9).

Stateless orchestrator. For a `BuildRequest`:
  1. Render tool.py / test_tool.py (Jinja).
  2. Apply policy checks (§9.5) → auto-escalate risk_tier.
  3. Write into a scratch dir, run sandbox.
  4. Validate pytest output.
  5. Sign → ToolArtifact, or produce BuildFailure.
"""
from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from jinja2 import Environment, FileSystemLoader, select_autoescape

from aae.codebuilder.sandbox import SandboxRunner
from aae.codebuilder.signer import compute_artifact_sha, write_artifact_files
from aae.codebuilder.validator import validate
from aae.schemas.build import BuildFailure, BuildRequest, ToolArtifact

TEMPLATE_DIR = Path(__file__).parent / "templates"
GENERATED_ROOT = Path(__file__).resolve().parents[1] / "tools" / "generated"

FORBIDDEN_IMPORTS = ("subprocess", "os.system", "socket", "ctypes", "pickle")
PII_FIELDS = ("email", "ssn", "passport", "dob", "address")


@dataclass
class BuildOutcome:
    status: Literal["artifact", "failure"]
    artifact: ToolArtifact | None = None
    failure: BuildFailure | None = None


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(enabled_extensions=()),
        keep_trailing_newline=True,
    )


def render(req: BuildRequest) -> tuple[bytes, bytes]:
    env = _env()
    ctx = {
        "tool_name": req.tool_name,
        "purpose": req.purpose,
        "risk_tier": req.risk_tier,
        "network_required": req.network_required,
        "input_schema_json": req.input_schema_json,
        "output_schema_json": req.output_schema_json,
    }
    tool_py = env.get_template("tool_skeleton.py.j2").render(**ctx).encode()
    test_py = env.get_template("test_skeleton.py.j2").render(**ctx).encode()
    return tool_py, test_py


def policy_escalate(req: BuildRequest, tool_source: bytes) -> BuildRequest:
    """§9.5 auto-escalate to high risk if any red flag is present."""
    src = tool_source.decode("utf-8", errors="ignore")
    reasons: list[str] = []
    if any(f"import {m}" in src or f"from {m}" in src for m in FORBIDDEN_IMPORTS):
        reasons.append("forbidden_import")
    try:
        schema = json.loads(req.input_schema_json)
        props = schema.get("properties", {}) if isinstance(schema, dict) else {}
        if any(p in props for p in PII_FIELDS):
            reasons.append("pii_field")
    except Exception:
        pass
    if req.network_required and not req.allowed_domains:
        reasons.append("open_network")
    if reasons and req.risk_tier != "high":
        return req.model_copy(update={"risk_tier": "high"})
    return req


def build(
    req: BuildRequest,
    *,
    runner: SandboxRunner,
    target_root: Path | None = None,
) -> BuildOutcome:
    target = target_root or GENERATED_ROOT
    tool_py, test_py = render(req)
    req = policy_escalate(req, tool_py)
    sha_preview = compute_artifact_sha(tool_py=tool_py, test_py=test_py, build_request=req)
    with tempfile.TemporaryDirectory(prefix=f"cb-{sha_preview[:12]}-") as td:
        td_path = Path(td)
        (td_path / "tool.py").write_bytes(tool_py)
        (td_path / "test_tool.py").write_bytes(test_py)
        result = runner.run(td_path, wall_seconds=req.max_wall_seconds)
    if result.reason == "timeout":
        return BuildOutcome(
            status="failure",
            failure=BuildFailure(
                build_request_id=req.id,
                reason="sandbox_timeout",
                detail=f"wall={result.wall_seconds:.1f}s stderr={result.stderr[:500]}",
                attempts=1,
            ),
        )
    if result.exit_code != 0:
        return BuildOutcome(
            status="failure",
            failure=BuildFailure(
                build_request_id=req.id,
                reason="tests_failed",
                detail=f"exit={result.exit_code} {result.stderr[:500] or result.stdout[:500]}",
                attempts=1,
            ),
        )
    v = validate(result.stdout)
    if not v.ok:
        return BuildOutcome(
            status="failure",
            failure=BuildFailure(
                build_request_id=req.id,
                reason="tests_failed" if v.failed_tests else "coverage_below_threshold",
                detail=result.stdout[:500],
                attempts=1,
            ),
        )
    tool_path, test_path, sha = write_artifact_files(
        target_root=target,
        tool_py=tool_py,
        test_py=test_py,
        build_request=req,
    )
    artifact = ToolArtifact(
        build_request_id=req.id,
        sha256=sha,
        code_path=str(tool_path),
        test_path=str(test_path),
        passed_tests=v.passed_tests,
        coverage_pct=max(v.coverage_pct, 0.0),
        signed_by="code_builder_v3",
        signed_at=datetime.now(timezone.utc),
    )
    return BuildOutcome(status="artifact", artifact=artifact)
