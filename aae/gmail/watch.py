"""Gmail watch channel setup (§13.4).

Registers a Pub/Sub push watch on the operator mailbox. Renewal every 6 days
(Gmail expires watches at 7 days). This module is stub-friendly: production
wires it against the Gmail API, tests exercise only the renewal clock.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

WATCH_TTL = timedelta(days=6, hours=12)


def next_renewal_at(watched_at: datetime) -> datetime:
    return watched_at + WATCH_TTL


def needs_renewal(watched_at: datetime, *, now: datetime | None = None) -> bool:
    return (now or datetime.now(timezone.utc)) >= next_renewal_at(watched_at)
