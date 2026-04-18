"""Hourly cashflow reconciliation (§7.4)."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from aae.cashflow.ledger import CashflowService
from aae.db.models import CashflowLedger

DRIFT_ALERT_THRESHOLD = Decimal("1.00")


def check_drift(session: Session, service: CashflowService) -> Decimal:
    """Compare sum(delta) against the pot balances returned by CashflowService.
    Returns the absolute drift in USD.
    """
    balances = service.balance()
    total_entries = session.execute(
        select(func.coalesce(func.sum(CashflowLedger.delta), 0))
    ).scalar_one()
    total_balances = balances.operating + balances.reserve + balances.growth
    return abs(Decimal(total_entries) - total_balances)
