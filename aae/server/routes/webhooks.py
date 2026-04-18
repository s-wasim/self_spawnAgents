"""Webhook endpoints (Gmail push, Polar, LemonSqueezy, Stripe)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from aae.core.operator_parser import FormLetter, OperatorMessage
from aae.gmail.client import GmailTransport
from aae.gmail.webhook import handle_push

router = APIRouter()


# Gmail push webhook. Transport is injected via app.state.gmail_transport.
@router.post("/webhooks/gmail")
async def gmail_push(request: Request) -> dict[str, Any]:
    envelope = await request.json()
    transport: GmailTransport | None = getattr(request.app.state, "gmail_transport", None)
    if transport is None:
        raise HTTPException(status_code=503, detail="gmail transport not configured")
    results = handle_push(envelope, transport)
    out: list[dict[str, Any]] = []
    for r in results:
        if isinstance(r, OperatorMessage):
            out.append({"kind": "operator_message", "action": r.action})
        elif isinstance(r, FormLetter):
            out.append({"kind": "form_letter", "reason": r.reason})
    return {"processed": len(results), "results": out}


@router.post("/webhooks/polar")
async def polar_webhook(
    request: Request,
    x_polar_signature: str | None = Header(default=None),
) -> dict[str, str]:
    # Production: use PolarClient.webhook_verify with the store secret.
    if x_polar_signature is None:
        raise HTTPException(status_code=401, detail="missing signature")
    _ = await request.body()
    return {"status": "accepted"}


@router.post("/webhooks/lemonsqueezy")
async def lemonsqueezy_webhook(
    request: Request,
    x_signature: str | None = Header(default=None),
) -> dict[str, str]:
    if x_signature is None:
        raise HTTPException(status_code=401, detail="missing signature")
    _ = await request.body()
    return {"status": "accepted"}


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None),
) -> dict[str, str]:
    if stripe_signature is None:
        raise HTTPException(status_code=401, detail="missing signature")
    _ = await request.body()
    return {"status": "accepted"}
