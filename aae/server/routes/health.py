"""Health + readiness endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from aae.ethics.ruleset_hash import frozen_prompt_hash

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@router.get("/readyz")
async def readyz() -> dict:
    return {
        "status": "ready",
        "ethics_prompt_sha256": frozen_prompt_hash(),
    }
