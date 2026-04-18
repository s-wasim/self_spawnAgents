"""Compute the ruleset hash for the Ethics Auditor (§12.3)."""
from __future__ import annotations

import hashlib
from pathlib import Path


def _default_prompt_path() -> Path:
    here = Path(__file__).resolve().parent
    return here / "prompt.md"


def read_frozen_prompt(path: Path | str | None = None) -> str:
    p = Path(path) if path else _default_prompt_path()
    return p.read_text(encoding="utf-8")


def frozen_prompt_hash(path: Path | str | None = None) -> str:
    p = Path(path) if path else _default_prompt_path()
    return hashlib.sha256(p.read_bytes()).hexdigest()
