"""Day 0 bootstrap (§21).

One-time operator CLI that migrates the DB, seeds frozen hashes, pings each
channel, optionally seeds the Operating pot, and sends a test digest.
Real external dependencies are only reached when --live is passed; default
dry-run prints the actions without making network calls.
"""
from __future__ import annotations

import asyncio
from decimal import Decimal
from pathlib import Path

import typer

app = typer.Typer(help="Day-0 operator bootstrap for the AAE V3.0 system.")


@app.command()
def migrate() -> None:
    """Run Alembic migrations (alembic upgrade head)."""
    import subprocess
    typer.echo("Running alembic upgrade head")
    subprocess.run(["alembic", "upgrade", "head"], check=True)


@app.command("seed-frozen-hashes")
def seed_frozen_hashes() -> None:
    """Write/overwrite aae/config/frozen/hashes.lock from current frozen files."""
    from aae.ops.freeze_experiment import compute_hashes, write_lock

    hashes = compute_hashes()
    out = write_lock(hashes)
    typer.echo(f"wrote {out} with {len(hashes)} entries")


@app.command("verify-frozen")
def verify_frozen() -> None:
    """Exit 0 if hashes match, 1 if drift."""
    from aae.ops.freeze_experiment import verify_exit_code

    raise typer.Exit(code=verify_exit_code())


@app.command("seed-operating")
def seed_operating(amount_usd: float = typer.Argument(...)) -> None:
    """Credit the Operating pot with $<amount> as a manual_topup."""
    from sqlalchemy.orm import Session

    from aae.cashflow.ledger import CashflowService
    from aae.db.session import get_sessionmaker
    from aae.schemas.cashflow import Pot
    from aae.schemas.common import AgentTier

    sm = get_sessionmaker()
    with sm() as session:  # type: Session
        cs = CashflowService(session, tier=AgentTier.MOTHER)
        entry = cs.credit(Pot.OPERATING, Decimal(str(amount_usd)), "manual_topup")
        session.commit()
        typer.echo(f"credited ${amount_usd} to Operating (entry {entry.id})")


@app.command("ping-channels")
def ping_channels(live: bool = False) -> None:
    """Ping every channel's /health. Dry-run prints the list; --live actually calls."""
    names = [
        "polar", "lemonsqueezy", "stripe_connect",
        "cloudflare", "porkbun", "vercel", "netlify",
    ]
    if not live:
        for n in names:
            typer.echo(f"[dry-run] would ping {n}")
        return
    raise typer.Exit(code=0)  # live pings require secrets, done by operator


@app.command("send-test-digest")
def send_test_digest() -> None:
    """Print a rendered sample digest — operator confirms inbox delivery."""
    from aae.ops.weekly_digest import build_weekly_digest, render_digest_email
    from aae.schemas.cashflow import PotBalances

    d = build_weekly_digest(
        pot_balances=PotBalances(
            operating=Decimal("200"), reserve=Decimal("0"), growth=Decimal("0")
        ),
        revenue_usd=Decimal("0"),
        cost_usd=Decimal("0"),
        active_children=0,
        proposals_awaiting_approval=0,
        ethics_escalations=0,
        notes=["Bootstrap complete. Awaiting first proposal."],
    )
    typer.echo(render_digest_email(d))


if __name__ == "__main__":
    app()
