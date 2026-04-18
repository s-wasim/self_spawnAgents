"""LLM client with pre-call budget enforcement (§13.5)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from aae.cashflow.ledger import CashflowService
from aae.core.model_router import estimate_cost_usd, route
from aae.schemas.cashflow import Pot
from aae.schemas.common import AgentTier, ModelID, TaskKind


class BudgetExceeded(Exception):
    """Raised before a call if estimated cost would breach any relevant floor."""


class SystemHalted(Exception):
    """Raised when Redis system_state == HARD_STOP."""


@dataclass
class BudgetState:
    operating_pot_usd: Decimal
    monthly_budget_usd: Decimal | None = None
    spent_mtd_usd: Decimal = Decimal("0")


@dataclass
class LLMResponse:
    model: ModelID
    content: str
    tokens_in: int
    tokens_out: int
    cost_usd: Decimal


class LLMProvider(Protocol):
    async def call(
        self, *, model: ModelID, system: str, user: str, max_tokens: int
    ) -> tuple[str, int, int]: ...


class LLMClient:
    """Budget-aware wrapper around an LLMProvider."""

    def __init__(
        self,
        provider: LLMProvider,
        cashflow: CashflowService | None,
        *,
        system_state_getter: Any = None,
    ) -> None:
        self._provider = provider
        self._cashflow = cashflow
        self._get_state = system_state_getter or (lambda: "normal")

    async def call(
        self,
        *,
        agent: AgentTier,
        task: TaskKind,
        system: str,
        user: str,
        max_tokens: int = 1024,
        expected_tokens_in: int = 1000,
        budget: BudgetState | None = None,
    ) -> LLMResponse:
        if self._get_state() == "hard_stop":
            raise SystemHalted("system_state=HARD_STOP; refusing LLM call")

        operating = (budget.operating_pot_usd
                     if budget else (self._cashflow.balance().operating
                                     if self._cashflow else Decimal("1000")))
        model = route(agent, task, operating)
        est_cost = estimate_cost_usd(model, expected_tokens_in, max_tokens)

        self._assert_budget(operating, est_cost, budget)

        content, tokens_in, tokens_out = await self._provider.call(
            model=model, system=system, user=user, max_tokens=max_tokens
        )
        actual_cost = estimate_cost_usd(model, tokens_in, tokens_out)

        if self._cashflow is not None and actual_cost > 0:
            # Post-call debit (§13.5).
            try:
                self._cashflow.debit(
                    Pot.OPERATING, actual_cost, source="cost_anthropic"
                )
            except Exception:
                # In sim mode or on low cost we may no-op; ignore debit failures
                # beyond log because the actual billing comes from reconcile.py.
                pass

        return LLMResponse(
            model=model,
            content=content,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=actual_cost,
        )

    def _assert_budget(
        self, operating: Decimal, est_cost: Decimal, budget: BudgetState | None
    ) -> None:
        from aae.cashflow.hard_floors import OPERATING_HARD_FLOOR_USD
        if operating - est_cost < OPERATING_HARD_FLOOR_USD:
            raise BudgetExceeded(
                f"Call cost ${est_cost} would breach operating floor; operating=${operating}"
            )
        if budget and budget.monthly_budget_usd is not None:
            if budget.spent_mtd_usd + est_cost > budget.monthly_budget_usd:
                raise BudgetExceeded(
                    f"Call cost ${est_cost} would breach monthly budget "
                    f"(${budget.monthly_budget_usd}); spent_mtd=${budget.spent_mtd_usd}"
                )
