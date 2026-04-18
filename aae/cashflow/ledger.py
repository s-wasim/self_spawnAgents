"""Cashflow service — the single writer of the three-pot ledger (§7).

Only the Mother Agent may construct this with tier=AgentTier.MOTHER. The trust
boundary (§5.1 rule 1) is enforced at __init__ by require_mother_for_ledger.
"""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from aae.cashflow.hard_floors import (
    GROWTH_SPLIT,
    OPERATING_HARD_FLOOR_USD,
    OPERATING_SPLIT,
    RESERVE_INVIOLATE,
    RESERVE_SPLIT,
)
from aae.cashflow.pots import (
    PotSnapshot,
    growth_cap_from_trailing_revenue,
)
from aae.core.trust_boundary import TrustViolation, require_mother_for_ledger
from aae.db.models import CashflowLedger
from aae.schemas.cashflow import CashflowEntry, CashflowSource, Pot, PotBalances
from aae.schemas.common import AgentTier, utc_now


class InsufficientFunds(Exception):
    """Raised when a debit would breach a hard floor."""


class ReserveLocked(Exception):
    """Raised when anything but a signed emergency_transfer tries to debit Reserve."""


class BadHMAC(Exception):
    """Raised when an EMERGENCY_TRANSFER's HMAC does not verify."""


@dataclass(frozen=True)
class InflowSplit:
    operating: Decimal
    reserve: Decimal
    growth: Decimal


def split_inflow(
    amount_usd: Decimal,
    *,
    current_reserve: Decimal = Decimal("0"),
    reserve_cap: Decimal | None = None,
    current_growth: Decimal = Decimal("0"),
    growth_cap: Decimal | None = None,
) -> InflowSplit:
    """Apply the 60/25/15 split. Overflow rules (§7.2): if reserve or growth is capped,
    overflow rolls to Operating.
    """
    op_amt = (amount_usd * OPERATING_SPLIT).quantize(Decimal("0.0001"))
    res_amt = (amount_usd * RESERVE_SPLIT).quantize(Decimal("0.0001"))
    gr_amt = (amount_usd * GROWTH_SPLIT).quantize(Decimal("0.0001"))
    # Fix quantization residue: push remainder to Operating.
    residue = amount_usd - (op_amt + res_amt + gr_amt)
    op_amt += residue

    if reserve_cap is not None and (current_reserve + res_amt) > reserve_cap:
        overflow = (current_reserve + res_amt) - reserve_cap
        res_amt -= overflow
        op_amt += overflow
    if growth_cap is not None and (current_growth + gr_amt) > growth_cap:
        overflow = (current_growth + gr_amt) - growth_cap
        gr_amt -= overflow
        op_amt += overflow
    return InflowSplit(
        operating=op_amt.quantize(Decimal("0.0001")),
        reserve=res_amt.quantize(Decimal("0.0001")),
        growth=gr_amt.quantize(Decimal("0.0001")),
    )


def verify_emergency_hmac(secret: str, amount_usd: Decimal, date_iso: str, signature: str) -> bool:
    msg = f"{amount_usd}|{date_iso}".encode()
    want = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(want, signature)


