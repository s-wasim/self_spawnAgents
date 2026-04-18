"""FastAPI smoke tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from aae.gmail.client import GmailMessage
from aae.server.app import create_app


def test_healthz() -> None:
    client = TestClient(create_app())
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_readyz_reports_ethics_hash() -> None:
    client = TestClient(create_app())
    r = client.get("/readyz")
    assert r.status_code == 200
    assert len(r.json()["ethics_prompt_sha256"]) == 64


def test_gmail_webhook_routes_to_parser() -> None:
    class FakeTransport:
        def list_unread(self):
            return [GmailMessage(id="g1", thread_id="t1", subject="CONTINUE", body="", from_addr="op@x")]

        def mark_read(self, mid):
            pass

        def send(self, *, to, subject, body, in_reply_to=None):
            return "sent"

    app = create_app()
    app.state.gmail_transport = FakeTransport()
    client = TestClient(app)
    envelope = {"message": {"data": "e30=", "messageId": "m"}, "subscription": "sub"}
    r = client.post("/webhooks/gmail", json=envelope)
    assert r.status_code == 200
    payload = r.json()
    assert payload["processed"] == 1
    assert payload["results"][0]["kind"] == "operator_message"
    assert payload["results"][0]["action"] == "CONTINUE"


def test_gmail_webhook_without_transport_returns_503() -> None:
    client = TestClient(create_app())
    envelope = {"message": {"data": "e30=", "messageId": "m"}, "subscription": "sub"}
    r = client.post("/webhooks/gmail", json=envelope)
    assert r.status_code == 503


def test_polar_webhook_requires_signature() -> None:
    client = TestClient(create_app())
    r = client.post("/webhooks/polar", json={})
    assert r.status_code == 401
    r = client.post("/webhooks/polar", headers={"x-polar-signature": "sig"}, json={})
    assert r.status_code == 200
