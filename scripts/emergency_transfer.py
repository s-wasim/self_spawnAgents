"""EMERGENCY_TRANSFER CLI (§15.1, §16.4).

Operator-only. Computes the HMAC signature for an EMERGENCY_TRANSFER email.
The resulting signature is pasted into the email body the operator sends to
the bot inbox — the Mother verifies it before debiting Reserve.
"""
from __future__ import annotations

import hashlib
import hmac
from datetime import date
from decimal import Decimal

import typer

app = typer.Typer(help="Sign an EMERGENCY_TRANSFER message.")


@app.command()
def sign(
    amount_usd: str = typer.Argument(..., help="e.g. 100.00"),
    date_iso: str = typer.Option(None, help="YYYY-MM-DD; defaults to today UTC"),
    secret_env: str = typer.Option("OPERATOR_HMAC_SECRET"),
) -> None:
    import os

    secret = os.environ.get(secret_env)
    if not secret:
        raise typer.BadParameter(f"{secret_env} not set")
    d = date_iso or date.today().isoformat()
    Decimal(amount_usd)  # shape check
    msg = f"{amount_usd}|{d}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    typer.echo(sig)


@app.command()
def verify(
    amount_usd: str = typer.Argument(...),
    date_iso: str = typer.Argument(...),
    signature: str = typer.Argument(...),
    secret_env: str = typer.Option("OPERATOR_HMAC_SECRET"),
) -> None:
    import os

    from aae.cashflow.ledger import verify_emergency_hmac

    secret = os.environ.get(secret_env, "")
    ok = verify_emergency_hmac(secret, Decimal(amount_usd), date_iso, signature)
    typer.echo("OK" if ok else "BAD")
    raise typer.Exit(code=0 if ok else 1)


if __name__ == "__main__":
    app()