class CashflowService:
    """All cashflow writes go through here. Reads are also centralized."""

    def __init__(self, session: Session, *, tier: AgentTier):
        require_mother_for_ledger(tier)
        self._session = session
        self._tier = tier

    # ---------- reads

    def balance(self) -> PotBalances:
        sums: dict[str, Decimal] = {p.value: Decimal("0") for p in Pot}
        rows = self._session.execute(select(CashflowLedger)).scalars().all()
        for r in rows:
            sums[r.pot] = sums[r.pot] + r.delta
        return PotBalances(
            operating=sums["operating"],
            reserve=sums["reserve"],
            growth=sums["growth"],
        )

    def snapshot(self) -> PotSnapshot:
        b = self.balance()
        return PotSnapshot(operating=b.operating, reserve=b.reserve, growth=b.growth)

    # ---------- writes

    def record(
        self,
        pot: Pot,
        delta: Decimal,
        source: CashflowSource,
        *,
        ref_id: str | None = None,
        note: str = "",
        ts: datetime | None = None,
    ) -> CashflowEntry:
        if delta == 0:
            raise ValueError("cashflow delta must be non-zero")
        if delta < 0:
            self._assert_debit_allowed(pot, delta, source)
        entry = CashflowEntry(
            ts=ts or utc_now(),
            pot=pot,
            delta=delta,
            source=source,
            ref_id=ref_id,
            note=note,
        )
        self._session.add(
            CashflowLedger(
                id=str(entry.id),
                ts=entry.ts,
                pot=entry.pot.value,
                delta=entry.delta,
                source=entry.source,
                ref_id=entry.ref_id,
                note=entry.note,
                written_by=self._tier.value,
            )
        )
        self._session.flush()
        return entry

    def debit(self, pot: Pot, amount_usd: Decimal, source: CashflowSource, **kw) -> CashflowEntry:
        if amount_usd <= 0:
            raise ValueError("debit must be a positive amount")
        return self.record(pot, -amount_usd, source, **kw)

    def credit(self, pot: Pot, amount_usd: Decimal, source: CashflowSource, **kw) -> CashflowEntry:
        if amount_usd <= 0:
            raise ValueError("credit must be a positive amount")
        return self.record(pot, amount_usd, source, **kw)

    # ---------- inflow split

    def split_and_record_inflow(
        self,
        amount_usd: Decimal,
        source: CashflowSource,
        *,
        ref_id: str | None = None,
        reserve_cap: Decimal | None = None,
        trailing_90d_revenue: Decimal = Decimal("0"),
    ) -> tuple[CashflowEntry, CashflowEntry, CashflowEntry]:
        snap = self.snapshot()
        growth_cap = growth_cap_from_trailing_revenue(trailing_90d_revenue)
        s = split_inflow(
            amount_usd,
            current_reserve=snap.reserve,
            reserve_cap=reserve_cap,
            current_growth=snap.growth,
            growth_cap=growth_cap,
        )
        op_entry = self.credit(Pot.OPERATING, s.operating, source, ref_id=ref_id)
        res_entry = self.credit(Pot.RESERVE, s.reserve, source, ref_id=ref_id) if s.reserve > 0 else op_entry
        gr_entry = self.credit(Pot.GROWTH, s.growth, source, ref_id=ref_id) if s.growth > 0 else op_entry
        return op_entry, res_entry, gr_entry

    # ---------- emergency transfer

    def emergency_transfer_reserve_to_operating(
        self, *, amount_usd: Decimal, date_iso: str, signature: str, operator_secret: str
    ) -> tuple[CashflowEntry, CashflowEntry]:
        if not RESERVE_INVIOLATE:
            raise TrustViolation("RESERVE_INVIOLATE flipped off — this is never allowed")
        if not verify_emergency_hmac(operator_secret, amount_usd, date_iso, signature):
            raise BadHMAC("EMERGENCY_TRANSFER signature invalid")
        if amount_usd <= 0:
            raise ValueError("amount must be positive")
        out = self.record(
            Pot.RESERVE, -amount_usd,
            source="emergency_transfer_reserve_to_operating",
            note=f"signed EMERGENCY_TRANSFER {date_iso}",
        )
        inn = self.record(
            Pot.OPERATING, amount_usd,
            source="emergency_transfer_reserve_to_operating",
            note=f"signed EMERGENCY_TRANSFER {date_iso}",
        )
        return out, inn

    # ---------- internal checks

    def _assert_debit_allowed(self, pot: Pot, delta: Decimal, source: CashflowSource) -> None:
        snap = self.snapshot()
        new_balance = snap.get(pot) + delta
        if pot == Pot.OPERATING:
            if new_balance < OPERATING_HARD_FLOOR_USD:
                raise InsufficientFunds(
                    f"Operating debit would breach hard floor "
                    f"(${OPERATING_HARD_FLOOR_USD}); balance after={new_balance}"
                )
        elif pot == Pot.RESERVE:
            if source != "emergency_transfer_reserve_to_operating":
                raise ReserveLocked(
                    "Reserve pot is inviolate; only emergency_transfer may debit."
                )
        elif pot == Pot.GROWTH:
            if new_balance < 0:
                raise InsufficientFunds("Growth pot cannot go negative")


# Drift-detection helper used by reconcile.py and tests.
def ledger_drift(balances: PotBalances, sum_of_entries: Decimal) -> Decimal:
    total = balances.operating + balances.reserve + balances.growth
    return abs(total - sum_of_entries)


def new_id() -> str:
    return str(uuid4())
