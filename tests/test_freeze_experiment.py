"""Tests for frozen-path integrity (§11, rows 10-11 of §20)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from aae.config.frozen import FROZEN_PATHS, HASHES_LOCK_FILE
from aae.ops import freeze_experiment


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_hashes_lock_exists_and_covers_all_frozen_paths():
    lock = freeze_experiment.read_lock()
    assert set(lock.keys()) == set(FROZEN_PATHS)


def test_verify_passes_on_clean_repo():
    assert freeze_experiment.verify_exit_code() == 0


def test_verify_detects_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Row 10: tampering a frozen file must be detected."""
    # Copy the frozen file to tmp and mutate.
    root = _repo_root()
    frozen_file = root / "aae/ethics/prompt.md"
    original = frozen_file.read_bytes()
    try:
        frozen_file.write_bytes(original + b"\ntampered\n")
        assert freeze_experiment.verify_exit_code() == 1
    finally:
        frozen_file.write_bytes(original)
    assert freeze_experiment.verify_exit_code() == 0


def test_cli_exit_code(tmp_path: Path):
    """Row 11: `freeze verify` CLI returns non-zero on drift."""
    root = _repo_root()
    frozen_file = root / "aae/cashflow/hard_floors.py"
    original = frozen_file.read_bytes()
    try:
        frozen_file.write_bytes(original + b"\n# drift\n")
        result = subprocess.run(
            [sys.executable, "-m", "aae.ops.freeze_experiment", "verify"],
            cwd=root,
            capture_output=True,
        )
        assert result.returncode == 1
    finally:
        frozen_file.write_bytes(original)

    result = subprocess.run(
        [sys.executable, "-m", "aae.ops.freeze_experiment", "verify"],
        cwd=root,
        capture_output=True,
    )
    assert result.returncode == 0


def test_frozen_paths_all_present():
    root = _repo_root()
    for rel in FROZEN_PATHS:
        assert (root / rel).exists(), f"Missing frozen file: {rel}"


def test_lock_file_location():
    assert HASHES_LOCK_FILE == "aae/config/frozen/hashes.lock"


def test_compute_hashes_deterministic():
    a = freeze_experiment.compute_hashes()
    b = freeze_experiment.compute_hashes()
    assert a == b
