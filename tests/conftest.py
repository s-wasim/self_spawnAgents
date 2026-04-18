"""Shared pytest fixtures."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure the repo root is on sys.path so `import aae` works without install.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("AAE_MODE", "simulation")
os.environ.setdefault("OPERATOR_HMAC_SECRET", "test-hmac-secret-0123456789abcdef")


@pytest.fixture
def tmp_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A writable sandbox rooted at tmp_path with a minimal aae/ tree."""
    monkeypatch.chdir(tmp_path)
    return tmp_path
