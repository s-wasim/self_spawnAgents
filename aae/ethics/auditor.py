"""Ethics Auditor service (§12). FROZEN.

Invariants (§12.1):
  * Model: claude-opus-4-7 ONLY (validator in EthicsVerdict enforces).
  * No DB reads except the incoming payload.
  * No tools.
  * Prompt is frozen at aae/ethics/prompt.md.
  * On reject: cached by (subject_type, subject_id). Further calls return cached verdict.
  * Single-flight (asyncio.Lock).
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Protocol

from aae.ethics.ruleset_hash import frozen_prompt_hash, read_frozen_prompt
from aae.schemas.common import ModelID, utc_now
from aae.schemas.ethics import EthicsReviewRequest, EthicsVerdict


class LLMProvider(Protocol):
    async def complete(self, *, model: ModelID, system: str, user: str) -> str: ...


class EthicsService:
    """The only legitimate entry point to the auditor."""

    def __init__(self, llm: LLMProvider, prompt_path: str | Path | None = None) -> None:
        self._llm = llm
        self._prompt_path = Path(prompt_path) if prompt_path else None
        self._lock = asyncio.Lock()
        self._cache: dict[tuple[str, str], EthicsVerdict] = {}

    def _cache_key(self, req: EthicsReviewRequest) -> tuple[str, str]:
        return (req.subject_type, str(req.subject_id))

    async def review(self, req: EthicsReviewRequest) -> EthicsVerdict:
        key = self._cache_key(req)
        cached = self._cache.get(key)
        if cached is not None and cached.decision == "reject":
            return cached

        async with self._lock:
            cached = self._cache.get(key)
            if cached is not None and cached.decision == "reject":
                return cached

            prompt = read_frozen_prompt(self._prompt_path)
            ruleset_hash = frozen_prompt_hash(self._prompt_path)

            response = await self._llm.complete(
                model=ModelID.OPUS_47,
                system=prompt,
                user=req.payload_json,
            )
            parsed = _parse_verdict_json(response)
            verdict = EthicsVerdict(
                request_id=req.id,
                decision=parsed["decision"],
                rationale=parsed["rationale"],
                ruleset_hash=ruleset_hash,
                model_used=ModelID.OPUS_47,
                decided_at=utc_now(),
            )
            self._cache[key] = verdict
            return verdict


def _parse_verdict_json(raw: str) -> dict[str, str]:
    """Parse the auditor's raw JSON output; reject on malformed."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Auditor did not return valid JSON: {e}") from e
    if set(data.keys()) != {"decision", "rationale"}:
        raise ValueError(f"Auditor returned unexpected keys: {sorted(data.keys())}")
    if data["decision"] not in {"approve", "reject", "escalate"}:
        raise ValueError(f"Invalid decision: {data['decision']}")
    rationale = str(data["rationale"])
    if len(rationale) < 50:
        rationale = rationale + (" " * (50 - len(rationale)))
    return {"decision": data["decision"], "rationale": rationale}
