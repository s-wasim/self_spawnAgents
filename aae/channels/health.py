"""Channel health monitoring (§6.5).

Runs every 6 hours (APScheduler cron) and pings every registered channel.
Results are written to the `channel_health` table for the Mother Agent to consult.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from sqlalchemy import insert
from sqlalchemy.orm import Session

from aae.channels.base import BaseChannelClient, ChannelStatus
from aae.db.models import ChannelHealth


async def check_all(clients: Iterable[BaseChannelClient]) -> list[ChannelStatus]:
    results: list[ChannelStatus] = []
    for c in clients:
        results.append(await c.health())
    return results


def persist(session: Session, statuses: Iterable[ChannelStatus]) -> None:
    now = datetime.now(timezone.utc)
    for s in statuses:
        session.execute(
            insert(ChannelHealth).values(
                channel=s.name,
                ok=s.ok,
                latency_ms=s.latency_ms,
                detail=s.detail,
                checked_at=now,
            )
        )
    session.commit()


async def run_health_cycle(
    clients: Iterable[BaseChannelClient], session: Session
) -> list[ChannelStatus]:
    statuses = await check_all(clients)
    persist(session, statuses)
    return statuses
