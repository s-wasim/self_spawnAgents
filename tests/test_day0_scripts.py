"""Phase 17: day0_bootstrap + emergency_transfer smoke tests."""
from __future__ import annotations

import os
from typer.testing import CliRunner

from scripts.day0_bootstrap import app as bootstrap_app
from scripts.emergency_transfer import app as et_app


runner = CliRunner()


def test_send_test_digest_renders_preview() -> None:
    result = runner.invoke(bootstrap_app, ["send-test-digest"])
    assert result.exit_code == 0
    assert "Operating:" in result.stdout
    assert "CONTINUE" in result.stdout


def test_verify_frozen_succeeds() -> None:
    result = runner.invoke(bootstrap_app, ["verify-frozen"])
    # clean repo → exit 0
    assert result.exit_code == 0


def test_ping_channels_dry_run() -> None:
    result = runner.invoke(bootstrap_app, ["ping-channels"])
    assert result.exit_code == 0
    for n in ("polar", "stripe_connect", "vercel", "netlify"):
        assert n in result.stdout


def test_emergency_sign_and_verify_roundtrip(monkeypatch) -> None:
    monkeypatch.setenv("OPERATOR_HMAC_SECRET", "test-secret")
    r1 = runner.invoke(et_app, ["sign", "100.00", "--date-iso", "2026-04-18"])
    assert r1.exit_code == 0
    sig = r1.stdout.strip()
    assert len(sig) == 64

    r2 = runner.invoke(et_app, ["verify", "100.00", "2026-04-18", sig])
    assert r2.exit_code == 0
    assert "OK" in r2.stdout

    r3 = runner.invoke(et_app, ["verify", "999.99", "2026-04-18", sig])
    assert r3.exit_code == 1


def test_emergency_sign_requires_env(monkeypatch) -> None:
    monkeypatch.delenv("OPERATOR_HMAC_SECRET", raising=False)
    r = runner.invoke(et_app, ["sign", "50"])
    assert r.exit_code != 0
