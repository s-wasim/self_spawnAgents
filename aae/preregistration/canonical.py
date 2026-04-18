"""Canonical-JSON encoder (§10.3). FROZEN.

Rules:
  * UTF-8, no BOM.
  * Sorted keys at every level.
  * Floats forbidden — use Decimal serialized as string.
  * No whitespace except a single trailing \\n.
  * Hash: SHA-256 hex lowercase.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


def _default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime | date):
        return obj.isoformat()
    raise TypeError(f"Not JSON-serializable: {type(obj).__name__}")


def _ban_floats(obj: Any) -> None:
    if isinstance(obj, float):
        raise TypeError("Canonical JSON forbids float — use Decimal")
    if isinstance(obj, dict):
        for v in obj.values():
            _ban_floats(v)
    elif isinstance(obj, list | tuple):
        for v in obj:
            _ban_floats(v)


def canonical_dumps(obj: Any) -> str:
    """Return the canonical representation of obj, including trailing newline."""
    _ban_floats(obj)
    body = json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=_default,
        allow_nan=False,
    )
    return body + "\n"


def canonical_bytes(obj: Any) -> bytes:
    return canonical_dumps(obj).encode("utf-8")


def canonical_hash(obj: Any) -> str:
    """Return sha256 hex-lowercase of the canonical representation of obj."""
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()
