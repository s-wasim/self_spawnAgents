"""Ethics Auditor tests (§20 rows 12-16)."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aae.ethics.auditor import EthicsService
from aae.ethics.ruleset_hash import frozen_prompt_hash
from aae.schemas.common import ModelID
from aae.schemas.ethics import EthicsReviewRequest, EthicsVerdict
from tests.fakes.llm import FakeLLMProvider


def _req(payload: dict) -> EthicsReviewRequest:
    return EthicsReviewRequest(
        subject_type="vertical_proposal",
        subject_id=uuid4(),
        payload_json=json.dumps(payload),
    )


def test_verdict_validator_opus_only():
    """Row 12."""
    with pytest.raises(ValidationError):
        EthicsVerdict(
            request_id=uuid4(),
            decision="approve",
            rationale="a" * 60,
            ruleset_hash="0" * 64,
            model_used=ModelID.HAIKU_45,
        )


@pytest.mark.asyncio
async def test_approve_happy_path():
    provider = FakeLLMProvider()
    svc = EthicsService(provider)
    verdict = await svc.review(_req({"title": "A benign SaaS widget"}))
    assert verdict.decision == "approve"
    assert verdict.model_used == ModelID.OPUS_47
    assert verdict.ruleset_hash == frozen_prompt_hash()


@pytest.mark.asyncio
async def test_reject_on_banned_category():
    """Row 13."""
    provider = FakeLLMProvider(
        default_content=json.dumps({
            "decision": "reject",
            "rationale": ("Product is an AI companion targeting vulnerable users, "
                          "which violates Polar.sh AUP category 2 and is auto-reject."),
        })
    )
    svc = EthicsService(provider)
    verdict = await svc.review(_req({"title": "AI girlfriend"}))
    assert verdict.decision == "reject"


@pytest.mark.asyncio
async def test_concurrent_calls_serialized():
    """Row 14. Single-flight via asyncio.Lock."""
    call_order: list[str] = []

    class CountingProvider:
        async def call(self, *, model, system, user, max_tokens):
            call_order.append("start")
            await asyncio.sleep(0.01)
            call_order.append("end")
            return FakeLLMProvider().default_content, 100, 100

        async def complete(self, *, model, system, user):
            call_order.append("start")
            await asyncio.sleep(0.01)
            call_order.append("end")
            return FakeLLMProvider().default_content

    svc = EthicsService(CountingProvider())
    reqs = [_req({"title": f"prop-{i}"}) for i in range(3)]
    await asyncio.gather(*(svc.review(r) for r in reqs))
    # start/end should strictly alternate since single-flight.
    for i in range(0, len(call_order), 2):
        assert call_order[i] == "start"
        assert call_order[i + 1] == "end"


@pytest.mark.asyncio
async def test_cached_reject_not_requeried():
    """Row 15. A rejected verdict must be cached by (subject_type, subject_id)."""
    class Provider:
        calls = 0
        default_content = json.dumps({
            "decision": "reject",
            "rationale": "Reject for test reasons that make the rationale 60+ chars long. X X X X X X",
        })

        async def complete(self, *, model, system, user):
            Provider.calls += 1
            return self.default_content

    svc = EthicsService(Provider())
    req = _req({"title": "same"})
    await svc.review(req)
    # Re-ask the SAME request id's subject_id by rebuilding a request with the same subject_id.
    req2 = EthicsReviewRequest(
        subject_type=req.subject_type,
        subject_id=req.subject_id,
        payload_json=req.payload_json,
    )
    v2 = await svc.review(req2)
    assert v2.decision == "reject"
    assert Provider.calls == 1


def test_ruleset_hash_matches_prompt_md():
    """Row 16."""
    p = Path(__file__).resolve().parent.parent / "aae/ethics/prompt.md"
    import hashlib
    assert frozen_prompt_hash() == hashlib.sha256(p.read_bytes()).hexdigest()
