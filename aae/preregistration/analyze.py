"""Day-30 analysis comparing observed data to the locked preregistration (§10.2 step 5)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from aae.preregistration.register import verify_hash
from aae.preregistration.schema import PreRegistration


@dataclass(frozen=True)
class AnalysisResult:
    preregistration_id: str
    met_threshold: bool
    observed_metric_value: Decimal
    threshold: Decimal
    hash_valid: bool
    notes: str


def analyze(prereg: PreRegistration, observed_value: Decimal) -> AnalysisResult:
    hash_ok = verify_hash(prereg)
    met = observed_value >= prereg.primary_threshold
    return AnalysisResult(
        preregistration_id=str(prereg.id),
        met_threshold=met,
        observed_metric_value=observed_value,
        threshold=prereg.primary_threshold,
        hash_valid=hash_ok,
        notes=(
            "HASH DRIFT — prereg tampered with!"
            if not hash_ok
            else ("threshold met" if met else "threshold missed")
        ),
    )
