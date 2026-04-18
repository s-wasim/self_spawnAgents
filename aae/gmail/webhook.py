"""Gmail Pub/Sub push-webhook handler (§13.4).

Pub/Sub POSTs a JWT-signed envelope containing a Gmail historyId. We fetch new
messages, run them through operator_parser, and emit an OperatorMessage or
FormLetter for the Mother Agent to act on.
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

from aae.core.operator_parser import FormLetter, OperatorMessage, ParseResult, parse
from aae.gmail.client import GmailMessage, GmailTransport


@dataclass
class PushEnvelope:
    message_data: dict[str, Any]
    message_id: str
    subscription: str


def decode_push(envelope: dict[str, Any]) -> PushEnvelope:
    msg = envelope.get("message", {})
    data_b64 = msg.get("data", "")
    pad = "=" * (-len(data_b64) % 4)
    payload = json.loads(base64.b64decode((data_b64 + pad).encode()).decode())
    return PushEnvelope(
        message_data=payload,
        message_id=msg.get("messageId", ""),
        subscription=envelope.get("subscription", ""),
    )


def handle_push(envelope: dict[str, Any], transport: GmailTransport) -> list[ParseResult]:
    """Entry point for FastAPI; returns parsed messages to process."""
    decode_push(envelope)  # validate shape; historyId-driven fetch is production-side
    parsed: list[ParseResult] = []
    for m in transport.list_unread():
        result = parse(m.subject, m.body)
        parsed.append(result)
        transport.mark_read(m.id)
    return parsed


def form_letter_body(form: FormLetter) -> str:
    """Canned reply when the operator message doesn't match grammar."""
    lines = [
        "Sorry — your message didn't match any of the allowed commands.",
        f"Reason: {form.reason}",
        "",
        "Allowed commands:",
    ]
    for verb in form.allowed_verbs:
        lines.append(f"  {verb}")
    return "\n".join(lines)
