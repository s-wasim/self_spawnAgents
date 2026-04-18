"""Deterministic SHA-256 signer for tool artifacts (§9.4).

sha256 = SHA256( tool.py bytes + test_tool.py bytes + canonical_dumps(BuildRequest) )
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from aae.preregistration.canonical import canonical_dumps
from aae.schemas.build import BuildRequest


def compute_artifact_sha(*, tool_py: bytes, test_py: bytes, build_request: BuildRequest) -> str:
    h = hashlib.sha256()
    h.update(tool_py)
    h.update(test_py)
    # Pydantic → dict → canonical JSON (stable across Python versions).
    h.update(canonical_dumps(build_request.model_dump(mode="json")).encode("utf-8"))
    return h.hexdigest()


def write_artifact_files(
    *,
    target_root: Path,
    tool_py: bytes,
    test_py: bytes,
    build_request: BuildRequest,
) -> tuple[Path, Path, str]:
    sha = compute_artifact_sha(tool_py=tool_py, test_py=test_py, build_request=build_request)
    out_dir = target_root / sha
    out_dir.mkdir(parents=True, exist_ok=True)
    tool_path = out_dir / "tool.py"
    test_path = out_dir / "test_tool.py"
    tool_path.write_bytes(tool_py)
    test_path.write_bytes(test_py)
    return tool_path, test_path, sha
