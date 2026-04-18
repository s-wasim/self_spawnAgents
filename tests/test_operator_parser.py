"""Rows 29 & 30: operator-parser happy path + form-letter on malformed."""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from aae.core.operator_parser import (
    FormLetter,
    OperatorMessage,
    parse,
)


def test_approve_happy_path() -> None:
    pid = uuid4()
    r = parse(f"APPROVE {pid}")
    assert isinstance(r, OperatorMessage)
    assert r.action == "APPROVE"
    assert r.subject_id == pid
    assert len(r.raw_sha256) == 64


def test_malformed_rejected() -> None:
    r = parse("approve the plan now")
    assert isinstance(r, FormLetter)
    assert "APPROVE" in r.allowed_verbs[0]


def test_case_insensitive_verb() -> None:
    pid = uuid4()
    r = parse(f"approve {pid}")
    assert isinstance(r, OperatorMessage)
    assert r.action == "APPROVE"


def test_reject_with_body_excerpt() -> None:
    pid = uuid4()
    r = parse(f"REJECT {pid}", body="Too risky for this cohort.")
    assert isinstance(r, OperatorMessage)
    assert r.action == "REJECT"
    assert "Too risky" in r.body_excerpt


def test_continue_pause() -> None:
    r1 = parse("CONTINUE")
    r2 = parse("PAUSE")
    assert isinstance(r1, OperatorMessage) and r1.action == "CONTINUE"
    assert isinstance(r2, OperatorMessage) and r2.action == "PAUSE"


def test_continue_rejects_arguments() -> None:
    r = parse("CONTINUE now")
    assert isinstance(r, FormLetter)


def test_kill_all_and_kill_child() -> None:
    cid = uuid4()
    r_all = parse("KILL ALL")
    r_child = parse(f"KILL {cid}")
    assert isinstance(r_all, OperatorMessage) and r_all.action == "KILL_ALL"
    assert isinstance(r_child, OperatorMessage) and r_child.action == "KILL_CHILD"
    assert r_child.subject_id == cid


def test_kill_bad_arg() -> None:
    r = parse("KILL now")
    assert isinstance(r, FormLetter)


def test_emergency_transfer_shape() -> None:
    r = parse("EMERGENCY_TRANSFER 250.00 reserve->operating")
    assert isinstance(r, OperatorMessage)
    assert r.action == "EMERGENCY_TRANSFER"
    assert r.amount_usd == Decimal("250.00")


def test_emergency_transfer_wrong_direction() -> None:
    r = parse("EMERGENCY_TRANSFER 100 operating->reserve")
    assert isinstance(r, FormLetter)


def test_emergency_transfer_bad_amount() -> None:
    r = parse("EMERGENCY_TRANSFER eleven reserve->operating")
    assert isinstance(r, FormLetter)


def test_empty_subject_rejected() -> None:
    r = parse("")
    assert isinstance(r, FormLetter)


def test_unknown_verb_rejected() -> None:
    r = parse("NUKE everything")
    assert isinstance(r, FormLetter)
    assert "unknown_verb" in r.reason


def test_raw_sha_is_deterministic() -> None:
    pid = uuid4()
    a = parse(f"APPROVE {pid}")
    b = parse(f"APPROVE {pid}")
    assert isinstance(a, OperatorMessage) and isinstance(b, OperatorMessage)
    assert a.raw_sha256 == b.raw_sha256


# ---- Gmail webhook: form_letter_body + decode_push ----

def test_form_letter_body_lists_verbs() -> None:
    from aae.gmail.webhook import form_letter_body

    r = parse("bogus")
    assert isinstance(r, FormLetter)
    text = form_letter_body(r)
    assert "APPROVE" in text
    assert "EMERGENCY_TRANSFER" in text


def test_decode_push_parses_pubsub_envelope() -> None:
    import base64
    import json
    from aae.gmail.webhook import decode_push

    payload = {"emailAddress": "op@example.com", "historyId": "42"}
    b64 = base64.b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    envelope = {
        "message": {"data": b64, "messageId": "m1"},
        "subscription": "projects/p/subscriptions/s",
    }
    e = decode_push(envelope)
    assert e.message_data == payload
    assert e.message_id == "m1"


def test_handle_push_parses_unread() -> None:
    from aae.gmail.client import GmailMessage
    from aae.gmail.webhook import handle_push

    class FakeTransport:
        def __init__(self) -> None:
            self.read: list[str] = []

        def list_unread(self):
            return [GmailMessage(id="g1", thread_id="t1", subject="CONTINUE", body="", from_addr="op@x")]

        def mark_read(self, mid: str) -> None:
            self.read.append(mid)

        def send(self, *, to, subject, body, in_reply_to=None):
            return "sent"

    ft = FakeTransport()
    envelope = {"message": {"data": "e30=", "messageId": "m"}, "subscription": "sub"}
    results = handle_push(envelope, ft)
    assert len(results) == 1
    assert isinstance(results[0], OperatorMessage)
    assert results[0].action == "CONTINUE"
    assert ft.read == ["g1"]
