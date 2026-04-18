"""Validator: parses pytest stdout, extracts passing test IDs & coverage (§9.1)."""
from __future__ import annotations

import re
from dataclasses import dataclass


PASSED_RE = re.compile(r"^(?P<node>[\w/\\.:\-]+::\S+)\s+PASSED", re.MULTILINE)
# pytest -q summary lines
SUMMARY_OK_RE = re.compile(r"^(\d+) passed", re.MULTILINE)
SUMMARY_FAIL_RE = re.compile(r"(\d+) failed", re.MULTILINE)
COVERAGE_RE = re.compile(r"TOTAL.*?(\d+(?:\.\d+)?)%", re.MULTILINE)


@dataclass
class ValidationResult:
    ok: bool
    passed_tests: list[str]
    failed_tests: int
    coverage_pct: float
    raw: str


def validate(stdout: str, *, min_coverage: float = 0.0) -> ValidationResult:
    passed_ids = [m.group("node") for m in PASSED_RE.finditer(stdout)]
    passed_ct = int(SUMMARY_OK_RE.search(stdout).group(1)) if SUMMARY_OK_RE.search(stdout) else len(passed_ids)
    fail_ct = int(SUMMARY_FAIL_RE.search(stdout).group(1)) if SUMMARY_FAIL_RE.search(stdout) else 0
    cov_m = COVERAGE_RE.search(stdout)
    cov = float(cov_m.group(1)) if cov_m else 0.0
    ok = fail_ct == 0 and passed_ct > 0 and cov >= min_coverage
    # If pytest -q omits individual PASSED lines, synthesize generic ids
    if not passed_ids and passed_ct:
        passed_ids = [f"test_{i+1}" for i in range(passed_ct)]
    return ValidationResult(
        ok=ok,
        passed_tests=passed_ids,
        failed_tests=fail_ct,
        coverage_pct=cov,
        raw=stdout,
    )
