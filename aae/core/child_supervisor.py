"""ChildSupervisor (§8.3) — enforces auto-kill / pause policies.

Pure logic + in-memory registry. At runtime the same class persists via
SQLAlchemy (ChildRunRow) but tests exercise the kill decisions directly.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID

from aae.schemas.child import ChildRun
from aae.schemas.vertical import KillCriteria


class SupervisorError(Exception):
    pass


@dataclass
class _ChildEntry:
    run: ChildRun
    kill: KillCriteria
    cumulative_spend_usd: Decimal = Decimal("0")


KillReason = Literal[
    "no_revenue_by_deadline",
    "below_day30_target",
    "burn_without_revenue",
    "operator",
    "kill_switch",
]
PauseReason = Literal["monthly_budget_breach", "operator"]


@dataclass
class SupervisorDecision:
    action: Literal["keep", "kill", "pause"]
    reason: str = ""


@dataclass
class ChildSupervisor:
    children: dict[UUID, _ChildEntry] = field(default_factory=dict)

    # ---- lifecycle ----
    def register(self, *, run: ChildRun, kill: KillCriteria) -> None:
        if run.id in self.children:
            raise SupervisorError("duplicate child id")
        self.children[run.id] = _ChildEntry(run=run, kill=kill)

    def heartbeat(self, child_id: UUID, *, now: datetime | None = None) -> None:
        entry = self._get(child_id)
        entry.run = entry.run.model_copy(
            update={"last_heartbeat": now or datetime.now(timezone.utc)}
        )

    def record_spend(self, child_id: UUID, amount_usd: Decimal) -> None:
        entry = self._get(child_id)
        entry.cumulative_spend_usd += amount_usd
        entry.run = entry.run.model_copy(
            update={"spent_mtd_usd": entry.run.spent_mtd_usd + amount_usd}
        )

    def record_revenue(self, child_id: UUID, amount_usd: Decimal) -> None:
        entry = self._get(child_id)
        entry.run = entry.run.model_copy(
            update={"revenue_mtd_usd": entry.run.revenue_mtd_usd + amount_usd}
        )

    # ---- decisions ----
    def evaluate(self, child_id: UUID, *, now: datetime | None = None) -> SupervisorDecision:
        entry = self._get(child_id)
        run = entry.run
        kc = entry.kill
        now = now or datetime.now(timezone.utc)
        day = max(0, (now - run.spawned_at).days)

        # §8.3 rule 4: monthly budget breach → pause
        if run.spent_mtd_usd >= run.monthly_budget_usd:
            return SupervisorDecision("pause", "monthly_budget_breach")

        # §8.3 rule 3: big burn with no revenue → kill
        if (
            entry.cumulative_spend_usd >= kc.max_burn_before_first_dollar_usd
            and run.revenue_mtd_usd == Decimal("0")
        ):
            return SupervisorDecision("kill", "burn_without_revenue")

        # §8.3 rule 1: deadline for first dollar
        if day >= kc.max_days_to_first_dollar and run.revenue_mtd_usd == Decimal("0"):
            return SupervisorDecision("kill", "no_revenue_by_deadline")

        # §8.3 rule 2: day-30 target
        if day >= 30 and run.revenue_mtd_usd < kc.min_revenue_by_day_30_usd:
            return SupervisorDecision("kill", "below_day30_target")

        return SupervisorDecision("keep", "ok")

    # ---- kill switch (§18 row 35) ----
    def pause(self, child_id: UUID, reason: PauseReason = "operator") -> None:
        entry = self._get(child_id)
        entry.run = entry.run.model_copy(update={"status": "paused", "last_error": reason})

    def kill(self, child_id: UUID, reason: KillReason = "operator") -> None:
        entry = self._get(child_id)
        entry.run = entry.run.model_copy(update={"status": "killed", "last_error": reason})

    def pause_all(self) -> int:
        n = 0
        for cid in list(self.children):
            if self.children[cid].run.status == "live":
                self.pause(cid)
                n += 1
        return n

    async def kill_all(self, *, deadline_seconds: float = 30.0) -> tuple[int, float]:
        """Row 35: kill every live child within deadline_seconds."""
        t0 = time.monotonic()
        killed = 0
        async with asyncio.TaskGroup() as tg:
            async def _kill(cid: UUID) -> None:
                nonlocal killed
                await asyncio.sleep(0)  # cooperative tick
                self.kill(cid, reason="kill_switch")
                killed += 1
            for cid, entry in list(self.children.items()):
                if entry.run.status in ("live", "paused", "starting"):
                    tg.create_task(_kill(cid))
        elapsed = time.monotonic() - t0
        if elapsed > deadline_seconds:
            raise SupervisorError(f"kill_all exceeded {deadline_seconds}s: {elapsed:.2f}s")
        return killed, elapsed

    # ---- helpers ----
    def get(self, child_id: UUID) -> ChildRun:
        return self._get(child_id).run

    def live_ids(self) -> list[UUID]:
        return [cid for cid, e in self.children.items() if e.run.status == "live"]

    def _get(self, child_id: UUID) -> _ChildEntry:
        if child_id not in self.children:
            raise SupervisorError(f"unknown child {child_id}")
        return self.children[child_id]
