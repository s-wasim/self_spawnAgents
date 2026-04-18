"""Row 39: Gmail push delivery → /webhooks/gmail → parser → action."""
from __future__ import annotations

from fastapi.testclient import TestClient

from aae.gmail.client import GmailMessage
from aae.server.app import create_app


class FakeGmailTransport:
    """In-memory Gmail transport for the round-trip test."""

    def __init__(self, messages: list[GmailMessage]) -> None:
        self.messages = list(messages)
        self.read: list[str] = []
        self.sent: list[dict] = []

    def list_unread(self) -> list[GmailMessage]:
        return [m for m in self.messages if m.id not in self.read]

    def mark_read(self, mid: str) -> None:
        self.read.append(mid)

    def send(self, *, to: str, subject: str, body: str, in_reply_to: str | None = None) -> str:
        self.sent.append({"to": to, "subject": subject, "body": body, "in_reply_to": in_reply_to})
        return f"sent-{len(self.sent)}"


def _envelope() -> dict:
    # base64("{}") = "e30="
    return {
        "message": {"data": "e30=", "messageId": "push-1"},
        "subscription": "projects/p/subscriptions/s",
    }


def test_push_parsed() -> None:
    """Row 39: a Pub/Sub push routes an APPROVE + KILL ALL through the parser."""
    pid = "11111111-2222-3333-4444-555555555555"
    cid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    msgs = [
        GmailMessage(id="g1", thread_id="t1", subject=f"APPROVE {pid}", body="", from_addr="op@x"),
        GmailMessage(id="g2", thread_id="t2", subject="KILL ALL", body="", from_addr="op@x"),
        GmailMessage(id="g3", thread_id="t3", subject="NONSENSE here", body="", from_addr="op@x"),
        GmailMessage(id="g4", thread_id="t4", subject=f"KILL {cid}", body="", from_addr="op@x"),
    ]
    transport = FakeGmailTransport(msgs)
    app = create_app()
    app.state.gmail_transport = transport
    client = TestClient(app)

    r = client.post("/webhooks/gmail", json=_envelope())
    assert r.status_code == 200
    payload = r.json()
    assert payload["processed"] == 4

    kinds = [(x["kind"], x.get("action") or x.get("reason")) for x in payload["results"]]
    assert ("operator_message", "APPROVE") in kinds
    assert ("operator_message", "KILL_ALL") in kinds
    assert ("operator_message", "KILL_CHILD") in kinds
    # one form letter for NONSENSE
    assert any(k == "form_letter" for k, _ in kinds)

    # All unread messages are now marked read
    assert set(transport.read) == {"g1", "g2", "g3", "g4"}


def test_push_without_transport_503() -> None:
    client = TestClient(create_app())
    r = client.post("/webhooks/gmail", json=_envelope())
    assert r.status_code == 503
