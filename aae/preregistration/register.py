"""Pre-registration creation flow (§10.2)."""
from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from aae.db.models import PreRegistrationRow
from aae.preregistration.canonical import canonical_dumps, canonical_hash
from aae.preregistration.schema import PreRegistration
from aae.schemas.common import utc_now


class PreRegistrationLocked(Exception):
    """Raised when something tries to update a locked preregistration row."""


def canonical_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Strip the lock_hash before hashing so the hash covers the content itself."""
    return {k: v for k, v in data.items() if k != "lock_hash"}


def compute_lock_hash(data: dict[str, Any]) -> str:
    return canonical_hash(canonical_payload(data))


def create(
    session: Session,
    *,
    vertical_title: str,
    hypothesis: str,
    primary_metric: str,
    primary_threshold: Decimal,
    measurement_window_days: int,
    analysis_plan: str,
    stopping_rule: str,
) -> PreRegistration:
    """Canonicalize, hash, insert a locked row.

    We build a Pydantic model first, serialize via model_dump_json (the single
    canonical source of truth for serialization), hash that dict, then re-validate
    with the lock_hash attached. This guarantees verify_hash() sees the same bytes.
    """
    # Build a provisional model without the lock_hash (use a placeholder that's stripped).
    provisional = PreRegistration(
        id=uuid4(),
        created_at=utc_now(),
        vertical_title=vertical_title,
        hypothesis=hypothesis,
        primary_metric=primary_metric,
        primary_threshold=primary_threshold,
        measurement_window_days=measurement_window_days,
        analysis_plan=analysis_plan,
        stopping_rule=stopping_rule,
        locked=True,
        lock_hash="0" * 64,  # placeholder, stripped before hashing
    )
    payload = json.loads(provisional.model_dump_json())
    lock_hash = compute_lock_hash(payload)
    payload["lock_hash"] = lock_hash
    prereg = PreRegistration.model_validate(payload)

    row = PreRegistrationRow(
        id=str(prereg.id),
        created_at=prereg.created_at,
        vertical_title=prereg.vertical_title,
        primary_metric=prereg.primary_metric,
        primary_threshold=prereg.primary_threshold,
        measurement_window_days=prereg.measurement_window_days,
        locked=True,
        lock_hash=prereg.lock_hash,
        payload_json=json.loads(prereg.model_dump_json()),
    )
    session.add(row)
    session.flush()
    return prereg


def get(session: Session, prereg_id: str) -> PreRegistration:
    row = session.execute(
        select(PreRegistrationRow).where(PreRegistrationRow.id == prereg_id)
    ).scalar_one()
    return PreRegistration.model_validate(row.payload_json)


def ensure_locked_and_exists(session: Session, prereg_id: str) -> PreRegistration:
    """Used by the vertical-proposal validator to enforce §10.2 step 4."""
    prereg = get(session, prereg_id)
    if not prereg.locked:
        raise PreRegistrationLocked(f"prereg {prereg_id} is not locked")
    return prereg


def reject_mutation(_session: Session, *args, **kw) -> None:
    """Application-level guard. On Postgres the DB trigger enforces this; on SQLite
    we emulate by calling this helper before any update."""
    raise PreRegistrationLocked("preregistration rows are immutable once locked")


def verify_hash(prereg: PreRegistration) -> bool:
    """Recompute the lock_hash and compare to stored value (§10.2 step 5)."""
    data = json.loads(prereg.model_dump_json())
    return compute_lock_hash(data) == prereg.lock_hash
