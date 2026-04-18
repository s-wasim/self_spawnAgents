"""Operator message parser (§15.1 / §15.2).

Case-insensitive subject parser. The ONLY legal verbs: APPROVE, REJECT,
CONTINUE, PAUSE, KILL, RESUME, EMERGENCY_TRANSFER. Anything else → FormLetter.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal
from uuid import UUID

Action = Literal[
    "APPROVE", "REJECT", "CONTINUE", "PAUSE",
    "KILL_CHILD", "KILL_ALL", "RESUME", "EMERGENCY_TRANSFER",
]

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
AMOUNT_RE = re.compile(r"^\d+(?:\.\d{1,2})?$")


@dataclass(frozen=True)
class OperatorMessage:
    action: Action
    subject_id: UUID | None = None
    amount_usd: Decimal | None = None
    body_excerpt: str = ""
    raw_sha256: str = ""


@dataclass(frozen=True)
class FormLetter:
    reason: str
    allowed_verbs: tuple[str, ...] = (
        "APPROVE <proposal_id>",
        "REJECT <proposal_id>",
        "CONTINUE",
        "PAUSE",
        "KILL <child_id>",
        "KILL ALL",
        "RESUME <event_id>",
        "EMERGENCY_TRANSFER <amount_usd> reserve->operating",
    )
    raw_sha256: str = ""


ParseResult = OperatorMessage | FormLetter


def _sha(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _reject(raw_sha: str, reason: str) -> FormLetter:
    return FormLetter(reason=reason, raw_sha256=raw_sha)


def parse(subject: str, body: str = "") -> ParseResult:
    raw = f"{subject}\n{body}".strip()
    raw_sha = _sha(raw)
    s = (subject or "").strip()
    if not s:
        return _reject(raw_sha, "empty_subject")

    parts = s.split()
    verb = parts[0].upper()

    if verb == "APPROVE":
        if len(parts) != 2 or not UUID_RE.match(parts[1]):
            return _reject(raw_sha, "APPROVE requires exactly one proposal UUID")
        return OperatorMessage("APPROVE", subject_id=UUID(parts[1]), raw_sha256=raw_sha)

    if verb == "REJECT":
        if len(parts) != 2 or not UUID_RE.match(parts[1]):
            return _reject(raw_sha, "REJECT requires exactly one proposal UUID")
        # optional body, logged but not parsed
        body_excerpt = (body or "")[:500]
        return OperatorMessage(
            "REJECT",
            subject_id=UUID(parts[1]),
            body_excerpt=body_excerpt,
            raw_sha256=raw_sha,
        )

    if verb == "CONTINUE":
        if len(parts) != 1:
            return _reject(raw_sha, "CONTINUE takes no arguments")
        return OperatorMessage("CONTINUE", raw_sha256=raw_sha)

    if verb == "PAUSE":
        if len(parts) != 1:
            return _reject(raw_sha, "PAUSE takes no arguments")
        return OperatorMessage("PAUSE", raw_sha256=raw_sha)

    if verb == "KILL":
        if len(parts) == 2:
            if parts[1].upper() == "ALL":
                return OperatorMessage("KILL_ALL", raw_sha256=raw_sha)
            if UUID_RE.match(parts[1]):
                return OperatorMessage("KILL_CHILD", subject_id=UUID(parts[1]), raw_sha256=raw_sha)
        return _reject(raw_sha, "KILL must be 'KILL ALL' or 'KILL <child_uuid>'")

    if verb == "RESUME":
        if len(parts) != 2 or not UUID_RE.match(parts[1]):
            return _reject(raw_sha, "RESUME requires exactly one event UUID")
        return OperatorMessage("RESUME", subject_id=UUID(parts[1]), raw_sha256=raw_sha)

    if verb == "EMERGENCY_TRANSFER":
        # EMERGENCY_TRANSFER <amount_usd> reserve->operating
        if len(parts) != 3:
            return _reject(raw_sha, "EMERGENCY_TRANSFER <amount> reserve->operating")
        if parts[2].lower() != "reserve->operating":
            return _reject(raw_sha, "EMERGENCY_TRANSFER direction must be reserve->operating")
        if not AMOUNT_RE.match(parts[1]):
            return _reject(raw_sha, "EMERGENCY_TRANSFER amount must be USD decimal")
        try:
            amt = Decimal(parts[1])
        except InvalidOperation:
            return _reject(raw_sha, "EMERGENCY_TRANSFER amount parse failed")
        return OperatorMessage(
            "EMERGENCY_TRANSFER",
            amount_usd=amt,
            body_excerpt=(body or "")[:500],
            raw_sha256=raw_sha,
        )

    return _reject(raw_sha, f"unknown_verb:{verb}")
