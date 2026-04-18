"""Gmail API client (§13.4 + §15).

Minimal wrapper around the Gmail REST API. At runtime authentication is OAuth2
with a service account — here we expose a thin protocol so tests inject a fake.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Protocol


@dataclass
class GmailMessage:
    id: str
    thread_id: str
    subject: str
    body: str
    from_addr: str
    snippet: str = ""


class GmailTransport(Protocol):
    def list_unread(self) -> list[GmailMessage]: ...
    def mark_read(self, message_id: str) -> None: ...
    def send(self, *, to: str, subject: str, body: str, in_reply_to: str | None = None) -> str: ...


def decode_body(b64: str) -> str:
    """Gmail encodes bodies as URL-safe base64."""
    pad = "=" * (-len(b64) % 4)
    return base64.urlsafe_b64decode((b64 + pad).encode()).decode("utf-8", errors="replace")
