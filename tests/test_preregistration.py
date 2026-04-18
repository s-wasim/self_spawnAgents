"""Pre-registration tests (§20 rows 7-9, also canonical JSON determinism)."""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aae.db.models import Base
from aae.preregistration.canonical import canonical_dumps, canonical_hash
from aae.preregistration.register import (
    PreRegistrationLocked,
    compute_lock_hash,
    create,
    ensure_locked_and_exists,
    reject_mutation,
)
from aae.preregistration.schema import PreRegistration
from aae.schemas.vertical import KillCriteria, RevenueChannel, VerticalProposal


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _create(session: Session) -> PreRegistration:
    return create(
        session,
        vertical_title="Widget for X",
        hypothesis="We can sell a widget at $9.99 to indie developers — " * 2,
        primary_metric="monthly_recurring_revenue_usd",
        primary_threshold=Decimal("500"),
        measurement_window_days=30,
        analysis_plan="Count paid subscriptions on day 30 via Polar API; net-of-refunds. " * 3,
        stopping_rule="Stop and kill if day-30 revenue < threshold. Stop if cumulative burn > budget.",
    )


def test_proposal_rejects_unlocked_prereg(session: Session):
    """Row 7 — can't advance a proposal whose prereg_id doesn't exist or isn't locked."""
    with pytest.raises(Exception):
        ensure_locked_and_exists(session, str(uuid4()))


def test_canonical_json_determinism():
    """Row 8."""
    a = {"b": 2, "a": 1, "nested": {"y": "z", "x": "w"}}
    b = {"nested": {"x": "w", "y": "z"}, "a": 1, "b": 2}
    assert canonical_dumps(a) == canonical_dumps(b)
    assert canonical_hash(a) == canonical_hash(b)


def test_canonical_rejects_float():
    with pytest.raises(TypeError):
        canonical_dumps({"x": 1.5})


def test_locked_row_update_rejected(session: Session):
    """Row 9 — application-level guard fires regardless of DB dialect."""
    _create(session)
    with pytest.raises(PreRegistrationLocked):
        reject_mutation(session)


def test_create_and_fetch(session: Session):
    p = _create(session)
    assert p.locked is True
    assert len(p.lock_hash) == 64
    p2 = ensure_locked_and_exists(session, str(p.id))
    assert p2.id == p.id


def test_compute_lock_hash_stable(session: Session):
    p = _create(session)
    # Recomputing should produce the same hash for the same content.
    from aae.preregistration.register import verify_hash
    assert verify_hash(p)


def test_vertical_proposal_requires_prereg_id(session: Session):
    p = _create(session)
    prop = VerticalProposal(
        title="Paid widget for indie devs X",
        one_line="A subscription widget to help indie devs ship faster.",
        problem="X" * 120,
        solution="Y" * 120,
        target_user="Indie developers " * 2,
        revenue_channel=RevenueChannel.POLAR,
        pricing_model="subscription_monthly",
        unit_price_usd=Decimal("9.99"),
        projected_monthly_revenue_usd=Decimal("500"),
        projected_monthly_cost_usd=Decimal("40"),
        launch_budget_usd=Decimal("50"),
        kill_criteria=KillCriteria(
            max_days_to_first_dollar=30,
            min_revenue_by_day_30_usd=Decimal("100"),
            max_burn_before_first_dollar_usd=Decimal("50"),
        ),
        preregistration_id=p.id,
    )
    assert prop.preregistration_id == p.id
