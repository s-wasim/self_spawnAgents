"""Frozen paths registry (§11.1). Any diff here trips the integrity alarm."""
from __future__ import annotations

FROZEN_PATHS: tuple[str, ...] = (
    "aae/ethics/prompt.md",
    "aae/ethics/auditor.py",
    "aae/cashflow/hard_floors.py",
    "aae/config/frozen/expansion_rungs.py",
    "aae/config/frozen/model_routing.py",
    "aae/preregistration/schema.py",
    "aae/preregistration/canonical.py",
    "aae/core/trust_boundary.py",
)

HASHES_LOCK_FILE = "aae/config/frozen/hashes.lock"
