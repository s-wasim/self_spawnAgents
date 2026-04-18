"""Row 24: lint_channels flags ad-hoc httpx outside aae/channels/.
Row 25: Polar channel builds Authorization: Bearer <token> header.
"""
from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.lint_channels import scan_file, scan_tree  # noqa: E402

from aae.channels.polar import PolarClient  # noqa: E402
from aae.channels.vercel import VercelClient  # noqa: E402


# --- Row 24: lint ---

def test_lint_clean_repo_returns_zero_violations() -> None:
    assert scan_tree(REPO) == []


def test_lint_flags_bad_file(tmp_path: Path) -> None:
    fake = tmp_path / "aae" / "bad.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("import httpx\n\ndef f(): ...\n")
    violations = scan_tree(tmp_path)
    assert len(violations) == 1
    assert "httpx" in violations[0][2]


def test_lint_ignores_channels_dir(tmp_path: Path) -> None:
    fake = tmp_path / "aae" / "channels" / "ok.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("import httpx\n")
    assert scan_tree(tmp_path) == []


def test_lint_flags_from_import(tmp_path: Path) -> None:
    fake = tmp_path / "aae" / "bad_from.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("from httpx import AsyncClient\n")
    violations = scan_file(fake)
    assert len(violations) == 1


def test_lint_flags_requests(tmp_path: Path) -> None:
    fake = tmp_path / "aae" / "bad_requests.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("import requests\n")
    violations = scan_file(fake)
    assert len(violations) == 1


# --- Row 25: Polar auth header via MockTransport ---

@pytest.mark.asyncio
async def test_polar_sets_bearer_header() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization")
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"id": "org_123"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        polar = PolarClient(client, org_token="polar_secret_xyz")
        await polar._get_json("/organizations/me")

    assert captured["auth"] == "Bearer polar_secret_xyz"
    assert captured["url"].endswith("/organizations/me")


@pytest.mark.asyncio
async def test_polar_webhook_verify() -> None:
    import hashlib
    import hmac

    async with httpx.AsyncClient() as client:
        polar = PolarClient(client, org_token="tok")

    body = b'{"event":"payment.succeeded"}'
    secret = "whsec_test"
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert await polar.webhook_verify(signature=sig, body=body, secret=secret) is True
    assert await polar.webhook_verify(signature="bad", body=body, secret=secret) is False


def test_vercel_rejects_hobby_plan() -> None:
    import pytest

    async def _runner() -> None:
        async with httpx.AsyncClient() as client:
            with pytest.raises(ValueError, match="pro"):
                VercelClient(client, pat="x", plan="hobby")

    import asyncio
    asyncio.run(_runner())
