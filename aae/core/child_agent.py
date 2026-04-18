"""Child Agent template (§5 / §14.x).

A Child is a narrow per-vertical operator. It cannot:
  * spawn other children (enforced by trust_boundary)
  * write to the cashflow ledger (trust_boundary)
  * call LLMs beyond the tier its ProposalCost allows

The template here is the pure-policy core. Runtime graph wiring (LangGraph or
plain asyncio) composes these calls.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from aae.core.trust_boundary import assert_child_graph_allowed
from aae.schemas.child import ChildRun

AUP_FOOTER = (
    "Outputs generated with assistance from an automated system. Review before use."
)


@dataclass
class ChildContext:
    run: ChildRun
    vertical_id: UUID
    preregistration_id: UUID


class ChildAgent:
    """Minimal per-vertical runner.

    ChildAgent owns a tiny state machine: starting → live → (paused|killed).
    Revenue/spend deltas are reported *back* to the Mother via supervisor.
    """

    GRAPH_NODES = ("observe", "plan", "act", "report")  # no "spawn_child"!

    def __init__(self, ctx: ChildContext) -> None:
        assert_child_graph_allowed(set(self.GRAPH_NODES))
        self.ctx = ctx

    def customer_footer(self) -> str:
        """§AUP flow-through — every customer-facing product must carry this line."""
        return AUP_FOOTER

    def heartbeat_payload(self, *, now: datetime | None = None) -> dict:
        """Health beacon the ChildSupervisor consumes."""
        return {
            "child_id": str(self.ctx.run.id),
            "status": self.ctx.run.status,
            "revenue_mtd_usd": str(self.ctx.run.revenue_mtd_usd),
            "spent_mtd_usd": str(self.ctx.run.spent_mtd_usd),
            "timestamp": (now or datetime.now(timezone.utc)).isoformat(),
        }

    def check_budget(self, projected_cost_usd: Decimal) -> bool:
        """Return True iff spending `projected_cost_usd` keeps us under budget."""
        return self.ctx.run.spent_mtd_usd + projected_cost_usd <= self.ctx.run.monthly_budget_usd
