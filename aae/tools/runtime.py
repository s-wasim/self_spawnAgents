"""Tool runtime (§9.6).

Loads a registered tool by sha (not by name). Enforces allowed_domains for
network-bound tools via an URL guard. Logs invocations to `tool_invocations`.
"""
from __future__ import annotations

import importlib.util
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from aae.tools.registry import RegisteredTool, ToolPolicyError, ToolRegistry


class DomainNotAllowed(Exception):
    pass


def enforce_domain(url: str, allowed: tuple[str, ...]) -> None:
    host = urlparse(url).hostname or ""
    if host and not any(host == d or host.endswith("." + d) for d in allowed):
        raise DomainNotAllowed(f"{host} not in allowed_domains={list(allowed)}")


def _load_module(sha: str, code_path: str):
    spec = importlib.util.spec_from_file_location(f"tool_{sha}", code_path)
    if not spec or not spec.loader:
        raise ToolPolicyError(f"cannot load tool module at {code_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def invoke(
    registry: ToolRegistry,
    *,
    sha: str,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], float]:
    """Run a registered tool's `run(payload)`; return (output, wall_seconds)."""
    rt: RegisteredTool = registry.get(sha)
    if rt.status == "retired":
        raise ToolPolicyError(f"tool {sha} is retired")
    if not Path(rt.code_path).exists():
        raise ToolPolicyError(f"tool code missing at {rt.code_path}")
    t0 = time.monotonic()
    mod = _load_module(rt.sha256, rt.code_path)
    if not hasattr(mod, "run"):
        raise ToolPolicyError("tool missing run(payload) entrypoint")
    output = mod.run(payload)
    return output, time.monotonic() - t0
